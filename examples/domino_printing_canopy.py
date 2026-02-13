"""
Domino Printing Loading Bay Canopy Builder

Project: 704216 - Domino Printing
Location: L30 4AJ
Style: Oxford XL
Structure Size: 13m x 10m
Roof Shape: Barrel (curved)
Cladding Type: Polycarbonate

This script builds the complete structural model from the client drawings.
"""

import sys
import math
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from loguru import logger

from src.core.model import StructuralModel
from src.core.column import Column
from src.core.beam import Beam
from src.core.footing import Footing
from src.core.profile import Profile, ProfileType, ProfileCatalog
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D


# =============================================================================
# PROJECT CONSTANTS (from drawings)
# =============================================================================

# Project info
PROJECT_NAME = "Domino Printing - Loading Bay Canopy"
PROJECT_NUMBER = "704216"

# Overall dimensions (mm)
CANOPY_LENGTH = 13000  # X-direction (grids 1-5)
CANOPY_WIDTH = 10000   # Y-direction (grids B-C)

# Grid positions (mm) - measured from grid 1/B origin
GRID_X = {
    '1': 0,
    '2': 2500,
    '3': 5000,
    '4': 7500,
    '5': 10000,
}

GRID_Y = {
    'B': 0,
    'C': 10000,
}

# Column positions - columns are on grids B and C at all numbered grids
# From drawing: all columns are at grid intersections B1-B5 and C1-C5 (10 total)

# Elevations (mm)
GROUND_LEVEL = 0
EAVES_HEIGHT = 4865  # Top of columns / bottom of hoops
TOP_OF_CANOPY = 6980  # Ridge height
COLUMN_HEIGHT = 5716  # Actual column length (includes base plate)

# Barrel roof parameters
ROOF_RISE = 2115  # From eaves to ridge
ROOF_SPAN = 10000  # Across Y-direction (B to C)
HOOP_SEGMENTS = 16  # Number of segments to approximate each curved hoop

# Foundation pad sizes (mm)
PAD_CORNER = 1200  # Corner pads (grids 1 and 5)
PAD_INTERMEDIATE = 1400  # Intermediate pads (grids 2, 3, 4)
PAD_DEPTH = 300  # Foundation depth

# Purlin spacing along hoops (mm)
PURLIN_SPACING = 700  # Approximate spacing between purlins


def create_custom_profiles():
    """Create the SHS profiles used in this project."""

    catalog = ProfileCatalog.get_instance()

    # SHS 150x150x5.0 for columns (should already exist, but ensure it)
    shs_150 = Profile(
        name="SHS 150x150x5",
        profile_type=ProfileType.SQUARE_HOLLOW,
        h=150,
        b=150,
        t=5,
        weight=22.0,
        area=2870,  # mm^2
    )
    catalog._profiles["SHS 150x150x5"] = shs_150

    # SHS 60x60x4.0 for hoops and edge purlins
    shs_60x4 = Profile(
        name="SHS 60x60x4",
        profile_type=ProfileType.SQUARE_HOLLOW,
        h=60,
        b=60,
        t=4,
        weight=6.71,
        area=855,
    )
    catalog._profiles["SHS 60x60x4"] = shs_60x4

    # SHS 60x60x3.0 for standard purlins
    shs_60x3 = Profile(
        name="SHS 60x60x3",
        profile_type=ProfileType.SQUARE_HOLLOW,
        h=60,
        b=60,
        t=3,
        weight=5.15,
        area=656,
    )
    catalog._profiles["SHS 60x60x3"] = shs_60x3

    # SHS 20x20x2.5 for hoop bracing (diagonal members)
    shs_20 = Profile(
        name="SHS 20x20x2.5",
        profile_type=ProfileType.SQUARE_HOLLOW,
        h=20,
        b=20,
        t=2.5,
        weight=1.12,
        area=143,
    )
    catalog._profiles["SHS 20x20x2.5"] = shs_20

    logger.info("Custom profiles created for Domino Printing project")
    return {
        'column': shs_150,
        'hoop': shs_60x4,
        'purlin': shs_60x3,
        'purlin_edge': shs_60x4,
        'bracing': shs_20,
    }


def calculate_barrel_curve_points(y_start, y_end, z_eaves, z_ridge, num_segments):
    """
    Calculate points along the barrel curve from B to C grid.

    The barrel roof is an arc spanning from grid B to grid C.
    The arc starts at eaves height at both edges and rises to ridge height at center.

    Returns list of (y, z) tuples along the curve.
    """
    points = []

    # Calculate arc parameters
    # The arc is part of a circle that passes through:
    # - (y_start, z_eaves) - left eaves
    # - (y_end, z_eaves) - right eaves
    # - (y_center, z_ridge) - center ridge

    span = y_end - y_start
    y_center = (y_start + y_end) / 2
    rise = z_ridge - z_eaves

    # For a circular arc: radius = (span/2)^2 / (2*rise) + rise/2
    # But we'll use a simpler parabolic approximation which is common for barrel roofs

    for i in range(num_segments + 1):
        t = i / num_segments
        y = y_start + t * span

        # Parabolic curve: z = z_eaves + 4*rise * t * (1-t)
        # This gives max height at t=0.5 (center)
        z = z_eaves + 4 * rise * t * (1 - t)

        points.append((y, z))

    return points


