"""
Beam structural element for Schmekla.

Represents a linear structural member (beam, girder, etc.).
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType, EndPointOffsets, LocalCoordinateSystem
from src.core.profile import Profile
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Beam(StructuralElement):
    """
    Structural beam element.

    A linear element defined by start and end points.
    """

    def __init__(
        self,
        start_point: Point3D,
        end_point: Point3D,
        profile: Profile = None,
        material: Material = None,
        rotation: float = 0.0,
        name: str = "",
    ):
        """
        Create a beam.

        Args:
            start_point: Beam start point
            end_point: Beam end point
            profile: Section profile
            material: Material
            rotation: Rotation around beam axis in degrees
            name: Element name/mark
        """
        super().__init__()

        self.start_point = start_point
        self.end_point = end_point
        self._profile = profile or Profile.from_name("UB 305x165x40")
        self._material = material or Material.default_steel()
        self.rotation = rotation
        self._name = name

        # Beam-specific properties - local coordinate offsets
        self._start_offsets = EndPointOffsets()  # Offset at start in local coordinates
        self._end_offsets = EndPointOffsets()    # Offset at end in local coordinates
        self.camber = 0.0                        # Camber in mm

        # Connection info (for reference)
        self.start_connection: str = ""
        self.end_connection: str = ""

        logger.debug(f"Created Beam from {start_point} to {end_point}")

    @property
    def element_type(self) -> ElementType:
        return ElementType.BEAM

    @property
    def length(self) -> float:
        """Beam length in mm."""
        return self.start_point.distance_to(self.end_point)

    @property
    def direction(self) -> Vector3D:
        """Unit direction vector from start to end."""
        return (self.end_point - self.start_point).normalize()

    @property
    def midpoint(self) -> Point3D:
        """Beam midpoint."""
        return self.start_point.midpoint_to(self.end_point)

    @property
    def start_offsets(self) -> EndPointOffsets:
        """Offset values at start point in local coordinates."""
        return self._start_offsets

    @start_offsets.setter
    def start_offsets(self, value: EndPointOffsets):
        self._start_offsets = value
        self.invalidate()

    @property
    def end_offsets(self) -> EndPointOffsets:
        """Offset values at end point in local coordinates."""
        return self._end_offsets

    @end_offsets.setter
    def end_offsets(self, value: EndPointOffsets):
        self._end_offsets = value
        self.invalidate()

    def get_local_coordinate_system(self, at_start: bool = True) -> LocalCoordinateSystem:
        """
        Get the local coordinate system at start or end point.

        The local coordinate system is defined as:
        - X-axis: Along element (from start to end)
        - Y-axis: Up direction (typically perpendicular to beam in vertical plane)
        - Z-axis: Right-hand perpendicular (completes right-hand system)

        Args:
            at_start: If True, origin is at start point; otherwise at end point

        Returns:
            LocalCoordinateSystem with origin, x_axis, y_axis, z_axis
        """
        # X-axis is along the beam
        x_axis = self.direction
        world_z = Vector3D.unit_z()

        # Calculate local Y axis (typically "up" relative to beam)
        if abs(x_axis.dot(world_z)) > 0.99:
            # Beam is nearly vertical, use X as reference
            y_axis = Vector3D.unit_x().cross(x_axis).normalize()
        else:
            # Use world Z to define "up"
            y_axis = x_axis.cross(world_z).cross(x_axis).normalize()

        # Z-axis completes the right-hand system
        z_axis = x_axis.cross(y_axis).normalize()

        # Apply rotation around beam axis
        if self.rotation != 0:
            y_axis = y_axis.rotate_around_axis(x_axis, self.rotation)
            z_axis = z_axis.rotate_around_axis(x_axis, self.rotation)

        origin = self.start_point if at_start else self.end_point

        return LocalCoordinateSystem(
            origin=origin,
            x_axis=x_axis,
            y_axis=y_axis,
            z_axis=z_axis
        )

    def get_actual_start_point(self) -> Point3D:
        """
        Get the actual start point after applying local offsets.

        Returns:
            Point3D representing the actual start position
        """
        if self._start_offsets.is_zero():
            return self.start_point.copy()

        local_cs = self.get_local_coordinate_system(at_start=True)
        global_offset = local_cs.transform_offsets_to_global(self._start_offsets)
        return self.start_point + global_offset

    def get_actual_end_point(self) -> Point3D:
        """
        Get the actual end point after applying local offsets.

        Returns:
            Point3D representing the actual end position
        """
        if self._end_offsets.is_zero():
            return self.end_point.copy()

        local_cs = self.get_local_coordinate_system(at_start=False)
        global_offset = local_cs.transform_offsets_to_global(self._end_offsets)
        return self.end_point + global_offset

    def swap_start_end(self):
        """
        Swap the start and end points of the beam.

        This also swaps the associated offsets and connection info.
        """
        # Swap points
        self.start_point, self.end_point = self.end_point, self.start_point

        # Swap offsets
        self._start_offsets, self._end_offsets = self._end_offsets, self._start_offsets

        # Swap connection info
        self.start_connection, self.end_connection = self.end_connection, self.start_connection

        self.invalidate()
        logger.debug(f"Swapped start/end for beam {self._id}")

    def generate_solid(self) -> Any:
        """
        Generate beam solid by sweeping profile along axis.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq
            from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2

            logger.debug(f"Generating solid for beam {self._id}")

            # Get actual start/end with offsets
            actual_start = self.get_actual_start_point()
            actual_end = self.get_actual_end_point()

            # Create profile at start point
            profile_wire = self._create_profile_wire()

            # Determine local coordinate system
            z_dir = self.direction  # Beam axis
            world_z = Vector3D.unit_z()

            # Calculate local Y axis (typically "up" relative to beam)
            if abs(z_dir.dot(world_z)) > 0.99:
                # Beam is nearly vertical, use X as reference
                y_dir = Vector3D.unit_x().cross(z_dir).normalize()
            else:
                # Use world Z to define "up"
                y_dir = z_dir.cross(world_z).cross(z_dir).normalize()

            x_dir = y_dir.cross(z_dir).normalize()

            # Apply rotation around beam axis
            if self.rotation != 0:
                y_dir = y_dir.rotate_around_axis(z_dir, self.rotation)
                x_dir = x_dir.rotate_around_axis(z_dir, self.rotation)

            # Create the swept solid
            # Using CadQuery for simplicity
            result = (
                cq.Workplane("XY")
                .transformed(
                    offset=(actual_start.x, actual_start.y, actual_start.z),
                    rotate=(0, 0, 0)  # TODO: proper rotation
                )
                .rect(self._profile.b, self._profile.h)
                .extrude(self.length)
            )

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return self._create_simple_box()
        except Exception as e:
            logger.error(f"Failed to generate beam solid: {e}")
            return self._create_simple_box()

    def _create_profile_wire(self):
        """Create profile wire for sweeping."""
        return self._profile.to_cadquery_wire()

    def _create_simple_box(self):
        """Create simple box as fallback geometry."""
        try:
            import cadquery as cq

            # Simple extruded rectangle
            length = self.length
            width = self._profile.b if self._profile else 100
            height = self._profile.h if self._profile else 100

            box = cq.Workplane("XY").box(width, height, length)
            return box.val().wrapped

        except Exception as e:
            logger.error(f"Failed to create fallback geometry: {e}")
            return None

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export beam to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcBeam entity
        """
        from src.ifc.ifc_beam import create_ifc_beam
        return create_ifc_beam(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get beam-specific properties."""
        return {
            "Length": f"{self.length:.1f} mm",
            "Start Point": str(self.start_point),
            "End Point": str(self.end_point),
            "Rotation": f"{self.rotation}°",
            "Camber": f"{self.camber} mm",
            "Start Offset DX": f"{self._start_offsets.dx:.1f} mm",
            "Start Offset DY": f"{self._start_offsets.dy:.1f} mm",
            "Start Offset DZ": f"{self._start_offsets.dz:.1f} mm",
            "End Offset DX": f"{self._end_offsets.dx:.1f} mm",
            "End Offset DY": f"{self._end_offsets.dy:.1f} mm",
            "End Offset DZ": f"{self._end_offsets.dz:.1f} mm",
        }

    def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
        """
        Calculate geometry key for beam based on length.

        Beams with the same length (within tolerance) are considered
        geometrically identical for Tekla-style numbering.

        Args:
            tolerance: Rounding tolerance in mm

        Returns:
            Geometry key string like "L6000"
        """
        rounded_length = round(self.length / tolerance) * tolerance
        return f"L{rounded_length:.0f}"

    def _get_rotation_key(self) -> Optional[int]:
        """
        Get rotation key for beam signature.

        Beams with different rotations are considered different parts.

        Returns:
            Rotation in degrees (rounded) or None if rotation is essentially zero
        """
        return round(self.rotation)

    def set_property(self, name: str, value: Any) -> bool:
        """Set beam property."""
        if super().set_property(name, value):
            return True

        if name == "Rotation":
            self.rotation = float(value)
            self.invalidate()
            return True
        elif name == "Camber":
            self.camber = float(value)
            self.invalidate()
            return True
        elif name == "Start Offset DX":
            self._start_offsets.dx = float(value)
            self.invalidate()
            return True
        elif name == "Start Offset DY":
            self._start_offsets.dy = float(value)
            self.invalidate()
            return True
        elif name == "Start Offset DZ":
            self._start_offsets.dz = float(value)
            self.invalidate()
            return True
        elif name == "End Offset DX":
            self._end_offsets.dx = float(value)
            self.invalidate()
            return True
        elif name == "End Offset DY":
            self._end_offsets.dy = float(value)
            self.invalidate()
            return True
        elif name == "End Offset DZ":
            self._end_offsets.dz = float(value)
            self.invalidate()
            return True

        return False

    def split_at_point(self, point: Point3D) -> tuple:
        """
        Split beam at given point.

        Args:
            point: Split point (should be on beam axis)

        Returns:
            Tuple of two new Beam objects
        """
        beam1 = Beam(
            self.start_point.copy(),
            point.copy(),
            self._profile,
            self._material,
            self.rotation
        )
        beam2 = Beam(
            point.copy(),
            self.end_point.copy(),
            self._profile,
            self._material,
            self.rotation
        )
        return (beam1, beam2)

    def extend_to_plane(self, plane) -> bool:
        """
        Extend beam to intersect with plane.

        Args:
            plane: Target plane

        Returns:
            True if beam was extended
        """
        from src.geometry.line import Line3D

        line = Line3D(self.start_point, self.end_point)
        intersection = line.intersection_with_plane(plane)

        if intersection is None:
            return False

        # Determine which end to extend
        dist_start = self.start_point.distance_to(intersection)
        dist_end = self.end_point.distance_to(intersection)

        if dist_start > self.length:
            # Extend at start
            self.start_point = intersection
        else:
            # Extend at end
            self.end_point = intersection

        self.invalidate()
        return True

    def move(self, vector: Vector3D):
        """Move beam by vector."""
        self.start_point = self.start_point + vector
        self.end_point = self.end_point + vector
        self.invalidate()

    def copy(self) -> "Beam":
        """Create a copy of this beam."""
        new_beam = Beam(
            self.start_point.copy(),
            self.end_point.copy(),
            self._profile,
            self._material,
            self.rotation,
            self._name
        )
        new_beam._start_offsets = self._start_offsets.copy()
        new_beam._end_offsets = self._end_offsets.copy()
        new_beam.camber = self.camber
        new_beam.start_connection = self.start_connection
        new_beam.end_connection = self.end_connection
        return new_beam

    def __repr__(self) -> str:
        return f"Beam(id={self._id}, {self.start_point} -> {self.end_point}, {self._profile.name if self._profile else 'no profile'})"
