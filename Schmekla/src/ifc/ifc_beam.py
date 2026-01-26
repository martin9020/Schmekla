"""
IFC Beam export for Schmekla.

Creates IfcBeam entities from Schmekla Beam elements.
"""

from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.beam import Beam
    from src.ifc.exporter import IFCExporter


def create_ifc_beam(beam: "Beam", exporter: "IFCExporter"):
    """
    Create IfcBeam from Schmekla Beam.

    Args:
        beam: Schmekla Beam element
        exporter: IFC exporter instance

    Returns:
        IfcBeam entity
    """
    try:
        import ifcopenshell.api
    except ImportError:
        logger.error("ifcopenshell not installed")
        return None

    ifc = exporter.ifc

    # Create beam entity
    ifc_beam = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcBeam",
        name=beam.name or f"B-{str(beam.id)[:8]}"
    )

    # Create profile definition
    profile = _create_profile(beam.profile, ifc)

    # Calculate beam direction and position
    start = beam.start_point
    end = beam.end_point
    direction = beam.direction
    length = beam.length

    # Create axis placement for swept solid
    # The extrusion direction is along the beam axis
    axis_placement = exporter.create_axis_placement(start, direction)

    # Create extruded area solid
    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=axis_placement,
        ExtrudedDirection=ifc.create_entity(
            "IfcDirection",
            DirectionRatios=[0.0, 0.0, 1.0]
        ),
        Depth=length
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

    # Assign representation to beam
    ifc_beam.Representation = product_shape

    # Create local placement
    ifc_beam.ObjectPlacement = exporter.create_local_placement(start)

    logger.debug(f"Created IfcBeam for {beam.id}")

    return ifc_beam


def _create_profile(profile, ifc):
    """
    Create IFC profile definition.

    Args:
        profile: Schmekla Profile
        ifc: IFC file

    Returns:
        IFC profile entity
    """
    from src.core.profile import ProfileType

    if profile.profile_type == ProfileType.I_SECTION:
        return ifc.create_entity(
            "IfcIShapeProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            OverallWidth=profile.b,
            OverallDepth=profile.h,
            WebThickness=profile.tw,
            FlangeThickness=profile.tf,
            FilletRadius=profile.r if profile.r > 0 else None
        )

    elif profile.profile_type == ProfileType.RECTANGULAR_HOLLOW:
        return ifc.create_entity(
            "IfcRectangleHollowProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            XDim=profile.b,
            YDim=profile.h,
            WallThickness=profile.t
        )

    elif profile.profile_type == ProfileType.SQUARE_HOLLOW:
        return ifc.create_entity(
            "IfcRectangleHollowProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            XDim=profile.b,
            YDim=profile.b,
            WallThickness=profile.t
        )

    elif profile.profile_type == ProfileType.CIRCULAR_HOLLOW:
        return ifc.create_entity(
            "IfcCircleHollowProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            Radius=profile.d / 2,
            WallThickness=profile.t
        )

    elif profile.profile_type == ProfileType.CHANNEL:
        return ifc.create_entity(
            "IfcCShapeProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            Depth=profile.h,
            Width=profile.b,
            WallThickness=profile.tw,
            Girth=profile.tf
        )

    else:
        # Default to rectangle
        return ifc.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            XDim=profile.b or 100,
            YDim=profile.h or 100
        )