def create_columns(model: StructuralModel, profiles: dict, material: Material):
    """Create all 10 columns."""

    columns = []
    col_profile = profiles['column']

    # Column positions based on drawing
    # Grids 1 and 5: COL1 and COL5 (corner columns)
    # Grids 2, 3, 4: COL6 (intermediate columns)

    for grid_num_name, x_pos in GRID_X.items():
        for grid_letter, y_pos in GRID_Y.items():
            base_point = Point3D(x_pos, y_pos, GROUND_LEVEL)

            # Determine column mark based on position
            if grid_num_name in ['1', '5']:
                if grid_letter == 'B':
                    mark = f"COL{'1' if grid_num_name == '1' else '5'}"
                else:
                    mark = f"COL{'1' if grid_num_name == '1' else '5'}"
            else:
                mark = "COL6"

            name = f"{mark}-{grid_letter}{grid_num_name}"

            col = Column(
                base_point=base_point,
                height=COLUMN_HEIGHT,
                profile=col_profile,
                material=material,
                rotation=0,
                name=name
            )

            model.add_element(col)
            columns.append(col)
            logger.info(f"Created column {name} at ({x_pos}, {y_pos})")

    return columns


def create_hoops(model: StructuralModel, profiles: dict, material: Material):
    """
    Create the 10 barrel hoops (one at each grid line 1-5 on both sides).

    Actually, looking at the drawing more carefully:
    - There are 10 hoops total
    - 5 hoops span from B to C at each X grid position (1, 2, 3, 4, 5)
    - Wait, that's only 5 hoops. Let me re-read...

    From the hoops drawing:
    - HOOP1: 1 piece at grid 1 (end hoop)
    - HOOP2: 3 pieces at grids 2, 3, 4 (intermediate hoops)
    - HOOP3: 1 piece (special hoop)
    - HOOP5: 3 pieces
    - HOOP6: 1 piece at grid 5 (end hoop)
    - HOOP7: 1 piece

    So there are 10 main hoops spanning B-C at positions 1-5 (both sides = 10)

    Actually re-reading: the hoops span from B to C (10m width).
    There's one hoop at each grid line: 1, 2, 3, 4, 5 = 5 hoops total.
    Each hoop is approximated with segmented beams.
    """

    hoops = []
    hoop_profile = profiles['hoop']

    for grid_name, x_pos in GRID_X.items():
        # Calculate the barrel curve points for this hoop
        curve_points = calculate_barrel_curve_points(
            y_start=GRID_Y['B'],
            y_end=GRID_Y['C'],
            z_eaves=EAVES_HEIGHT,
            z_ridge=TOP_OF_CANOPY,
            num_segments=HOOP_SEGMENTS
        )

        # Determine hoop mark
        if grid_name == '1':
            mark = "HOOP1"
        elif grid_name == '5':
            mark = "HOOP6"
        else:
            mark = "HOOP2"

        # Create beam segments for the hoop
        for i in range(len(curve_points) - 1):
            y1, z1 = curve_points[i]
            y2, z2 = curve_points[i + 1]

            start = Point3D(x_pos, y1, z1)
            end = Point3D(x_pos, y2, z2)

            name = f"{mark}-{grid_name}-seg{i+1}"

            beam = Beam(
                start_point=start,
                end_point=end,
                profile=hoop_profile,
                material=material,
                rotation=0,
                name=name
            )

            model.add_element(beam)
            hoops.append(beam)

        logger.info(f"Created hoop at grid {grid_name} with {HOOP_SEGMENTS} segments")

    return hoops


