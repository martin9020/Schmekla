"""
Curved beam structural element for Schmekla.

Represents an arc-shaped structural member (hoop, curved rafter, etc.).
Used for barrel vault canopies and curved roof structures.
"""

import math
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
from src.core.profile import Profile
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class CurvedBeam(StructuralElement):
    """
    Curved structural beam element (arc/hoop).

    Defined by start point, end point, and rise (sag).
    The arc is in the vertical plane containing start and end points.
    """

    def __init__(
        self,
        start_point: Point3D,
        end_point: Point3D,
        rise: float,
        profile: Profile = None,
        material: Material = None,
        rotation: float = 0.0,
        name: str = "",
        segments: int = 12,
    ):
        """
        Create a curved beam (arc/hoop).

        Args:
            start_point: Arc start point
            end_point: Arc end point
            rise: Height of arc apex above the chord line (mm)
                  Positive = arc curves upward, Negative = arc curves downward
            profile: Section profile
            material: Material
            rotation: Rotation of profile around arc axis in degrees
            name: Element name/mark
            segments: Number of segments for discretization (for display/export)
        """
        super().__init__()

        self.start_point = start_point
        self.end_point = end_point
        self.rise = rise
        self._profile = profile or Profile.from_name("CHS 168.3x7.1")
        self._material = material or Material.default_steel()
        self.rotation = rotation
        self._name = name
        self.segments = segments

        # Calculate arc geometry
        self._calculate_arc_properties()

        logger.debug(f"Created CurvedBeam from {start_point} to {end_point}, rise={rise}")

    def _calculate_arc_properties(self):
        """Calculate arc center, radius, and angles."""
        # Chord vector and length
        self._chord_vector = self.end_point - self.start_point
        self._chord_length = self._chord_vector.length  # length is a property, not a method
        self._chord_midpoint = self.start_point.midpoint_to(self.end_point)

        # For a circular arc with known chord and rise:
        # radius = (chord^2 / (8 * rise)) + (rise / 2)
        if abs(self.rise) < 1e-6:
            # Essentially straight - treat as degenerate case
            self._radius = float('inf')
            self._arc_center = None
            self._arc_length = self._chord_length
            self._start_angle = 0
            self._end_angle = 0
            return

        half_chord = self._chord_length / 2
        self._radius = (half_chord ** 2 / (2 * abs(self.rise))) + (abs(self.rise) / 2)

        # Direction perpendicular to chord (in vertical plane)
        # Assuming arc is in the plane containing the chord and vertical
        chord_dir = self._chord_vector.normalize()

        # Get the "up" direction for the arc plane
        # For a barrel vault, this is typically in the Z direction
        world_z = Vector3D.unit_z()

        # Normal to the arc plane
        plane_normal = chord_dir.cross(world_z)
        if plane_normal.length < 1e-6:
            # Chord is vertical, use X as reference
            plane_normal = Vector3D.unit_x()
        plane_normal = plane_normal.normalize()

        # Up direction in arc plane (perpendicular to chord, in arc plane)
        up_in_plane = plane_normal.cross(chord_dir).normalize()

        # Center is below/above midpoint depending on rise sign
        # Distance from midpoint to center along up direction
        center_offset = self._radius - abs(self.rise)

        if self.rise > 0:
            # Arc curves upward, center is below
            self._arc_center = self._chord_midpoint - up_in_plane * center_offset
        else:
            # Arc curves downward, center is above
            self._arc_center = self._chord_midpoint + up_in_plane * center_offset

        # Calculate arc angles
        start_vec = self.start_point - self._arc_center
        end_vec = self.end_point - self._arc_center

        # Arc angle (total sweep)
        cos_half_angle = (self._radius - abs(self.rise)) / self._radius
        cos_half_angle = max(-1, min(1, cos_half_angle))  # Clamp for numerical stability
        half_angle = math.acos(cos_half_angle)
        self._sweep_angle = 2 * half_angle

        # Arc length
        self._arc_length = self._radius * self._sweep_angle

        # Store up direction for later use
        self._up_direction = up_in_plane

    @property
    def element_type(self) -> ElementType:
        return ElementType.BEAM  # Treated as beam type for IFC

    @property
    def chord_length(self) -> float:
        """Straight-line distance from start to end."""
        return self._chord_length

    @property
    def arc_length(self) -> float:
        """Length along the arc."""
        return self._arc_length

    @property
    def radius(self) -> float:
        """Arc radius."""
        return self._radius

    @property
    def apex_point(self) -> Point3D:
        """Highest/lowest point of the arc."""
        return self._chord_midpoint + self._up_direction * self.rise

    def get_point_at_parameter(self, t: float) -> Point3D:
        """
        Get point on arc at parameter t (0 to 1).

        Args:
            t: Parameter from 0 (start) to 1 (end)

        Returns:
            Point on the arc
        """
        if self._arc_center is None:
            # Degenerate case - straight line
            return self.start_point + self._chord_vector * t

        # Angle at parameter t
        start_vec = (self.start_point - self._arc_center).normalize()

        # Rotate start vector around plane normal
        chord_dir = self._chord_vector.normalize()
        world_z = Vector3D.unit_z()
        plane_normal = chord_dir.cross(world_z)
        if plane_normal.length < 1e-6:
            plane_normal = Vector3D.unit_x()
        plane_normal = plane_normal.normalize()

        # Angle to rotate (negative because we go from start to end)
        angle = t * self._sweep_angle
        if self.rise > 0:
            angle = -angle  # Reverse for upward arc

        # Rotate the start vector
        rotated = start_vec.rotate_around_axis(plane_normal, math.degrees(angle))

        return self._arc_center + rotated * self._radius

    def get_arc_points(self, num_points: int = None) -> List[Point3D]:
        """
        Get discretized points along the arc.

        Args:
            num_points: Number of points (default: self.segments + 1)

        Returns:
            List of points along the arc
        """
        if num_points is None:
            num_points = self.segments + 1

        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            points.append(self.get_point_at_parameter(t))

        return points

    def generate_solid(self) -> Any:
        """
        Generate curved beam solid by sweeping profile along arc.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq
            from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
            from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe
            from OCC.Core.GC import GC_MakeArcOfCircle
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

            logger.debug(f"Generating solid for curved beam {self._id}")

            # Create arc path
            p1 = gp_Pnt(self.start_point.x, self.start_point.y, self.start_point.z)
            p2 = gp_Pnt(self.apex_point.x, self.apex_point.y, self.apex_point.z)
            p3 = gp_Pnt(self.end_point.x, self.end_point.y, self.end_point.z)

            # Create arc through 3 points
            arc = GC_MakeArcOfCircle(p1, p2, p3).Value()
            edge = BRepBuilderAPI_MakeEdge(arc).Edge()
            wire = BRepBuilderAPI_MakeWire(edge).Wire()

            # Create profile at start
            profile_shape = self._create_profile_shape()

            # Sweep profile along arc
            pipe = BRepOffsetAPI_MakePipe(wire, profile_shape)
            pipe.Build()

            if pipe.IsDone():
                return pipe.Shape()
            else:
                logger.warning("Pipe sweep failed, using segmented fallback")
                return self._create_segmented_solid()

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return self._create_segmented_solid()
        except Exception as e:
            logger.error(f"Failed to generate curved beam solid: {e}")
            return self._create_segmented_solid()

    def _create_profile_shape(self):
        """Create profile shape for sweeping."""
        try:
            import cadquery as cq
            from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Circ
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace

            # For CHS profiles, create circular face
            if self._profile and "CHS" in self._profile.name:
                # Circular hollow section
                radius = self._profile.d / 2 if hasattr(self._profile, 'd') else 84.15  # Default CHS 168.3

                # Create at start point with correct orientation
                chord_dir = self._chord_vector.normalize()
                center = gp_Pnt(self.start_point.x, self.start_point.y, self.start_point.z)
                direction = gp_Dir(chord_dir.x, chord_dir.y, chord_dir.z)
                ax2 = gp_Ax2(center, direction)

                circle = gp_Circ(ax2, radius)
                edge = BRepBuilderAPI_MakeEdge(circle).Edge()
                wire = BRepBuilderAPI_MakeWire(edge).Wire()
                face = BRepBuilderAPI_MakeFace(wire).Face()
                return face

            # For I-sections, create rectangular approximation
            width = self._profile.b if self._profile else 100
            height = self._profile.h if self._profile else 100

            result = (
                cq.Workplane("XY")
                .transformed(offset=(self.start_point.x, self.start_point.y, self.start_point.z))
                .rect(width, height)
            )
            return result.val().wrapped

        except Exception as e:
            logger.error(f"Failed to create profile shape: {e}")
            return None

    def _create_segmented_solid(self):
        """Create segmented solid as fallback (multiple straight segments)."""
        try:
            import cadquery as cq

            logger.debug("Creating segmented curved beam geometry")

            # Get arc points
            points = self.get_arc_points()

            # Create segments
            result = None
            width = self._profile.b if self._profile else 100
            height = self._profile.h if self._profile else 100

            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]

                seg_length = p1.distance_to(p2)
                direction = (p2 - p1).normalize()

                # Create segment box
                segment = (
                    cq.Workplane("XY")
                    .transformed(offset=(p1.x, p1.y, p1.z))
                    .rect(width, height)
                    .extrude(seg_length)
                )

                if result is None:
                    result = segment
                else:
                    result = result.union(segment)

            return result.val().wrapped if result else None

        except Exception as e:
            logger.error(f"Failed to create segmented solid: {e}")
            return None

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export curved beam to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcBeam entity
        """
        from src.ifc.ifc_curved_beam import create_ifc_curved_beam
        return create_ifc_curved_beam(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get curved beam-specific properties."""
        return {
            "Chord Length": f"{self.chord_length:.1f} mm",
            "Arc Length": f"{self.arc_length:.1f} mm",
            "Rise": f"{self.rise:.1f} mm",
            "Radius": f"{self.radius:.1f} mm",
            "Start Point": str(self.start_point),
            "End Point": str(self.end_point),
            "Apex Point": str(self.apex_point),
            "Segments": self.segments,
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set curved beam property."""
        if super().set_property(name, value):
            return True

        if name == "Rise":
            self.rise = float(value)
            self._calculate_arc_properties()
            self.invalidate()
            return True
        elif name == "Segments":
            self.segments = int(value)
            self.invalidate()
            return True

        return False

    def move(self, vector: Vector3D):
        """Move curved beam by vector."""
        self.start_point = self.start_point + vector
        self.end_point = self.end_point + vector
        self._calculate_arc_properties()
        self.invalidate()

    def copy(self) -> "CurvedBeam":
        """Create a copy of this curved beam."""
        new_beam = CurvedBeam(
            self.start_point.copy(),
            self.end_point.copy(),
            self.rise,
            self._profile,
            self._material,
            self.rotation,
            self._name,
            self.segments
        )
        return new_beam

    def to_straight_segments(self) -> List["Beam"]:
        """
        Convert to list of straight beam segments.

        Useful for export to systems that don't support curved members.

        Returns:
            List of Beam objects approximating the arc
        """
        from src.core.beam import Beam

        points = self.get_arc_points()
        segments = []

        for i in range(len(points) - 1):
            segment = Beam(
                points[i],
                points[i + 1],
                self._profile,
                self._material,
                self.rotation,
                f"{self._name}_seg{i + 1}"
            )
            segments.append(segment)

        return segments

    def __repr__(self) -> str:
        return f"CurvedBeam(id={self._id}, {self.start_point} -> {self.end_point}, rise={self.rise}, {self._profile.name if self._profile else 'no profile'})"


# Convenience factory functions
def create_barrel_hoop(
    grid_line_start: Point3D,
    grid_line_end: Point3D,
    eaves_height: float,
    apex_height: float,
    profile: Profile = None,
    name: str = ""
) -> CurvedBeam:
    """
    Create a barrel vault hoop from grid positions.

    Args:
        grid_line_start: Start point at ground level on grid
        grid_line_end: End point at ground level on grid
        eaves_height: Height of eaves (where columns meet hoop)
        apex_height: Height of apex (top of barrel)
        profile: Section profile (default: CHS 168.3x7.1)
        name: Hoop name/mark

    Returns:
        CurvedBeam representing the hoop
    """
    # Create points at eaves level
    start_at_eaves = Point3D(grid_line_start.x, grid_line_start.y, eaves_height)
    end_at_eaves = Point3D(grid_line_end.x, grid_line_end.y, eaves_height)

    # Rise is the difference between apex and eaves
    rise = apex_height - eaves_height

    return CurvedBeam(
        start_at_eaves,
        end_at_eaves,
        rise,
        profile or Profile.from_name("CHS 168.3x7.1"),
        name=name
    )
