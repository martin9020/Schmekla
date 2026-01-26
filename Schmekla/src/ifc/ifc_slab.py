"""
IFC Slab export for Schmekla.

Creates IfcSlab entities from Schmekla Slab elements.
"""

from typing import Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.slab import Slab
    from src.ifc.exporter import IFCExporter


def create_ifc_slab(slab: "Slab", exporter: "IFCExporter") -> Any:
    """
    Create IfcSlab from Schmekla Slab.

    Args:
        slab: Schmekla Slab element
        exporter: IFC exporter instance

    Returns:
        IfcSlab entity
    """
    import ifcopenshell.api

    ifc = exporter.ifc
    logger.debug(f"Creating IFC slab for {slab.id}")

    # Determine slab predefined type
    slab_type_map = {
        "floor": "FLOOR",
        "roof": "ROOF",
        "landing": "LANDING",
        "mat": "BASESLAB",
    }
    predefined_type = slab_type_map.get(slab.slab_type, "FLOOR")

    # Create slab entity
    ifc_slab = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcSlab",
        name=slab.name or f"Slab_{str(slab.id)[:8]}",
        predefined_type=predefined_type
    )

    # Create polygon outline
    ifc_points = [
        ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=[p.x, p.y]
        )
        for p in slab.points
    ]
    ifc_points.append(ifc_points[0])

    polyline = ifc.create_entity(
        "IfcPolyline",
        Points=ifc_points
    )

    # Create profile
    profile_def = ifc.create_entity(
        "IfcArbitraryClosedProfileDef",
        ProfileType="AREA",
        OuterCurve=polyline
    )

    # Axis placement at slab top, extrude downward
    from src.geometry.point import Point3D
    top_z = slab.elevation
    centroid = slab.centroid
    placement_point = Point3D(centroid.x, centroid.y, top_z)

    axis_placement = exporter.create_axis_placement(placement_point)

    # Extrude downward (negative Z)
    extrusion_dir = ifc.create_entity(
        "IfcDirection",
        DirectionRatios=[0.0, 0.0, -1.0]
    )

    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile_def,
        Position=axis_placement,
        ExtrudedDirection=extrusion_dir,
        Depth=slab.thickness
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

    ifc_slab.Representation = product_shape
    ifc_slab.ObjectPlacement = exporter.create_local_placement(placement_point)

    # Add properties
    _add_slab_properties(ifc_slab, slab, exporter)

    # Add openings as voids
    for i, opening in enumerate(slab.openings):
        _add_slab_opening(ifc_slab, slab, opening, i, exporter)

    logger.debug(f"Created IfcSlab: {ifc_slab.Name}")
    return ifc_slab


def _add_slab_properties(ifc_slab: Any, slab: "Slab", exporter: "IFCExporter"):
    """Add slab-specific properties."""
    import ifcopenshell.api

    ifc = exporter.ifc

    pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_slab,
        name="Pset_SlabCommon"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=pset,
        properties={
            "Reference": slab.name or str(slab.id),
            "LoadBearing": True,
        }
    )

    schmekla_pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_slab,
        name="Schmekla_SlabProperties"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=schmekla_pset,
        properties={
            "Thickness": slab.thickness,
            "Elevation": slab.elevation,
            "Area": slab.area,
            "SlabType": slab.slab_type,
        }
    )


def _add_slab_opening(
    ifc_slab: Any,
    slab: "Slab",
    opening: dict,
    index: int,
    exporter: "IFCExporter"
):
    """Add opening void to slab."""
    import ifcopenshell.api

    ifc = exporter.ifc

    # Create opening element
    opening_name = f"Opening_{index + 1}"

    ifc_opening = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcOpeningElement",
        name=opening_name
    )

    # Create opening geometry based on type
    opening_type = opening.get("type", "rectangular")

    if opening_type == "rectangular":
        points = opening.get("points", [])
        if len(points) >= 2:
            p1, p2 = points[0], points[1]
            width = abs(p2[0] - p1[0])
            length = abs(p2[1] - p1[1])
            center_x = (p1[0] + p2[0]) / 2
            center_y = (p1[1] + p2[1]) / 2

            profile = ifc.create_entity(
                "IfcRectangleProfileDef",
                ProfileType="AREA",
                XDim=width,
                YDim=length
            )

            from src.geometry.point import Point3D
            opening_point = Point3D(center_x, center_y, slab.elevation)
            axis_placement = exporter.create_axis_placement(opening_point)

            solid = ifc.create_entity(
                "IfcExtrudedAreaSolid",
                SweptArea=profile,
                Position=axis_placement,
                ExtrudedDirection=ifc.create_entity(
                    "IfcDirection",
                    DirectionRatios=[0.0, 0.0, -1.0]
                ),
                Depth=slab.thickness + 10  # Extend beyond slab
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
            ifc_opening.ObjectPlacement = exporter.create_local_placement(opening_point)

            # Create void relationship
            ifcopenshell.api.run(
                "void.add_opening", ifc,
                opening=ifc_opening,
                element=ifc_slab
            )
