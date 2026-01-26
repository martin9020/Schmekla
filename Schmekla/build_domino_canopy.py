"""
Build the Domino Printing Loading Bay Canopy model.

Project: 704216 - Domino Printing
Location: L30 4AJ
Style: Oxford XL (Barrel Vault)
Structure Size: 13m x 10m

This script creates the complete structural model and launches the Schmekla UI.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.model import StructuralModel
from src.core.column import Column
from src.core.beam import Beam
from src.core.curved_beam import CurvedBeam, create_barrel_hoop
from src.core.profile import Profile, ProfileType
from src.core.material import Material
from src.geometry.point import Point3D
from loguru import logger


def create_shs_profile(size: float, thickness: float) -> Profile:
    """Create a Square Hollow Section profile."""
    return Profile(
        name=f"SHS {size}x{size}x{thickness}",
        profile_type=ProfileType.SQUARE_HOLLOW,
        h=size,
        b=size,
        t=thickness,
    )


def build_domino_canopy() -> StructuralModel:
    """
    Build the Domino Printing canopy structural model.

    Returns:
        StructuralModel with all canopy elements
    """
    logger.info("Building Domino Printing Canopy Model (Job 704216)")

    model = StructuralModel()
    model.name = "704216 - Domino Printing Loading Bay Canopy"
    model.description = "Oxford XL Barrel Vault Canopy - 13m x 10m"

    # ===== Project Parameters =====
    # All dimensions in millimeters

    # Overall dimensions
    LENGTH = 13000  # X direction (along building)
    WIDTH = 10000   # Y direction (span across)

    # Heights
    GROUND_LEVEL = 0
    EAVES_HEIGHT = 4865      # Top of columns / start of hoops
    APEX_HEIGHT = 6980       # Crown of barrel vault
    RISE = APEX_HEIGHT - EAVES_HEIGHT  # 2115mm

    # Column positions (from drawing)
    # Grid lines 1-5 along the length (X direction)
    # Using equal spacing with end cantilevers
    GRID_X = [1500, 4000, 6500, 9000, 11500]  # Grids 1, 2, 3, 4, 5

    # Grid lines B-C across the width (Y direction)
    # Columns at B and C lines
    GRID_Y_B = 400      # Grid B (inset from edge)
    GRID_Y_C = 9600     # Grid C (inset from edge)

    # ===== Create Profiles =====
    # Column profile: SHS 150x150x5.0
    col_profile = create_shs_profile(150, 5.0)

    # Hoop profile: SHS 60x60x4.0
    hoop_profile = create_shs_profile(60, 4.0)

    # Purlin profile: SHS 60x60x3.0
    purlin_profile = create_shs_profile(60, 3.0)

    # Material
    steel = Material.default_steel()

    # ===== Create Columns =====
    logger.info("Creating columns...")
    column_count = 0

    for i, x in enumerate(GRID_X):
        grid_num = i + 1

        # Column at Grid B
        col_b_start = Point3D(x, GRID_Y_B, GROUND_LEVEL)
        col_b_end = Point3D(x, GRID_Y_B, GROUND_LEVEL + EAVES_HEIGHT)
        col_b = Column(
            start_point=col_b_start,
            end_point=col_b_end,
            profile=col_profile,
            material=steel,
            name=f"COL-{grid_num}B"
        )
        model.add_element(col_b)
        column_count += 1

        # Column at Grid C
        col_c_start = Point3D(x, GRID_Y_C, GROUND_LEVEL)
        col_c_end = Point3D(x, GRID_Y_C, GROUND_LEVEL + EAVES_HEIGHT)
        col_c = Column(
            start_point=col_c_start,
            end_point=col_c_end,
            profile=col_profile,
            material=steel,
            name=f"COL-{grid_num}C"
        )
        model.add_element(col_c)
        column_count += 1

    logger.info(f"Created {column_count} columns")

    # ===== Create Barrel Hoops =====
    logger.info("Creating barrel hoops...")
    hoop_count = 0

    # Main hoops at each grid line (1-5)
    for i, x in enumerate(GRID_X):
        grid_num = i + 1

        hoop = CurvedBeam(
            start_point=Point3D(x, GRID_Y_B, EAVES_HEIGHT),
            end_point=Point3D(x, GRID_Y_C, EAVES_HEIGHT),
            rise=RISE,
            profile=hoop_profile,
            material=steel,
            name=f"HOOP-{grid_num}",
            segments=16  # Smooth curve
        )
        model.add_element(hoop)
        hoop_count += 1

    # Intermediate hoops between main grid lines
    intermediate_x = [2750, 5250, 7750, 10250]  # Midpoints between grids
    for i, x in enumerate(intermediate_x):
        hoop = CurvedBeam(
            start_point=Point3D(x, GRID_Y_B, EAVES_HEIGHT),
            end_point=Point3D(x, GRID_Y_C, EAVES_HEIGHT),
            rise=RISE,
            profile=hoop_profile,
            material=steel,
            name=f"HOOP-INT{i+1}",
            segments=16
        )
        model.add_element(hoop)
        hoop_count += 1

    logger.info(f"Created {hoop_count} barrel hoops")

    # ===== Create Purlins =====
    logger.info("Creating purlins...")
    purlin_count = 0

    # Purlins run along the length (X direction)
    # They connect the hoops at various heights along the barrel curve

    # Get purlin positions along the arc
    # We'll place purlins at regular intervals along the hoop curve
    num_purlin_rows = 8  # Number of purlin rows across the barrel

    # Create a reference hoop to get arc points
    ref_hoop = CurvedBeam(
        start_point=Point3D(0, GRID_Y_B, EAVES_HEIGHT),
        end_point=Point3D(0, GRID_Y_C, EAVES_HEIGHT),
        rise=RISE,
        segments=num_purlin_rows
    )

    # Get Y and Z coordinates at each purlin position
    arc_points = ref_hoop.get_arc_points(num_purlin_rows + 1)

    # All X positions where hoops exist
    all_hoop_x = sorted(GRID_X + intermediate_x)

    # Create purlins between adjacent hoops
    for row_idx in range(len(arc_points)):
        arc_pt = arc_points[row_idx]
        y_pos = arc_pt.y
        z_pos = arc_pt.z

        for hoop_idx in range(len(all_hoop_x) - 1):
            x_start = all_hoop_x[hoop_idx]
            x_end = all_hoop_x[hoop_idx + 1]

            purlin = Beam(
                start_point=Point3D(x_start, y_pos, z_pos),
                end_point=Point3D(x_end, y_pos, z_pos),
                profile=purlin_profile,
                material=steel,
                name=f"PURL-R{row_idx+1}-B{hoop_idx+1}"
            )
            model.add_element(purlin)
            purlin_count += 1

    logger.info(f"Created {purlin_count} purlins")

    # ===== Create Eaves Beams =====
    logger.info("Creating eaves beams...")
    eaves_count = 0

    # Eaves beam along Grid B (front)
    for hoop_idx in range(len(all_hoop_x) - 1):
        x_start = all_hoop_x[hoop_idx]
        x_end = all_hoop_x[hoop_idx + 1]

        eaves_b = Beam(
            start_point=Point3D(x_start, GRID_Y_B, EAVES_HEIGHT),
            end_point=Point3D(x_end, GRID_Y_B, EAVES_HEIGHT),
            profile=hoop_profile,  # Same as hoop for eaves
            material=steel,
            name=f"EAVES-B-{hoop_idx+1}"
        )
        model.add_element(eaves_b)
        eaves_count += 1

    # Eaves beam along Grid C (back)
    for hoop_idx in range(len(all_hoop_x) - 1):
        x_start = all_hoop_x[hoop_idx]
        x_end = all_hoop_x[hoop_idx + 1]

        eaves_c = Beam(
            start_point=Point3D(x_start, GRID_Y_C, EAVES_HEIGHT),
            end_point=Point3D(x_end, GRID_Y_C, EAVES_HEIGHT),
            profile=hoop_profile,
            material=steel,
            name=f"EAVES-C-{hoop_idx+1}"
        )
        model.add_element(eaves_c)
        eaves_count += 1

    logger.info(f"Created {eaves_count} eaves beams")

    # ===== Summary =====
    total = model.element_count
    logger.info(f"\n{'='*50}")
    logger.info(f"MODEL COMPLETE: {model.name}")
    logger.info(f"Total elements: {total}")
    logger.info(f"  - Columns: {column_count}")
    logger.info(f"  - Hoops: {hoop_count}")
    logger.info(f"  - Purlins: {purlin_count}")
    logger.info(f"  - Eaves beams: {eaves_count}")
    logger.info(f"{'='*50}\n")

    return model


def launch_ui(model: StructuralModel):
    """Launch the Schmekla UI with the given model."""
    from PySide6.QtWidgets import QApplication
    from src.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()

    # Replace the window's model with our built model
    window.model = model

    # Connect model signals to UI
    window._connect_signals()

    # Rebuild tree to show elements
    window._rebuild_tree()

    # Update viewport
    if window.viewport:
        window.viewport.model = model
        window.viewport._connect_model_signals()
        window.viewport.update_display()

    # Update status
    window._update_ui()
    window.status_label.setText(f"Loaded: {model.name} ({model.element_count} elements)")

    window.show()

    # Set isometric view
    if window.viewport:
        window.viewport.set_view("iso")
        window.viewport.zoom_to_fit()

    return app.exec()


def main():
    """Main entry point."""
    logger.info("Schmekla - Domino Printing Canopy Builder")
    logger.info("="*50)

    # Build the model
    model = build_domino_canopy()

    # Launch UI
    logger.info("Launching Schmekla UI...")
    return launch_ui(model)


if __name__ == "__main__":
    sys.exit(main())
