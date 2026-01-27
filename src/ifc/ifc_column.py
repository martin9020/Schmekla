"""
IFC Column export for Schmekla.

Creates IfcColumn entities from Schmekla Column elements.
"""

from typing import Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.column import Column
    from src.ifc.exporter import IFCExporter


def create_ifc_column(column: "Column", exporter: "IFCExporter") -> Any:
    """
    Create IfcColumn from Schmekla Column.

    Args:
        column: Schmekla Column element
        exporter: IFC exporter instance

    Returns:
        IfcColumn entity
    """
    import ifcopenshell.api

    ifc = exporter.ifc
    logger.debug(f"Creating IFC column for {column.id}")

    # Create column entity
    ifc_column = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcColumn",
        name=column.name or f"Column_{str(column.id)[:8]}"
    )

    # Create profile definition
    profile_def = column.profile.to_ifc_profile_def(exporter)

    # Create axis placement for the column
    # Column axis is vertical (Z direction)
    base_pt = column.base_point
    axis_placement = exporter.create_axis_placement(
        base_pt,
        direction=column.direction,  # Z axis
        ref_direction=None  # Will be calculated based on rotation
    )

    # Create extruded solid for column body
    # Direction of extrusion is Z (up)
    extrusion_dir = ifc.create_entity(
        "IfcDirection",
        DirectionRatios=[0.0, 0.0, 1.0]
    )

    # Calculate actual height
    actual_height = column.actual_height

    # Create extruded area solid
    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile_def,
        Position=axis_placement,
        ExtrudedDirection=extrusion_dir,
        Depth=actual_height
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

    # Assign representation to column
    ifc_column.Representation = product_shape

    # Create local placement
    # Account for base offset
    placement_point = column.base_point.translate(dz=column.base_offset)
    ifc_column.ObjectPlacement = exporter.create_local_placement(placement_point)

    # Add column-specific property set
    _add_column_properties(ifc_column, column, exporter)

    logger.debug(f"Created IfcColumn: {ifc_column.Name}")
    return ifc_column


def _add_column_properties(ifc_column: Any, column: "Column", exporter: "IFCExporter"):
    """Add column-specific properties to IFC entity."""
    import ifcopenshell.api

    ifc = exporter.ifc

    # Create property set
    pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_column,
        name="Pset_ColumnCommon"
    )

    # Add properties
    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=pset,
        properties={
            "Reference": column.name or str(column.id),
            "LoadBearing": True,
            "Slope": 0.0,  # Columns are vertical
        }
    )

    # Add Schmekla-specific properties
    schmekla_pset = ifcopenshell.api.run(
        "pset.add_pset", ifc,
        product=ifc_column,
        name="Schmekla_ColumnProperties"
    )

    ifcopenshell.api.run(
        "pset.edit_pset", ifc,
        pset=schmekla_pset,
        properties={
            "Height": column.height,
            "BaseOffset": column.base_offset,
            "TopOffset": column.top_offset,
            "Rotation": column.rotation,
        }
    )
