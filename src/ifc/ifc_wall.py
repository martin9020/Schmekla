"""
IFC Wall export for Schmekla.

Creates IfcWall entities from Schmekla Wall elements.
"""

from typing import Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.wall import Wall
    from src.ifc.exporter import IFCExporter


def create_ifc_wall(wall: "Wall", exporter: "IFCExporter") -> Any:
    """
    Create IfcWall from Schmekla Wall.

    Args:
        wall: Schmekla Wall element
        exporter: IFC exporter instance

    Returns:
        IfcWall entity
    """
    import ifcopenshell.api

    ifc = exporter.ifc
    logger.debug(f"Creating IFC wall for {wall.id}")

    # Determine wall predefined type
    wall_type_map = {
        "standard": "STANDARD",
        "shear": "SHEAR",
        "retaining": "RETAINING",
        "partition": "PARTITIONING",
    }
    predefined_type = wall_type_map.get(wall.wall_type, "STANDARD")

    # Create wall entity - use IfcWallStandardCase for simple walls
    ifc_wall = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcWall",
        name=wall.name or f"Wall_{str(wall.id)[:8]}",
        predefined_type=predefined_type
    )

    # Create wall geometry
    # Wall is defined by extruding a rectangle along the baseline

    # Create rectangular profile (thickness x height when looking along wall)
    profile_def = ifc.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=wall.thickness,
        YDim=wall.height
    )

    # Axis placement at wall start
    # Wall axis runs along X, profile is in YZ plane
    from src.geometry.point import Point3D
    from src.geometry.vector import Vector3D

    start = wall.start_point
    direction = wall.direction
    normal = wall.normal

    # Placement at start point, mid-height
    placement_point = Point3D(
        start.x,
        start.y,
        start.z + wall.base_offset + wall.height / 2
    )

    axis_placement = exporter.create_axis_placement(
        placement_point,
        direction=direction,
        ref_direction=normal
    )

    # Extrude along wall direction
    extrusion_dir = ifc.create_entity(
        "IfcDirection",
        DirectionRatios=[direction.x, direction.y, direction.z]
    )

    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile_def,
        Position=axis_placement,
        ExtrudedDirection=extrusion_dir,
        Depth=wall.length
    )

    # Shape representation
    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid]
    )

    product_shape = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )

    ifc_wall.Representation = product_shape
    ifc_wall.ObjectPlacement = exporter.create_local_placement(placement_point)

    # Add properties
    _add_wall_properties(ifc_wall, wall, exporter)

    # Add openings
    for i, opening in enumerate(wall.openings):
        _add_wall_opening(ifc_wall, wall, opening, i, exporter)

    logger.debug(f"Created IfcWall: {ifc_wall.Name}")
    return ifc_wall


def _add_wall_properties(ifc_wall: Any, wall: "Wall", exporter: "IFCExporter"):
    """Add wall-specific properties."""
    import ifcopenshell.api

    ifc = exporter.ifc

    pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_wall,
        name="Pset_WallCommon"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=pset,
        properties={
            "Reference": wall.name or str(wall.id),
            "LoadBearing": wall.wall_type in ("standard", "shear"),
            "IsExternal": False,
        }
    )

    schmekla_pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_wall,
        name="Schmekla_WallProperties"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=schmekla_pset,
        properties={
            "Length": wall.length,
            "Height": wall.height,
            "Thickness": wall.thickness,
            "WallType": wall.wall_type,
        }
    )


def _add_wall_opening(
    ifc_wall: Any,
    wall: "Wall",
    opening: dict,
    index: int,
    exporter: "IFCExporter"
):
    """Add opening (door/window) to wall."""
    import ifcopenshell.api

    ifc = exporter.ifc

    opening_type = opening.get("type", "rectangular")
    width = opening.get("width", 1000)
    height = opening.get("height", 2100)
    sill_height = opening.get("sill_height", 0)
    position = opening.get("position", 0.5)

    # Create opening element
    opening_name = f"{opening_type.capitalize()}_{index + 1}"

    ifc_opening = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcOpeningElement",
        name=opening_name
    )

    # Calculate opening position
    from src.geometry.point import Point3D

    distance_along = wall.length * position
    dir_vec = wall.direction

    opening_center = Point3D(
        wall.start_point.x + dir_vec.x * distance_along,
        wall.start_point.y + dir_vec.y * distance_along,
        wall.start_point.z + wall.base_offset + sill_height + height / 2
    )

    # Create rectangular profile for opening
    profile = ifc.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=width,
        YDim=height
    )

    axis_placement = exporter.create_axis_placement(
        opening_center,
        direction=wall.normal
    )

    # Extrude through wall
    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=axis_placement,
        ExtrudedDirection=ifc.create_entity(
            "IfcDirection",
            DirectionRatios=[wall.normal.x, wall.normal.y, wall.normal.z]
        ),
        Depth=wall.thickness + 10
    )

    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid]
    )

    ifc_opening.Representation = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )
    ifc_opening.ObjectPlacement = exporter.create_local_placement(opening_center)

    # Create void relationship
    ifcopenshell.api.run(
        "void.add_opening", ifc,
        opening=ifc_opening,
        element=ifc_wall
    )