def create_purlins(model: StructuralModel, profiles: dict, material: Material):
    """
    Create purlins connecting the hoops.

    Purlins run in the X-direction (from grid 1 to 5) at regular intervals along the hoops.
    From the purlin drawing:
    - PURL6: SHS 60x60x3.0 - 72 pieces, 2438mm long (standard purlins)
    - PURL10: SHS 60x60x4.0 - 16 pieces, 2350mm long (edge purlins)

    Purlins connect adjacent hoops at matching positions along the curve.
    """

    purlins = []
    purlin_profile = profiles['purlin']
    edge_profile = profiles['purlin_edge']

    # Calculate purlin positions along the curve
    # We need to match the hoop segment points
    curve_points = calculate_barrel_curve_points(
        y_start=GRID_Y['B'],
        y_end=GRID_Y['C'],
        z_eaves=EAVES_HEIGHT,
        z_ridge=TOP_OF_CANOPY,
        num_segments=HOOP_SEGMENTS
    )

    grid_names = list(GRID_X.keys())

    # For each point along the curve (purlin line)
    for pt_idx, (y_pos, z_pos) in enumerate(curve_points):
        # Determine if this is an edge purlin (first or last position)
        is_edge = (pt_idx == 0 or pt_idx == len(curve_points) - 1)
        profile = edge_profile if is_edge else purlin_profile

        # Create purlins between adjacent grids
        for i in range(len(grid_names) - 1):
            grid1 = grid_names[i]
            grid2 = grid_names[i + 1]

            x1 = GRID_X[grid1]
            x2 = GRID_X[grid2]

            start = Point3D(x1, y_pos, z_pos)
            end = Point3D(x2, y_pos, z_pos)

            mark = "PURL10" if is_edge else "PURL6"
            name = f"{mark}-{grid1}{grid2}-p{pt_idx+1}"

            beam = Beam(
                start_point=start,
                end_point=end,
                profile=profile,
                material=material,
                rotation=0,
                name=name
            )

            model.add_element(beam)
            purlins.append(beam)

    logger.info(f"Created {len(purlins)} purlins")
    return purlins


def create_footings(model: StructuralModel, material_concrete: Material):
    """Create foundation pads at each column location."""

    footings = []

    for grid_num_name, x_pos in GRID_X.items():
        for grid_letter, y_pos in GRID_Y.items():
            # Determine pad size based on position
            if grid_num_name in ['1', '5']:
                pad_size = PAD_CORNER
            else:
                pad_size = PAD_INTERMEDIATE

            name = f"PAD-{grid_letter}{grid_num_name}"

            center = Point3D(x_pos, y_pos, GROUND_LEVEL)

            footing = Footing(
                center_point=center,
                width=pad_size,
                length=pad_size,
                depth=PAD_DEPTH,
                material=material_concrete,
                name=name
            )

            model.add_element(footing)
            footings.append(footing)
            logger.info(f"Created footing {name} ({pad_size}x{pad_size})")

    return footings


def create_structural_grids(model: StructuralModel):
    """Add structural grid lines to the model for visualization."""

    # Store grids in model for viewport to render
    model._grids = {
        'x_grids': [
            {'name': name, 'position': pos}
            for name, pos in GRID_X.items()
        ],
        'y_grids': [
            {'name': name, 'position': pos}
            for name, pos in GRID_Y.items()
        ],
    }

    logger.info(f"Added {len(GRID_X)} X-grids and {len(GRID_Y)} Y-grids")


def build_domino_printing_canopy():
    """
    Build the complete Domino Printing canopy model.

    Returns:
        StructuralModel: The completed model
    """

    logger.info("=" * 60)
    logger.info(f"Building {PROJECT_NAME}")
    logger.info(f"Job Number: {PROJECT_NUMBER}")
    logger.info("=" * 60)

    # Create model
    model = StructuralModel()
    model.name = PROJECT_NAME
    model.description = f"Job {PROJECT_NUMBER} - Oxford XL Loading Bay Canopy 13m x 10m"
    model.author = "Clovis Canopies / GMC"

    # Create custom profiles
    profiles = create_custom_profiles()

    # Create materials
    steel = Material.default_steel()
    steel.name = "S355"

    concrete = Material.default_concrete()
    concrete.name = "C30/37"

    # Build structure
    logger.info("\n--- Creating Structural Elements ---\n")

    # 1. Footings (foundations first)
    footings = create_footings(model, concrete)

    # 2. Columns
    columns = create_columns(model, profiles, steel)

    # 3. Hoops (barrel roof frames)
    hoops = create_hoops(model, profiles, steel)

    # 4. Purlins
    purlins = create_purlins(model, profiles, steel)

    # 5. Structural grids
    create_structural_grids(model)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MODEL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Footings: {len(footings)}")
    logger.info(f"Columns: {len(columns)}")
    logger.info(f"Hoop segments: {len(hoops)}")
    logger.info(f"Purlins: {len(purlins)}")
    logger.info(f"Total elements: {model.element_count}")
    logger.info("=" * 60)

    return model


def main():
    """Main entry point - build model and optionally launch viewer."""

    from src.utils.logger import setup_logging
    setup_logging()

    # Build the model
    model = build_domino_printing_canopy()

    # Save the model
    output_path = Path(__file__).parent / "domino_printing_704216.json"
    if model.save(output_path):
        logger.info(f"Model saved to {output_path}")

    return model


if __name__ == "__main__":
    main()
