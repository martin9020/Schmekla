"""
Step 2: Extract ground from point cloud
Uses height-based filtering + RANSAC plane detection
"""
import numpy as np
import open3d as o3d
import os

# File paths
INPUT_PLY = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\input\Fordley_Area_1.ply"
OUTPUT_DIR = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\output"

def extract_ground(pcd, ground_height_threshold=0.5):
    """
    Extract ground points using RANSAC plane fitting

    Strategy:
    1. Find the dominant horizontal plane (ground)
    2. Extract points near that plane
    3. Separate remaining points (non-ground)
    """
    print(f"\n{'='*60}")
    print("GROUND EXTRACTION")
    print(f"{'='*60}\n")

    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) if pcd.has_colors() else None

    print(f"Input points: {len(points):,}")
    print(f"Z range: {points[:,2].min():.2f} to {points[:,2].max():.2f}")

    # Method 1: RANSAC to find ground plane
    print("\nFinding ground plane with RANSAC...")

    # First, take only lower portion of points to find ground faster
    z_threshold = np.percentile(points[:,2], 30)  # Lower 30% of points
    low_points_mask = points[:,2] < z_threshold
    low_points = points[low_points_mask]

    # Create temp point cloud for RANSAC
    temp_pcd = o3d.geometry.PointCloud()
    temp_pcd.points = o3d.utility.Vector3dVector(low_points)

    # RANSAC plane fitting
    plane_model, inliers = temp_pcd.segment_plane(
        distance_threshold=0.05,  # 5cm tolerance
        ransac_n=3,
        num_iterations=1000
    )

    [a, b, c, d] = plane_model
    print(f"Ground plane equation: {a:.4f}x + {b:.4f}y + {c:.4f}z + {d:.4f} = 0")

    # Check if plane is horizontal (c should be close to 1 or -1)
    if abs(c) > 0.9:
        print("Ground plane is horizontal (good)")
    else:
        print(f"Warning: Ground plane may not be horizontal (c={c:.3f})")

    # Calculate distance of ALL points to ground plane
    distances = np.abs(a * points[:,0] + b * points[:,1] + c * points[:,2] + d) / np.sqrt(a*a + b*b + c*c)

    # Ground points: close to plane AND in lower portion
    ground_mask = (distances < ground_height_threshold) & (points[:,2] < z_threshold + 0.5)
    non_ground_mask = ~ground_mask

    ground_points = points[ground_mask]
    non_ground_points = points[non_ground_mask]

    print(f"\n--- Results ---")
    print(f"Ground points: {len(ground_points):,} ({100*len(ground_points)/len(points):.1f}%)")
    print(f"Non-ground points: {len(non_ground_points):,} ({100*len(non_ground_points)/len(points):.1f}%)")

    # Create output point clouds
    ground_pcd = o3d.geometry.PointCloud()
    ground_pcd.points = o3d.utility.Vector3dVector(ground_points)

    non_ground_pcd = o3d.geometry.PointCloud()
    non_ground_pcd.points = o3d.utility.Vector3dVector(non_ground_points)

    # Add colors if available
    if colors is not None:
        ground_pcd.colors = o3d.utility.Vector3dVector(colors[ground_mask])
        non_ground_pcd.colors = o3d.utility.Vector3dVector(colors[non_ground_mask])

    return ground_pcd, non_ground_pcd, plane_model

def main():
    print(f"Loading: {INPUT_PLY}")
    pcd = o3d.io.read_point_cloud(INPUT_PLY)
    print(f"Loaded {len(pcd.points):,} points")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extract ground
    ground_pcd, non_ground_pcd, plane_model = extract_ground(pcd)

    # Save results
    ground_file = os.path.join(OUTPUT_DIR, "01_ground.ply")
    non_ground_file = os.path.join(OUTPUT_DIR, "01_non_ground.ply")

    o3d.io.write_point_cloud(ground_file, ground_pcd)
    o3d.io.write_point_cloud(non_ground_file, non_ground_pcd)

    print(f"\n{'='*60}")
    print("SAVED FILES")
    print(f"{'='*60}")
    print(f"Ground: {ground_file}")
    print(f"Non-ground: {non_ground_file}")

    # Save plane model for later use
    plane_file = os.path.join(OUTPUT_DIR, "ground_plane.txt")
    np.savetxt(plane_file, plane_model)
    print(f"Plane model: {plane_file}")

if __name__ == "__main__":
    main()
