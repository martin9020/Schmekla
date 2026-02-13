"""
Simple portal frame example for Schmekla.

Creates a basic portal frame and exports to IFC.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.model import StructuralModel
from src.core.beam import Beam
from src.core.profile import Profile
from src.core.material import Material
from src.geometry.point import Point3D


def create_portal_frame(
    width: float = 12000,
    height: float = 6000,
    beam_profile: str = "UB 406x178x54",
    column_profile: str = "UC 254x254x73"
):
    """
    Create a simple portal frame.

    Args:
        width: Frame width in mm
        height: Frame height in mm
        beam_profile: Profile name for beam/rafter
        column_profile: Profile name for columns

    Returns:
        StructuralModel with portal frame
    """
    model = StructuralModel()
    model.name = "Simple Portal Frame"

    # Get profiles
    beam_prof = Profile.from_name(beam_profile)
    col_prof = Profile.from_name(column_profile)
    steel = Material.default_steel()

    # Create columns
    col1 = Beam(
        start_point=Point3D(0, 0, 0),
        end_point=Point3D(0, 0, height),
        profile=col_prof,
        material=steel,
        name="Col-1"
    )

    col2 = Beam(
        start_point=Point3D(width, 0, 0),
        end_point=Point3D(width, 0, height),
        profile=col_prof,
        material=steel,
        name="Col-2"
    )

    # Create rafter
    rafter = Beam(
        start_point=Point3D(0, 0, height),
        end_point=Point3D(width, 0, height),
        profile=beam_prof,
        material=steel,
        name="Rafter"
    )

    # Add to model
    model.add_element(col1)
    model.add_element(col2)
    model.add_element(rafter)

    return model


def main():
    """Create portal frame and export to IFC."""
    print("Creating portal frame...")

    model = create_portal_frame(
        width=12000,  # 12m span
        height=6000,  # 6m eaves height
    )

    print(f"Created model with {model.element_count} elements")

    # Export to IFC
    output_path = Path(__file__).parent / "portal_frame.ifc"

    try:
        from src.ifc.exporter import IFCExporter

        exporter = IFCExporter(model)
        exporter.export(str(output_path))
        print(f"Exported to: {output_path}")
    except ImportError as e:
        print(f"Cannot export IFC (missing dependency): {e}")
        print("Install with: pip install ifcopenshell")


if __name__ == "__main__":
    main()
