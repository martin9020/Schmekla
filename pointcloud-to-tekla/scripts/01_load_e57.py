"""
Step 1: Load E57 file and inspect contents
"""
import numpy as np

try:
    import pye57
    print("pye57 loaded successfully")
except ImportError as e:
    print(f"pye57 import error: {e}")

try:
    import open3d as o3d
    print(f"Open3D version: {o3d.__version__}")
except ImportError as e:
    print(f"Open3D import error: {e}")

# File path
E57_FILE = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\input\Fordley_Area_1.e57"

def load_e57_full():
    """Load E57 file with all available data"""
    print(f"\n{'='*60}")
    print(f"Loading: {E57_FILE}")
    print(f"{'='*60}\n")

    try:
        e57_file = pye57.E57(E57_FILE)

        # Get scan count
        scan_count = e57_file.scan_count
        print(f"Number of scans: {scan_count}")

        # Get header info
        header = e57_file.get_header(0)
        print(f"Point count: {header.point_count:,}")

        # Get available fields
        available_fields = header.point_fields
        print(f"Available fields: {available_fields}")

        # Load only available fields
        print(f"\nLoading point data...")

        # Read with specific fields that we know exist
        data = e57_file.read_scan_raw(0)

        print(f"Raw data keys: {list(data.keys())}")

        # Get XYZ
        x = data['cartesianX']
        y = data['cartesianY']
        z = data['cartesianZ']

        print(f"\n--- Point Cloud Stats ---")
        print(f"Total points: {len(x):,}")
        print(f"X range: {x.min():.2f} to {x.max():.2f} ({x.max()-x.min():.2f}m)")
        print(f"Y range: {y.min():.2f} to {y.max():.2f} ({y.max()-y.min():.2f}m)")
        print(f"Z range: {z.min():.2f} to {z.max():.2f} ({z.max()-z.min():.2f}m)")

        # Check colors
        has_color = 'colorRed' in data
        if has_color:
            r = data['colorRed']
            g = data['colorGreen']
            b = data['colorBlue']
            print(f"\nColor: YES")
            print(f"  R range: {r.min()} to {r.max()}")
            print(f"  G range: {g.min()} to {g.max()}")
            print(f"  B range: {b.min()} to {b.max()}")
        else:
            print(f"\nColor: NO")

        # Check intensity
        has_intensity = 'intensity' in data
        if has_intensity:
            intensity = data['intensity']
            print(f"Intensity: YES (range: {intensity.min():.2f} to {intensity.max():.2f})")
        else:
            print(f"Intensity: NO")

        # Create Open3D point cloud
        print(f"\n--- Creating Open3D Point Cloud ---")
        points = np.column_stack([x, y, z])
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        if has_color:
            # Normalize colors to 0-1 range
            colors = np.column_stack([r, g, b])
            if colors.max() > 1:
                colors = colors / 255.0
            pcd.colors = o3d.utility.Vector3dVector(colors)
            print("Colors added to point cloud")

        print(f"Open3D point cloud created: {len(pcd.points):,} points")

        # Save as PLY for easier future loading
        output_ply = r"C:\Users\Daradudai\Everything-Claude\pointcloud-to-tekla\data\input\Fordley_Area_1.ply"
        o3d.io.write_point_cloud(output_ply, pcd)
        print(f"\nSaved as PLY: {output_ply}")

        return pcd, data

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    pcd, data = load_e57_full()
