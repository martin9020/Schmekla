"""
Step 4: Create geometry from segmented point clouds (MEMORY OPTIMIZED)
- Process each file separately
- Heavy downsampling for mesh creation
- Clear memory between operations
"""
import numpy as np
import open3d as o3d
import os
import gc

OUTPUT_DIR = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\output"

def points_to_rectangle(points):
    """Convert wall points to a flat rectangle mesh"""
    if len(points) < 10:
        return None

    centroid = points.mean(axis=0)
    centered = points - centroid
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    idx = eigenvalues.argsort()[::-1]
    eigenvectors = eigenvectors[:, idx]

    wall_u = eigenvectors[:, 0]
    wall_v = eigenvectors[:, 1]

    if wall_v[2] < 0:
        wall_v = -wall_v

    u_coords = np.dot(centered, wall_u)
    v_coords = np.dot(centered, wall_v)

    u_min, u_max = u_coords.min(), u_coords.max()
    v_min, v_max = v_coords.min(), v_coords.max()

    corners = [
        centroid + u_min * wall_u + v_min * wall_v,
        centroid + u_max * wall_u + v_min * wall_v,
        centroid + u_max * wall_u + v_max * wall_v,
        centroid + u_min * wall_u + v_max * wall_v,
    ]

    vertices = np.array(corners)
    triangles = np.array([[0, 1, 2], [0, 2, 3]])

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(vertices)
    mesh.triangles = o3d.utility.Vector3iVector(triangles)
    mesh.compute_vertex_normals()

    width = u_max - u_min
    height = v_max - v_min

    return mesh, width, height

def process_ground(voxel_size=0.5):
    """Process ground separately to save memory"""
    print("\n" + "="*60)
    print("PROCESSING GROUND")
    print("="*60)

    ground_file = os.path.join(OUTPUT_DIR, "01_ground.ply")

    # Load and immediately downsample
    print(f"Loading {ground_file}...")
    pcd = o3d.io.read_point_cloud(ground_file)
    print(f"Original: {len(pcd.points):,} points")

    # Heavy downsample for mesh creation
    pcd_down = pcd.voxel_down_sample(voxel_size)
    print(f"Downsampled: {len(pcd_down.points):,} points")

    # Clear original
    del pcd
    gc.collect()

    # Estimate normals
    print("Estimating normals...")
    pcd_down.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30)
    )
    pcd_down.orient_normals_towards_camera_location(np.array([0, 0, 100]))

    # Create mesh
    print("Creating ground mesh (Poisson)...")
    try:
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd_down, depth=7  # Lower depth = faster, less detail
        )

        # Cleanup low density
        densities = np.asarray(densities)
        threshold = np.quantile(densities, 0.1)
        mesh.remove_vertices_by_mask(densities < threshold)

    except Exception as e:
        print(f"Poisson failed: {e}, using alpha shapes...")
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd_down, 2.0)

    del pcd_down
    gc.collect()

    # Save
    out_ply = os.path.join(OUTPUT_DIR, "03_ground_mesh.ply")
    out_obj = os.path.join(OUTPUT_DIR, "03_ground_mesh.obj")

    o3d.io.write_triangle_mesh(out_ply, mesh)
    o3d.io.write_triangle_mesh(out_obj, mesh)

    print(f"Ground mesh: {len(mesh.triangles):,} triangles")
    print(f"Saved: {out_ply}")
    print(f"Saved: {out_obj}")

    del mesh
    gc.collect()

    return True

def process_walls(voxel_size=0.1):
    """Process walls separately"""
    print("\n" + "="*60)
    print("PROCESSING WALLS")
    print("="*60)

    walls_file = os.path.join(OUTPUT_DIR, "02_walls.ply")

    print(f"Loading {walls_file}...")
    pcd = o3d.io.read_point_cloud(walls_file)
    print(f"Original: {len(pcd.points):,} points")

    # Less aggressive downsample for walls (need to preserve structure)
    pcd_down = pcd.voxel_down_sample(voxel_size)
    print(f"Downsampled: {len(pcd_down.points):,} points")

    del pcd
    gc.collect()

    # Cluster walls - adjusted parameters for downsampled data
    print("Clustering walls (DBSCAN)...")
    labels = np.array(pcd_down.cluster_dbscan(eps=0.3, min_points=50))
    max_label = labels.max()
    print(f"Found {max_label + 1} wall clusters")

    wall_points = np.asarray(pcd_down.points)
    wall_meshes = []
    wall_info = []

    for i in range(max_label + 1):
        cluster_mask = labels == i
        cluster_points = wall_points[cluster_mask]

        if len(cluster_points) > 50:
            result = points_to_rectangle(cluster_points)
            if result:
                mesh, width, height = result
                wall_meshes.append(mesh)
                wall_info.append(f"  Wall {i+1}: {width:.1f}m x {height:.1f}m")

    del pcd_down, wall_points
    gc.collect()

    # Combine meshes
    if wall_meshes:
        combined = wall_meshes[0]
        for m in wall_meshes[1:]:
            combined += m
    else:
        combined = o3d.geometry.TriangleMesh()

    # Print wall info
    for info in wall_info:
        print(info)

    # Save
    out_ply = os.path.join(OUTPUT_DIR, "03_walls_mesh.ply")
    out_obj = os.path.join(OUTPUT_DIR, "03_walls_mesh.obj")

    o3d.io.write_triangle_mesh(out_ply, combined)
    o3d.io.write_triangle_mesh(out_obj, combined)

    print(f"Total: {len(wall_meshes)} walls, {len(combined.triangles):,} triangles")
    print(f"Saved: {out_ply}")
    print(f"Saved: {out_obj}")

    del combined, wall_meshes
    gc.collect()

    return True

def process_fences():
    """Process fences separately"""
    print("\n" + "="*60)
    print("PROCESSING FENCES")
    print("="*60)

    fences_file = os.path.join(OUTPUT_DIR, "02_fences.ply")

    print(f"Loading {fences_file}...")
    pcd = o3d.io.read_point_cloud(fences_file)
    print(f"Points: {len(pcd.points):,}")

    if len(pcd.points) < 100:
        print("Not enough fence points")
        return False

    points = np.asarray(pcd.points)
    result = points_to_rectangle(points)

    del pcd
    gc.collect()

    if result:
        mesh, width, height = result
        print(f"Fence: {width:.1f}m x {height:.1f}m")

        out_ply = os.path.join(OUTPUT_DIR, "03_fence_mesh.ply")
        out_obj = os.path.join(OUTPUT_DIR, "03_fence_mesh.obj")

        o3d.io.write_triangle_mesh(out_ply, mesh)
        o3d.io.write_triangle_mesh(out_obj, mesh)

        print(f"Saved: {out_ply}")
        print(f"Saved: {out_obj}")

    return True

def main():
    print("="*60)
    print("GEOMETRY CREATION (Memory Optimized)")
    print("="*60)

    # Process each separately
    process_ground(voxel_size=0.5)  # 50cm grid
    process_walls(voxel_size=0.1)   # 10cm grid for wall structure
    process_fences()

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)

    # List output files
    print("\nOutput files:")
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("03_"):
            fpath = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(fpath) / 1024
            print(f"  {f}: {size:.1f} KB")

if __name__ == "__main__":
    main()
