"""
Beam structural element for Schmekla.

Represents a linear structural member (beam, girder, etc.).
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
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

        # Beam-specific properties
        self.start_offset = Vector3D.zero()  # Offset at start
        self.end_offset = Vector3D.zero()    # Offset at end
        self.camber = 0.0                    # Camber in mm

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

    def generate_solid(self) -> Any:
        """
        Generate beam solid by sweeping profile along axis.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq
            from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2

            logger.debug(f"Generating solid for beam {self._id}")

            # Get actual start/end with offsets
            actual_start = self.start_point + self.start_offset
            actual_end = self.end_point + self.end_offset

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
        }

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
        new_beam.start_offset = self.start_offset.copy()
        new_beam.end_offset = self.end_offset.copy()
        new_beam.camber = self.camber
        return new_beam

    def __repr__(self) -> str:
        return f"Beam(id={self._id}, {self.start_point} -> {self.end_point}, {self._profile.name if self._profile else 'no profile'})"
