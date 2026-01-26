"""
Column structural element for Schmekla.

Represents a vertical structural member (column, post, pier).
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

        # Derived property for legacy support
        self.height = start_point.distance_to(end_point)

        # Column-specific properties
        self.base_offset: float = 0.0      # Offset at base (mm)
        self.top_offset: float = 0.0       # Offset at top (mm)
        self.splice_location: Optional[float] = None  # Height of splice if any

        logger.debug(f"Created Column from {start_point} to {end_point} (h={self.height}mm)")

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
    def actual_height(self) -> float:
        """Actual height accounting for offsets."""
        return self.height - self.base_offset - self.top_offset

    @property
    def midpoint(self) -> Point3D:
        """Column midpoint."""
        return self.start_point.midpoint_to(self.end_point)

    @property
    def direction(self) -> Vector3D:
        """Column direction."""
        return (self.end_point - self.start_point).normalize()

    def generate_solid(self) -> Any:
        """
        Generate column solid by extruding profile along Z axis.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for column {self._id}")

            # Calculate actual base/top Z
            actual_base_z = self.base_point.z + self.base_offset
            actual_height = self.actual_height

            if actual_height <= 0:
                logger.warning(f"Column {self._id} has non-positive height")
                return None

            # Create profile at base and extrude
            # Start workplane at base point
            wp = cq.Workplane("XY").workplane(offset=actual_base_z)

            # Move to base point XY
            wp = wp.center(self.base_point.x, self.base_point.y)

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
            "Base Offset": f"{self.base_offset} mm",
            "Top Offset": f"{self.top_offset} mm",
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set column property."""
        if super().set_property(name, value):
            return True

        if name == "Height":
            self.height = float(value)
            self.invalidate()
            return True
        elif name == "Rotation":
            self.rotation = float(value)
            self.invalidate()
            return True
        elif name == "Base Offset":
            self.base_offset = float(value)
            self.invalidate()
            return True
        elif name == "Top Offset":
            self.top_offset = float(value)
            self.invalidate()
            return True

        return False

    def extend_height(self, additional_height: float):
        """
        Extend column height.

        Args:
            additional_height: Height to add (can be negative)
        """
        self.height += additional_height
        self.invalidate()

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
        new_col.base_offset = self.base_offset
        new_col.top_offset = self.top_offset
        new_col.splice_location = self.splice_location
        return new_col

    def __repr__(self) -> str:
        return f"Column(id={self._id}, base={self.base_point}, h={self.height}, {self._profile.name if self._profile else 'no profile'})"
