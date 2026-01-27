"""
IFC Plate export for Schmekla.

Creates IfcPlate entities from Schmekla Plate elements.
"""

from typing import Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.plate import Plate
    from src.ifc.exporter import IFCExporter


def create_ifc_plate(plate: "Plate", exporter: "IFCExporter") -> Any:
    """
    Create IfcPlate from Schmekla Plate.

    Args:
        plate: Schmekla Plate element
        exporter: IFC exporter instance

    Returns:
        IfcPlate entity
    """
    import ifcopenshell.api

    ifc = exporter.ifc
    logger.debug(f"Creating IFC plate for {plate.id}")

    # Create plate entity
    ifc_plate = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcPlate",
        name=plate.name or f"Plate_{str(plate.id)[:8]}"
    )

    # Create polygon outline for profile
    ifc_points = [
        ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=[p.x, p.y]
        )
        for p in plate.points
    ]
    # Close the polygon
    ifc_points.append(ifc_points[0])

    polyline = ifc.create_entity(
        "IfcPolyline",
        Points=ifc_points
    )

    # Create arbitrary profile
    profile_def = ifc.create_entity(
        "IfcArbitraryClosedProfileDef",
        ProfileType="AREA",
        OuterCurve=polyline
    )

    # Create axis placement at plate base
    base_z = plate.points[0].z if plate.points else 0
    placement_point = plate.centroid
    placement_point = type(placement_point)(placement_point.x, placement_point.y, base_z)

    axis_placement = exporter.create_axis_placement(placement_point)

    # Create extruded solid
    extrusion_dir = ifc.create_entity(
        "IfcDirection",
        DirectionRatios=[0.0, 0.0, 1.0]
    )

    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile_def,
        Position=axis_placement,
        ExtrudedDirection=extrusion_dir,
        Depth=plate.thickness
    )

    # Create shape representation
    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid]
    )

    # Create product definition shape
    product_shape = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )

    ifc_plate.Representation = product_shape
    ifc_plate.ObjectPlacement = exporter.create_local_placement(placement_point)

    # Add properties
    _add_plate_properties(ifc_plate, plate, exporter)

    logger.debug(f"Created IfcPlate: {ifc_plate.Name}")
    return ifc_plate


def _add_plate_properties(ifc_plate: Any, plate: "Plate", exporter: "IFCExporter"):
    """Add plate-specific properties."""
    import ifcopenshell.api

    ifc = exporter.ifc

    pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_plate,
        name="Pset_PlateCommon"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=pset,
        properties={
            "Reference": plate.name or str(plate.id),
        }
    )

    schmekla_pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_plate,
        name="Schmekla_PlateProperties"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=schmekla_pset,
        properties={
            "Thickness": plate.thickness,
            "Area": plate.area,
            "VertexCount": len(plate.points),
        }
    )
