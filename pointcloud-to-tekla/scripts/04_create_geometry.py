"""
Step 4: Create clean geometry from segmented point clouds
- Walls → Flat rectangles
- Ground → Mesh following terrain
- Fences → Flat rectangles
"""
import numpy as np
import open3d as o3d
import os

OUTPUT_DIR = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\output"

def points_to_rectangle(points, normal=None):
    """
    Convert wall points to a flat rectangle mesh

    1. Find plane equation from points
    2. Project points onto plane
    3. Find bounding rectangle in 2D
    4. Create mesh
    """
    if len(points) < 10:
        return None

    # Compute centroid
    centroid = points.mean(axis=0)

    # PCA to find principal axes
    centered = points - centroid
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort by eigenvalue (largest first)
    idx = eigenvalues.argsort()[::-1]
    eigenvectors = eigenvectors[:, idx]

    # The normal is the smallest eigenvector (perpendicular to wall)
    wall_normal = eigenvectors[:, 2]
    wall_u = eigenvectors[:, 0]  # Horizontal direction
    wall_v = eigenvectors[:, 1]  # Vertical direction (usually Z)

    # Make sure v points mostly up
    if wall_v[2] < 0:
        wall_v = -wall_v

    # Project points onto 2D (u, v) coordinates
    u_coords = np.dot(centered, wall_u)
    v_coords = np.dot(centered, wall_v)

    # Find bounding rectangle
    u_min, u_max = u_coords.min(), u_coords.max()
    v_min, v_max = v_coords.min(), v_coords.max()

    # Create rectangle corners in 3D
    corners = [
        centroid + u_min * wall_u + v_min * wall_v,
        centroid + u_max * wall_u + v_min * wall_v,
        centroid + u_max * wall_u + v_max * wall_v,
        centroid + u_min * wall_u + v_max * wall_v,
    ]

    # Create mesh
    vertices = np.array(corners)
    triangles = np.array([
        [0, 1, 2],
        [0, 2, 3]
    ])

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(vertices)
    mesh.triangles = o3d.utility.Vector3iVector(triangles)
    mesh.compute_vertex_normals()

    # Calculate dimensions
    width = u_max - u_min
    height = v_max - v_min

    return mesh, width, height

def create_ground_mesh(ground_pcd, voxel_size=0.5):
    """
    Create terrain mesh from ground points

    Uses Poisson reconstruction to create smooth surface
    """
    print("Creating ground mesh...")

    # Downsample for faster processing
    pcd_down = ground_pcd.voxel_down_sample(voxel_size)
    print(f"Downsampled to {len(pcd_down.points):,} points")

    # Estimate normals (pointing up)
    pcd_down.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30)
    )

    # Orient normals upward
    pcd_down.orient_normals_towards_camera_location(
        camera_location=np.array([0, 0, 100])  # Point above scene
    )

    # Poisson reconstruction
    print("Running Poisson reconstruction...")
    try:
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd_down, depth=8
        )

        # Remove low-density vertices (cleanup)
        densities = np.asarray(densities)
        density_threshold = np.quantile(densities, 0.1)
        vertices_to_remove = densities < density_threshold
        mesh.remove_vertices_by_mask(vertices_to_remove)

        print(f"Ground mesh: {len(mesh.vertices):,} vertices, {len(mesh.triangles):,} triangles")
        return mesh

    except Exception as e:
        print(f"Poisson failed: {e}")
        print("Using alpha shapes instead...")

        # Fallback: alpha shapes
        alpha = 2.0
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd_down, alpha)
        return mesh

def main():
    print(f"{'='*60}")
    print("GEOMETRY CREATION")
    print(f"{'='*60}\n")

    # Load segmented point clouds
    walls_pcd = o3d.io.read_point_cloud(os.path.join(OUTPUT_DIR, "02_walls.ply"))
    fences_pcd = o3d.io.read_point_cloud(os.path.join(OUTPUT_DIR, "02_fences.ply"))
    ground_pcd = o3d.io.read_point_cloud(os.path.join(OUTPUT_DIR, "01_ground.ply"))

    print(f"Walls: {len(walls_pcd.points):,} points")
    print(f"Fences: {len(fences_pcd.points):,} points")
    print(f"Ground: {len(ground_pcd.points):,} points")

    # 1. Create ground mesh (with terrain curves)
    print(f"\n--- Ground Mesh ---")
    ground_mesh = create_ground_mesh(ground_pcd, voxel_size=0.3)

    # 2. Create wall rectangles from point clusters
    print(f"\n--- Wall Rectangles ---")

    # Use DBSCAN to cluster wall points
    labels = np.array(walls_pcd.cluster_dbscan(eps=0.5, min_points=1000))
    max_label = labels.max()
    print(f"Found {max_label + 1} wall clusters")

    wall_meshes = []
    wall_points = np.asarray(walls_pcd.points)

    for i in range(max_label + 1):
        cluster_mask = labels == i
        cluster_points = wall_points[cluster_mask]

        if len(cluster_points) > 1000:
            result = points_to_rectangle(cluster_points)
            if result:
                mesh, width, height = result
                wall_meshes.append(mesh)
                print(f"  Wall {i+1}: {width:.2f}m x {height:.2f}m")

    # Combine all wall meshes
    if wall_meshes:
        combined_walls = wall_meshes[0]
        for m in wall_meshes[1:]:
            combined_walls += m
    else:
        combined_walls = o3d.geometry.TriangleMesh()

    print(f"Total wall meshes: {len(wall_meshes)}")

    # 3. Create fence rectangles
    print(f"\n--- Fence Rectangles ---")
    if len(fences_pcd.points) > 100:
        result = points_to_rectangle(np.asarray(fences_pcd.points))
        if result:
            fence_mesh, width, height = result
            print(f"  Fence: {width:.2f}m x {height:.2f}m")
        else:
            fence_mesh = o3d.geometry.TriangleMesh()
    else:
        fence_mesh = o3d.geometry.TriangleMesh()

    # Save meshes
    print(f"\n{'='*60}")
    print("SAVING MESHES")
    print(f"{'='*60}")

    ground_file = os.path.join(OUTPUT_DIR, "03_ground_mesh.ply")
    walls_file = os.path.join(OUTPUT_DIR, "03_walls_mesh.ply")
    fence_file = os.path.join(OUTPUT_DIR, "03_fence_mesh.ply")

    o3d.io.write_triangle_mesh(ground_file, ground_mesh)
    o3d.io.write_triangle_mesh(walls_file, combined_walls)
    o3d.io.write_triangle_mesh(fence_file, fence_mesh)

    print(f"Ground mesh: {ground_file}")
    print(f"Walls mesh: {walls_file}")
    print(f"Fence mesh: {fence_file}")

    # Also save as OBJ (widely supported)
    ground_obj = os.path.join(OUTPUT_DIR, "03_ground_mesh.obj")
    walls_obj = os.path.join(OUTPUT_DIR, "03_walls_mesh.obj")
    fence_obj = os.path.join(OUTPUT_DIR, "03_fence_mesh.obj")

    o3d.io.write_triangle_mesh(ground_obj, ground_mesh)
    o3d.io.write_triangle_mesh(walls_obj, combined_walls)
    o3d.io.write_triangle_mesh(fence_obj, fence_mesh)

    print(f"\nAlso saved as OBJ format")

    # Stats
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Ground mesh: {len(ground_mesh.triangles):,} triangles")
    print(f"Wall meshes: {len(wall_meshes)} walls, {len(combined_walls.triangles):,} triangles")
    print(f"Fence mesh: {len(fence_mesh.triangles):,} triangles")

if __name__ == "__main__":
    main()
