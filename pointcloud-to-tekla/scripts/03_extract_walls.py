"""
Step 3: Extract walls and fences from non-ground points
Uses iterative RANSAC to find vertical planes
"""
import numpy as np
import open3d as o3d
import os

# File paths
INPUT_PLY = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\output\01_non_ground.ply"
OUTPUT_DIR = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\output"

def is_vertical_plane(plane_model, threshold=0.3):
    """Check if plane is vertical (c coefficient should be near 0)"""
    a, b, c, d = plane_model
    return abs(c) < threshold

def extract_walls_iterative(pcd, max_walls=20, min_points=5000):
    """
    Extract multiple wall planes using iterative RANSAC

    Strategy:
    1. Find largest plane
    2. Check if vertical (wall) or horizontal (skip)
    3. Remove those points, repeat
    """
    print(f"\n{'='*60}")
    print("WALL EXTRACTION (Iterative RANSAC)")
    print(f"{'='*60}\n")

    remaining_pcd = pcd
    walls = []
    all_wall_points = []
    all_wall_colors = []

    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) if pcd.has_colors() else None

    print(f"Input points: {len(points):,}")
    print(f"Looking for up to {max_walls} walls with min {min_points:,} points each\n")

    for i in range(max_walls):
        if len(remaining_pcd.points) < min_points:
            print(f"Stopping: only {len(remaining_pcd.points):,} points remaining")
            break

        # Find largest plane
        try:
            plane_model, inliers = remaining_pcd.segment_plane(
                distance_threshold=0.05,  # 5cm
                ransac_n=3,
                num_iterations=1000
            )
        except Exception as e:
            print(f"RANSAC failed: {e}")
            break

        if len(inliers) < min_points:
            print(f"Stopping: largest plane has only {len(inliers):,} points")
            break

        # Check if vertical
        if is_vertical_plane(plane_model):
            wall_type = "WALL"
            a, b, c, d = plane_model

            # Get wall points
            wall_points = np.asarray(remaining_pcd.points)[inliers]
            wall_colors = np.asarray(remaining_pcd.colors)[inliers] if remaining_pcd.has_colors() else None

            # Calculate wall dimensions
            z_min, z_max = wall_points[:,2].min(), wall_points[:,2].max()
            height = z_max - z_min

            # Classify as WALL or FENCE based on height
            if height < 2.0:
                wall_type = "FENCE"

            print(f"Plane {i+1}: {wall_type} - {len(inliers):,} points, height={height:.2f}m")

            walls.append({
                'plane_model': plane_model,
                'points': wall_points,
                'colors': wall_colors,
                'type': wall_type,
                'height': height,
                'point_count': len(inliers)
            })

            all_wall_points.append(wall_points)
            if wall_colors is not None:
                all_wall_colors.append(wall_colors)

        else:
            a, b, c, d = plane_model
            print(f"Plane {i+1}: HORIZONTAL (skipping) - {len(inliers):,} points, c={c:.3f}")

        # Remove inliers from remaining points
        remaining_pcd = remaining_pcd.select_by_index(inliers, invert=True)

    print(f"\n--- Summary ---")
    print(f"Total walls found: {len(walls)}")

    wall_count = sum(1 for w in walls if w['type'] == 'WALL')
    fence_count = sum(1 for w in walls if w['type'] == 'FENCE')
    print(f"  WALLS: {wall_count}")
    print(f"  FENCES: {fence_count}")

    return walls, remaining_pcd

def main():
    print(f"Loading: {INPUT_PLY}")
    pcd = o3d.io.read_point_cloud(INPUT_PLY)
    print(f"Loaded {len(pcd.points):,} points")

    # Extract walls
    walls, remaining_pcd = extract_walls_iterative(pcd)

    # Separate walls and fences
    wall_points_list = []
    fence_points_list = []
    wall_colors_list = []
    fence_colors_list = []

    for w in walls:
        if w['type'] == 'WALL':
            wall_points_list.append(w['points'])
            if w['colors'] is not None:
                wall_colors_list.append(w['colors'])
        else:
            fence_points_list.append(w['points'])
            if w['colors'] is not None:
                fence_colors_list.append(w['colors'])

    # Create combined point clouds
    if wall_points_list:
        all_wall_points = np.vstack(wall_points_list)
        walls_pcd = o3d.geometry.PointCloud()
        walls_pcd.points = o3d.utility.Vector3dVector(all_wall_points)
        if wall_colors_list:
            walls_pcd.colors = o3d.utility.Vector3dVector(np.vstack(wall_colors_list))
    else:
        walls_pcd = o3d.geometry.PointCloud()

    if fence_points_list:
        all_fence_points = np.vstack(fence_points_list)
        fences_pcd = o3d.geometry.PointCloud()
        fences_pcd.points = o3d.utility.Vector3dVector(all_fence_points)
        if fence_colors_list:
            fences_pcd.colors = o3d.utility.Vector3dVector(np.vstack(fence_colors_list))
    else:
        fences_pcd = o3d.geometry.PointCloud()

    # Save results
    walls_file = os.path.join(OUTPUT_DIR, "02_walls.ply")
    fences_file = os.path.join(OUTPUT_DIR, "02_fences.ply")
    other_file = os.path.join(OUTPUT_DIR, "02_other.ply")

    o3d.io.write_point_cloud(walls_file, walls_pcd)
    o3d.io.write_point_cloud(fences_file, fences_pcd)
    o3d.io.write_point_cloud(other_file, remaining_pcd)

    print(f"\n{'='*60}")
    print("SAVED FILES")
    print(f"{'='*60}")
    print(f"Walls ({len(walls_pcd.points):,} pts): {walls_file}")
    print(f"Fences ({len(fences_pcd.points):,} pts): {fences_file}")
    print(f"Other ({len(remaining_pcd.points):,} pts): {other_file}")

    # Save wall details
    details_file = os.path.join(OUTPUT_DIR, "wall_details.txt")
    with open(details_file, 'w') as f:
        for i, w in enumerate(walls):
            f.write(f"--- {w['type']} {i+1} ---\n")
            f.write(f"Points: {w['point_count']}\n")
            f.write(f"Height: {w['height']:.2f}m\n")
            f.write(f"Plane: {w['plane_model']}\n\n")
    print(f"Details: {details_file}")

if __name__ == "__main__":
    main()
