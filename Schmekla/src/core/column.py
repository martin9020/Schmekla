"""
Column structural element for Schmekla.

Represents a vertical structural member (column, post, pier).
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType, EndPointOffsets, LocalCoordinateSystem
from src.core.profile import Profile
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Column(StructuralElement):
    """
    Structural column element.

    A vertical element defined by base point and height.
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
        Create a column.

        Args:
            start_point: Column start point (bottom/base)
            end_point: Column end point (top)
            profile: Section profile
            material: Material
            rotation: Rotation around Z axis in degrees
            name: Element name/mark
        """
        super().__init__()

        self.start_point = start_point
        self.end_point = end_point
        self._profile = profile or Profile.from_name("UC 203x203x46")
        self._material = material or Material.default_steel()
        self.rotation = rotation
        self._name = name

        # Note: height is now a computed property - no assignment needed

        # Column-specific properties - local coordinate offsets
        self._start_offsets = EndPointOffsets()  # Offset at start/base in local coordinates
        self._end_offsets = EndPointOffsets()    # Offset at end/top in local coordinates
        self.splice_location: Optional[float] = None  # Height of splice if any

        logger.debug(f"Created Column from {start_point} to {end_point} (h={self.height:.1f}mm)")

    @property
    def height(self) -> float:
        """Column height calculated dynamically from start and end points."""
        return self.start_point.distance_to(self.end_point)

    @height.setter
    def height(self, value: float):
        """
        Set height by adjusting end_point along column direction.

        Args:
            value: New height in mm (must be positive)

        Raises:
            ValueError: If height is not positive
        """
        if value <= 0:
            raise ValueError("Height must be positive")

        # Calculate direction from start to end
        current_direction = self.end_point - self.start_point
        length = current_direction.length()

        if length > 0:
            # Normalize and scale to new height
            direction = current_direction.normalize()
            self.end_point = self.start_point + direction * value
        else:
            # Degenerate case: default to vertical column
            self.end_point = Point3D(
                self.start_point.x,
                self.start_point.y,
                self.start_point.z + value
            )

        self.invalidate()

    @property
    def element_type(self) -> ElementType:
        return ElementType.COLUMN

    @property
    def base_point(self) -> Point3D:
        """Alias for start_point (legacy support)."""
        return self.start_point

    @base_point.setter
    def base_point(self, value: Point3D):
        self.start_point = value

    @property
    def top_point(self) -> Point3D:
        """Column top point."""
        return self.end_point

    @property
    def midpoint(self) -> Point3D:
        """Column midpoint."""
        return self.start_point.midpoint_to(self.end_point)

    @property
    def direction(self) -> Vector3D:
        """Column direction."""
        return (self.end_point - self.start_point).normalize()

    @property
    def start_offsets(self) -> EndPointOffsets:
        """Offset values at start/base point in local coordinates."""
        return self._start_offsets

    @start_offsets.setter
    def start_offsets(self, value: EndPointOffsets):
        self._start_offsets = value
        self.invalidate()

    @property
    def end_offsets(self) -> EndPointOffsets:
        """Offset values at end/top point in local coordinates."""
        return self._end_offsets

    @end_offsets.setter
    def end_offsets(self, value: EndPointOffsets):
        self._end_offsets = value
        self.invalidate()

    @property
    def base_offset(self) -> float:
        """Legacy property: Offset at base (mm) - maps to start_offsets.dx."""
        return self._start_offsets.dx

    @base_offset.setter
    def base_offset(self, value: float):
        self._start_offsets.dx = value
        self.invalidate()

    @property
    def top_offset(self) -> float:
        """Legacy property: Offset at top (mm) - maps to end_offsets.dx."""
        return self._end_offsets.dx

    @top_offset.setter
    def top_offset(self, value: float):
        self._end_offsets.dx = value
        self.invalidate()

    def get_local_coordinate_system(self, at_start: bool = True) -> LocalCoordinateSystem:
        """
        Get the local coordinate system at start or end point.

        The local coordinate system is defined as:
        - X-axis: Along element (from start to end, typically vertical for columns)
        - Y-axis: Perpendicular axis (typically along global X)
        - Z-axis: Right-hand perpendicular (completes right-hand system)

        Args:
            at_start: If True, origin is at start point; otherwise at end point

        Returns:
            LocalCoordinateSystem with origin, x_axis, y_axis, z_axis
        """
        # X-axis is along the column
        x_axis = self.direction
        world_x = Vector3D.unit_x()
        world_y = Vector3D.unit_y()

        # Calculate local Y axis
        if abs(x_axis.dot(world_x)) > 0.99:
            # Column direction is nearly parallel to X, use Y as reference
            y_axis = world_y.cross(x_axis).cross(x_axis).normalize()
        else:
            # Use world X to define local Y
            y_axis = x_axis.cross(world_x).cross(x_axis).normalize()

        # Z-axis completes the right-hand system
        z_axis = x_axis.cross(y_axis).normalize()

        # Apply rotation around column axis
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
        Get the actual start/base point after applying local offsets.

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
        Get the actual end/top point after applying local offsets.

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
        Swap the start and end points of the column.

        This also swaps the associated offsets.
        """
        # Swap points
        self.start_point, self.end_point = self.end_point, self.start_point

        # Swap offsets
        self._start_offsets, self._end_offsets = self._end_offsets, self._start_offsets

        self.invalidate()
        logger.debug(f"Swapped start/end for column {self._id}")

    @property
    def actual_height(self) -> float:
        """Actual height accounting for offsets along the column axis."""
        return self.height - self._start_offsets.dx - self._end_offsets.dx

    def generate_solid(self) -> Any:
        """
        Generate column solid by extruding profile along Z axis.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for column {self._id}")

            # Get actual start/end points with offsets applied
            actual_start = self.get_actual_start_point()
            actual_end = self.get_actual_end_point()
            actual_height = actual_start.distance_to(actual_end)

            if actual_height <= 0:
                logger.warning(f"Column {self._id} has non-positive height")
                return None

            # Create profile at base and extrude
            # Start workplane at actual start point
            wp = cq.Workplane("XY").workplane(offset=actual_start.z)

            # Move to actual start point XY
            wp = wp.center(actual_start.x, actual_start.y)

            # Create profile based on type
            if self._profile.profile_type.value == "I":
                # I-section - simplified as rectangle
                wp = wp.rect(self._profile.b, self._profile.h)
            elif self._profile.profile_type.value in ("SHS", "RHS"):
                wp = wp.rect(self._profile.b, self._profile.h)
            elif self._profile.profile_type.value in ("CHS", "CIRC"):
                wp = wp.circle(self._profile.d / 2)
            else:
                wp = wp.rect(self._profile.b or 200, self._profile.h or 200)

            # Apply rotation around column axis
            if self.rotation != 0:
                wp = wp.rotate((0, 0, 0), (0, 0, 1), self.rotation)

            # Extrude
            result = wp.extrude(actual_height)

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return self._create_simple_box()
        except Exception as e:
            logger.error(f"Failed to generate column solid: {e}")
            return self._create_simple_box()

    def _create_simple_box(self):
        """Create simple box as fallback geometry."""
        try:
            import cadquery as cq

            width = self._profile.b if self._profile and self._profile.b > 0 else 200
            depth = self._profile.h if self._profile and self._profile.h > 0 else 200

            box = (
                cq.Workplane("XY")
                .workplane(offset=self.base_point.z)
                .center(self.base_point.x, self.base_point.y)
                .box(width, depth, self.height)
            )
            return box.val().wrapped

        except Exception as e:
            logger.error(f"Failed to create fallback geometry: {e}")
            return None

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export column to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcColumn entity
        """
        from src.ifc.ifc_column import create_ifc_column
        return create_ifc_column(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get column-specific properties."""
        return {
            "Height": f"{self.height:.1f} mm",
            "Base Point": str(self.base_point),
            "Top Point": str(self.top_point),
            "Rotation": f"{self.rotation}deg",
            "Start Offset DX": f"{self._start_offsets.dx:.1f} mm",
            "Start Offset DY": f"{self._start_offsets.dy:.1f} mm",
            "Start Offset DZ": f"{self._start_offsets.dz:.1f} mm",
            "End Offset DX": f"{self._end_offsets.dx:.1f} mm",
            "End Offset DY": f"{self._end_offsets.dy:.1f} mm",
            "End Offset DZ": f"{self._end_offsets.dz:.1f} mm",
        }

    def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
        """
        Calculate geometry key for column based on height.

        Columns with the same height (within tolerance) are considered
        geometrically identical for Tekla-style numbering.

        Args:
            tolerance: Rounding tolerance in mm

        Returns:
            Geometry key string like "H4000"
        """
        rounded_height = round(self.height / tolerance) * tolerance
        return f"H{rounded_height:.0f}"

    def _get_rotation_key(self) -> Optional[int]:
        """
        Get rotation key for column signature.

        Columns with different rotations are considered different parts.

        Returns:
            Rotation in degrees (rounded) or None if rotation is essentially zero
        """
        return round(self.rotation)

    def set_property(self, name: str, value: Any) -> bool:
        """Set column property."""
        if super().set_property(name, value):
            return True

        if name == "Height":
            self.height = float(value)  # Setter handles invalidate()
            return True
        elif name == "Rotation":
            self.rotation = float(value)
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

    def extend_height(self, additional_height: float):
        """
        Extend column height.

        Args:
            additional_height: Height to add (can be negative)

        Raises:
            ValueError: If resulting height would be non-positive
        """
        new_height = self.height + additional_height
        if new_height <= 0:
            raise ValueError(f"Resulting height {new_height:.1f}mm must be positive")
        self.height = new_height  # Uses the setter which updates end_point

    def split_at_height(self, split_height: float) -> tuple:
        """
        Split column at given height.

        Args:
            split_height: Height from base to split at

        Returns:
            Tuple of two new Column objects
        """
        if split_height <= 0 or split_height >= self.height:
            raise ValueError(f"Split height must be between 0 and {self.height}")

        # Lower column
        split_point = Point3D(self.base_point.x, self.base_point.y, self.base_point.z + split_height)
        col1 = Column(
            self.base_point.copy(),
            split_point,
            self._profile,
            self._material,
            self.rotation
        )

        # Upper column
        col2 = Column(
            split_point.copy(),
            self.end_point.copy(),
            self._profile,
            self._material,
            self.rotation
        )

        return (col1, col2)

    def move(self, vector: Vector3D):
        """Move column by vector."""
        self.start_point = self.start_point + vector
        self.end_point = self.end_point + vector
        self.invalidate()

    def copy(self) -> "Column":
        """Create a copy of this column."""
        new_col = Column(
            self.start_point.copy(),
            self.end_point.copy(),
            self._profile,
            self._material,
            self.rotation,
            self._name
        )
        new_col._start_offsets = self._start_offsets.copy()
        new_col._end_offsets = self._end_offsets.copy()
        new_col.splice_location = self.splice_location
        return new_col

    def __repr__(self) -> str:
        return f"Column(id={self._id}, base={self.base_point}, h={self.height}, {self._profile.name if self._profile else 'no profile'})"
