"""
IFC Curved Beam export for Schmekla.

Creates IfcBeam entities with curved axis from Schmekla CurvedBeam elements.
For IFC2X3 compatibility, curved beams are represented as:
1. Swept solid along polyline approximation, or
2. Tessellated solid for maximum compatibility
"""

import math
from typing import TYPE_CHECKING, List
from loguru import logger

if TYPE_CHECKING:
    from src.core.curved_beam import CurvedBeam
    from src.ifc.exporter import IFCExporter


def create_ifc_curved_beam(curved_beam: "CurvedBeam", exporter: "IFCExporter"):
    """
    Create IfcBeam from Schmekla CurvedBeam.

    For Tekla compatibility, creates a polyline-based swept solid
    that approximates the arc.

    Args:
        curved_beam: Schmekla CurvedBeam element
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
        name=curved_beam.name or f"CB-{str(curved_beam.id)[:8]}"
    )

    # Create profile definition
    profile = _create_profile(curved_beam.profile, ifc)

    # Get arc points for polyline representation
    arc_points = curved_beam.get_arc_points()

    # Create representation based on schema version
    schema = ifc.schema
    if "IFC4" in schema:
        # IFC4: Can use IfcSweptDiskSolid with proper curve
        solid = _create_ifc4_swept_solid(curved_beam, arc_points, profile, ifc, exporter)
    else:
        # IFC2X3: Use faceted brep or multiple swept segments
        solid = _create_ifc2x3_representation(curved_beam, arc_points, profile, ifc, exporter)

    if solid is None:
        logger.error("Failed to create solid for curved beam")
        return None

    # Create shape representation
    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SolidModel",
        Items=[solid]
    )

    # Create product definition shape
    product_shape = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )

    # Assign representation to beam
    ifc_beam.Representation = product_shape

    # Create local placement at origin (geometry is in world coords)
    ifc_beam.ObjectPlacement = exporter.create_local_placement()

    # Add property set with curved beam info
    _add_property_set(curved_beam, ifc_beam, ifc, exporter)

    logger.debug(f"Created IfcBeam (curved) for {curved_beam.id}")

    return ifc_beam


def _create_ifc2x3_representation(curved_beam, arc_points, profile, ifc, exporter):
    """
    Create IFC2X3 compatible representation for curved beam.

    Uses faceted brep to represent the curved surface.

    Args:
        curved_beam: CurvedBeam element
        arc_points: List of points along arc
        profile: IFC profile entity
        ifc: IFC file
        exporter: IFC exporter

    Returns:
        IFC solid entity
    """
    try:
        # Create swept solid along polyline path
        # Build a polyline from arc points
        cartesian_points = []
        for pt in arc_points:
            cp = ifc.create_entity(
                "IfcCartesianPoint",
                Coordinates=(pt.x, pt.y, pt.z)
            )
            cartesian_points.append(cp)

        # Create polyline for directrix
        polyline = ifc.create_entity(
            "IfcPolyline",
            Points=cartesian_points
        )

        # For circular profiles, use IfcSweptDiskSolid
        if _is_circular_profile(curved_beam.profile):
            radius = curved_beam.profile.d / 2 if hasattr(curved_beam.profile, 'd') else 84.15
            inner_radius = radius - curved_beam.profile.t if hasattr(curved_beam.profile, 't') else radius - 7.1

            solid = ifc.create_entity(
                "IfcSweptDiskSolid",
                Directrix=polyline,
                Radius=radius,
                InnerRadius=inner_radius if inner_radius > 0 else None,
                StartParam=0.0,
                EndParam=1.0
            )
            return solid

        # For non-circular profiles, create faceted brep
        return _create_faceted_brep(curved_beam, arc_points, ifc, exporter)

    except Exception as e:
        logger.error(f"Failed to create IFC2X3 representation: {e}")
        return _create_faceted_brep(curved_beam, arc_points, ifc, exporter)


def _create_ifc4_swept_solid(curved_beam, arc_points, profile, ifc, exporter):
    """
    Create IFC4 swept solid along arc.

    Args:
        curved_beam: CurvedBeam element
        arc_points: List of points along arc
        profile: IFC profile entity
        ifc: IFC file
        exporter: IFC exporter

    Returns:
        IFC solid entity
    """
    try:
        # Create trimmed curve (arc)
        start_pt = curved_beam.start_point
        apex_pt = curved_beam.apex_point
        end_pt = curved_beam.end_point

        # Create cartesian points for arc
        p1 = ifc.create_entity("IfcCartesianPoint", Coordinates=(start_pt.x, start_pt.y, start_pt.z))
        p2 = ifc.create_entity("IfcCartesianPoint", Coordinates=(apex_pt.x, apex_pt.y, apex_pt.z))
        p3 = ifc.create_entity("IfcCartesianPoint", Coordinates=(end_pt.x, end_pt.y, end_pt.z))

        # Create B-spline or polyline through points
        cartesian_points = []
        for pt in arc_points:
            cp = ifc.create_entity("IfcCartesianPoint", Coordinates=(pt.x, pt.y, pt.z))
            cartesian_points.append(cp)

        polyline = ifc.create_entity(
            "IfcPolyline",
            Points=cartesian_points
        )

        # Create swept disk solid for circular profiles
        if _is_circular_profile(curved_beam.profile):
            radius = curved_beam.profile.d / 2 if hasattr(curved_beam.profile, 'd') else 84.15
            inner_radius = radius - curved_beam.profile.t if hasattr(curved_beam.profile, 't') else radius - 7.1

            solid = ifc.create_entity(
                "IfcSweptDiskSolid",
                Directrix=polyline,
                Radius=radius,
                InnerRadius=inner_radius if inner_radius > 0 else None,
                StartParam=0.0,
                EndParam=1.0
            )
            return solid

        # For other profiles, use IfcFixedReferenceSweptAreaSolid
        # This requires a reference direction along the path
        ref_dir = ifc.create_entity(
            "IfcDirection",
            DirectionRatios=(0.0, 0.0, 1.0)
        )

        solid = ifc.create_entity(
            "IfcFixedReferenceSweptAreaSolid",
            SweptArea=profile,
            Directrix=polyline,
            FixedReference=ref_dir
        )
        return solid

    except Exception as e:
        logger.error(f"Failed to create IFC4 swept solid: {e}")
        return _create_faceted_brep(curved_beam, arc_points, ifc, exporter)


def _create_faceted_brep(curved_beam, arc_points, ifc, exporter):
    """
    Create faceted brep representation as fallback.

    This creates a tessellated solid that any IFC viewer can handle.

    Args:
        curved_beam: CurvedBeam element
        arc_points: List of points along arc
        ifc: IFC file
        exporter: IFC exporter

    Returns:
        IfcFacetedBrep entity
    """
    try:
        from src.geometry.point import Point3D
        from src.geometry.vector import Vector3D

        # Get profile dimensions
        profile = curved_beam.profile
        if _is_circular_profile(profile):
            # For circular profiles, create octagonal approximation
            radius = profile.d / 2 if hasattr(profile, 'd') else 84.15
            num_sides = 8
            profile_points = []
            for i in range(num_sides):
                angle = 2 * math.pi * i / num_sides
                profile_points.append((radius * math.cos(angle), radius * math.sin(angle)))
        else:
            # Rectangular profile
            w = profile.b / 2 if profile else 50
            h = profile.h / 2 if profile else 50
            profile_points = [(-w, -h), (w, -h), (w, h), (-w, h)]

        # Generate vertices along the arc
        all_vertices = []
        for pt in arc_points:
            # Calculate local coordinate system at this point
            idx = arc_points.index(pt)
            if idx < len(arc_points) - 1:
                tangent = (arc_points[idx + 1] - pt).normalize()
            else:
                tangent = (pt - arc_points[idx - 1]).normalize()

            # Up direction (toward apex)
            up = Vector3D.unit_z()
            if abs(tangent.dot(up)) > 0.99:
                up = Vector3D.unit_y()

            # Local x and y axes
            local_x = tangent.cross(up).normalize()
            local_y = tangent.cross(local_x).normalize()

            # Transform profile points to world coordinates
            for px, py in profile_points:
                world_pt = (
                    pt.x + px * local_x.x + py * local_y.x,
                    pt.y + px * local_x.y + py * local_y.y,
                    pt.z + px * local_x.z + py * local_y.z
                )
                all_vertices.append(world_pt)

        # Create IFC cartesian points
        ifc_points = []
        for v in all_vertices:
            cp = ifc.create_entity("IfcCartesianPoint", Coordinates=v)
            ifc_points.append(cp)

        # Create faces
        faces = []
        num_profile_pts = len(profile_points)
        num_segments = len(arc_points) - 1

        for seg in range(num_segments):
            base_idx = seg * num_profile_pts
            next_base_idx = (seg + 1) * num_profile_pts

            for i in range(num_profile_pts):
                i_next = (i + 1) % num_profile_pts

                # Create quad face
                p1 = ifc_points[base_idx + i]
                p2 = ifc_points[base_idx + i_next]
                p3 = ifc_points[next_base_idx + i_next]
                p4 = ifc_points[next_base_idx + i]

                # Create polyloop
                poly_loop = ifc.create_entity(
                    "IfcPolyLoop",
                    Polygon=[p1, p2, p3, p4]
                )

                face_bound = ifc.create_entity(
                    "IfcFaceOuterBound",
                    Bound=poly_loop,
                    Orientation=True
                )

                face = ifc.create_entity(
                    "IfcFace",
                    Bounds=[face_bound]
                )
                faces.append(face)

        # End caps
        # Start cap
        start_pts = [ifc_points[i] for i in range(num_profile_pts)]
        start_loop = ifc.create_entity("IfcPolyLoop", Polygon=start_pts[::-1])
        start_bound = ifc.create_entity("IfcFaceOuterBound", Bound=start_loop, Orientation=True)
        start_face = ifc.create_entity("IfcFace", Bounds=[start_bound])
        faces.append(start_face)

        # End cap
        end_start_idx = num_segments * num_profile_pts
        end_pts = [ifc_points[end_start_idx + i] for i in range(num_profile_pts)]
        end_loop = ifc.create_entity("IfcPolyLoop", Polygon=end_pts)
        end_bound = ifc.create_entity("IfcFaceOuterBound", Bound=end_loop, Orientation=True)
        end_face = ifc.create_entity("IfcFace", Bounds=[end_bound])
        faces.append(end_face)

        # Create closed shell
        shell = ifc.create_entity(
            "IfcClosedShell",
            CfsFaces=faces
        )

        # Create faceted brep
        brep = ifc.create_entity(
            "IfcFacetedBrep",
            Outer=shell
        )

        return brep

    except Exception as e:
        logger.error(f"Failed to create faceted brep: {e}")
        return None


def _is_circular_profile(profile) -> bool:
    """Check if profile is circular hollow section."""
    if profile is None:
        return True  # Default assumption for hoops
    return "CHS" in profile.name if hasattr(profile, 'name') else False


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

    if profile is None:
        # Default CHS profile
        return ifc.create_entity(
            "IfcCircleHollowProfileDef",
            ProfileType="AREA",
            ProfileName="CHS 168.3x7.1",
            Radius=84.15,
            WallThickness=7.1
        )

    if profile.profile_type == ProfileType.CIRCULAR_HOLLOW:
        return ifc.create_entity(
            "IfcCircleHollowProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            Radius=profile.d / 2,
            WallThickness=profile.t
        )

    elif profile.profile_type == ProfileType.I_SECTION:
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

    else:
        # Default rectangle
        return ifc.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name if profile else "RECT",
            XDim=profile.b if profile else 100,
            YDim=profile.h if profile else 100
        )


def _add_property_set(curved_beam, ifc_beam, ifc, exporter):
    """Add custom property set with curved beam information."""
    try:
        import ifcopenshell.api

        # Create property set
        pset = ifcopenshell.api.run(
            "pset.add_pset", ifc,
            product=ifc_beam,
            name="Schmekla_CurvedBeamProperties"
        )

        ifcopenshell.api.run(
            "pset.edit_pset", ifc,
            pset=pset,
            properties={
                "ChordLength": curved_beam.chord_length,
                "ArcLength": curved_beam.arc_length,
                "Rise": curved_beam.rise,
                "Radius": curved_beam.radius,
                "Segments": curved_beam.segments
            }
        )

    except Exception as e:
        logger.debug(f"Could not add property set: {e}")
