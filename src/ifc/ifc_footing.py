"""
IFC Footing export for Schmekla.

Creates IfcFooting entities from Schmekla Footing elements.
"""

from typing import Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.footing import Footing
    from src.ifc.exporter import IFCExporter


def create_ifc_footing(footing: "Footing", exporter: "IFCExporter") -> Any:
    """
    Create IfcFooting from Schmekla Footing.

    Args:
        footing: Schmekla Footing element
        exporter: IFC exporter instance

    Returns:
        IfcFooting entity
    """
    import ifcopenshell.api

    ifc = exporter.ifc
    logger.debug(f"Creating IFC footing for {footing.id}")

    # Determine footing predefined type
    footing_type_map = {
        "pad": "PAD_FOOTING",
        "strip": "STRIP_FOOTING",
        "mat": "MAT_FOUNDATION",
        "pile_cap": "PILE_CAP",
    }
    predefined_type = footing_type_map.get(footing.footing_type, "PAD_FOOTING")

    # Create footing entity
    ifc_footing = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcFooting",
        name=footing.name or f"Footing_{str(footing.id)[:8]}",
        predefined_type=predefined_type
    )

    # Create rectangular profile
    profile_def = ifc.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=footing.width,
        YDim=footing.length
    )

    # Axis placement at footing top center
    from src.geometry.point import Point3D
    from src.geometry.vector import Vector3D

    placement_point = footing.center_point

    # Create rotation if needed
    ref_dir = None
    if footing.rotation != 0:
        import math
        angle_rad = math.radians(footing.rotation)
        ref_dir = Vector3D(math.cos(angle_rad), math.sin(angle_rad), 0)

    axis_placement = exporter.create_axis_placement(
        placement_point,
        ref_direction=ref_dir
    )

    # Extrude downward
    extrusion_dir = ifc.create_entity(
        "IfcDirection",
        DirectionRatios=[0.0, 0.0, -1.0]
    )

    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile_def,
        Position=axis_placement,
        ExtrudedDirection=extrusion_dir,
        Depth=footing.depth
    )

    items = [solid]

    # Add pedestal if present
    if footing.pedestal_width > 0 and footing.pedestal_height > 0:
        pedestal_profile = ifc.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=footing.pedestal_width,
            YDim=footing.pedestal_width
        )

        pedestal_placement = exporter.create_axis_placement(
            placement_point,
            ref_direction=ref_dir
        )

        pedestal_dir = ifc.create_entity(
            "IfcDirection",
            DirectionRatios=[0.0, 0.0, 1.0]
        )

        pedestal_solid = ifc.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=pedestal_profile,
            Position=pedestal_placement,
            ExtrudedDirection=pedestal_dir,
            Depth=footing.pedestal_height
        )
        items.append(pedestal_solid)

    # Shape representation
    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=items
    )

    product_shape = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )

    ifc_footing.Representation = product_shape
    ifc_footing.ObjectPlacement = exporter.create_local_placement(placement_point)

    # Add properties
    _add_footing_properties(ifc_footing, footing, exporter)

    logger.debug(f"Created IfcFooting: {ifc_footing.Name}")
    return ifc_footing


def _add_footing_properties(ifc_footing: Any, footing: "Footing", exporter: "IFCExporter"):
    """Add footing-specific properties."""
    import ifcopenshell.api

    ifc = exporter.ifc

    pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_footing,
        name="Pset_FootingCommon"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=pset,
        properties={
            "Reference": footing.name or str(footing.id),
            "LoadBearing": True,
        }
    )

    schmekla_pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_footing,
        name="Schmekla_FootingProperties"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=schmekla_pset,
        properties={
            "Width": footing.width,
            "Length": footing.length,
            "Depth": footing.depth,
            "FootingType": footing.footing_type,
            "TopElevation": footing.top_elevation,
            "BottomElevation": footing.bottom_elevation,
            "PedestalWidth": footing.pedestal_width,
            "PedestalHeight": footing.pedestal_height,
        }
    )
