"""
Footing structural element for Schmekla.

Represents foundation elements (pad footings, strip footings, etc.).
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Footing(StructuralElement):
    """
    Structural footing element.

    Foundation element defined by plan dimensions and depth.
    Supports both pad (isolated) and strip (continuous) footings.
    """

    def __init__(
        self,
        center_point: Point3D,
        width: float,
        length: float,
        depth: float,
        material: Material = None,
        name: str = "",
    ):
        """
        Create a footing.

        Args:
            center_point: Footing center point (at top of footing)
            width: Footing width in X direction (mm)
            length: Footing length in Y direction (mm)
            depth: Footing depth/thickness (mm)
            material: Material (defaults to concrete)
            name: Element name/mark
        """
        super().__init__()

        self.center_point = center_point
        self.width = width
        self.length = length
        self.depth = depth
        self._material = material or Material.default_concrete()
        self._name = name

        # Footing-specific properties
        self.footing_type: str = "pad"  # pad, strip, mat, pile_cap
        self.pedestal_width: float = 0   # Width of pedestal/pier if any
        self.pedestal_height: float = 0  # Height of pedestal/pier if any
        self.rotation: float = 0.0       # Rotation around Z axis (degrees)

        logger.debug(f"Created Footing at {center_point}, {width}x{length}x{depth}mm")

    @property
    def element_type(self) -> ElementType:
        return ElementType.FOOTING

    @property
    def top_elevation(self) -> float:
        """Top of footing elevation."""
        return self.center_point.z

    @property
    def bottom_elevation(self) -> float:
        """Bottom of footing elevation."""
        return self.center_point.z - self.depth

    @property
    def area(self) -> float:
        """Footing plan area."""
        return self.width * self.length

    @property
    def volume(self) -> float:
        """Footing volume."""
        return self.area * self.depth

    @property
    def corner_points(self) -> List[Point3D]:
        """Get footing corner points at top."""
        half_w = self.width / 2
        half_l = self.length / 2
        z = self.center_point.z
        cx, cy = self.center_point.x, self.center_point.y

        corners = [
            Point3D(cx - half_w, cy - half_l, z),
            Point3D(cx + half_w, cy - half_l, z),
            Point3D(cx + half_w, cy + half_l, z),
            Point3D(cx - half_w, cy + half_l, z),
        ]

        # Apply rotation if any
        if self.rotation != 0:
            corners = [c.rotate_around_z(self.rotation, self.center_point) for c in corners]

        return corners

    def generate_solid(self) -> Any:
        """
        Generate footing solid.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for footing {self._id}")

            cp = self.center_point

            # Create footing as box
            wp = cq.Workplane("XY").workplane(offset=cp.z)
            wp = wp.center(cp.x, cp.y)

            # Apply rotation
            if self.rotation != 0:
                wp = wp.transformed(rotate=(0, 0, self.rotation))

            # Create main footing body
            result = wp.rect(self.width, self.length).extrude(-self.depth)

            # Add pedestal if specified
            if self.pedestal_width > 0 and self.pedestal_height > 0:
                ped_size = self.pedestal_width
                result = (
                    result.faces(">Z").workplane()
                    .center(0, 0)
                    .rect(ped_size, ped_size)
                    .extrude(self.pedestal_height)
                )

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate footing solid: {e}")
            return None

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export footing to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcFooting entity
        """
        from src.ifc.ifc_footing import create_ifc_footing
        return create_ifc_footing(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get footing-specific properties."""
        return {
            "Width": f"{self.width} mm",
            "Length": f"{self.length} mm",
            "Depth": f"{self.depth} mm",
            "Center Point": str(self.center_point),
            "Top Elevation": f"{self.top_elevation} mm",
            "Bottom Elevation": f"{self.bottom_elevation} mm",
            "Footing Type": self.footing_type,
            "Area": f"{self.area:.1f} mm2",
            "Volume": f"{self.volume:.1f} mm3",
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set footing property."""
        if super().set_property(name, value):
            return True

        if name == "Width":
            self.width = float(value)
            self.invalidate()
            return True
        elif name == "Length":
            self.length = float(value)
            self.invalidate()
            return True
        elif name == "Depth":
            self.depth = float(value)
            self.invalidate()
            return True
        elif name == "Footing Type":
            self.footing_type = str(value)
            return True

        return False

    def add_pedestal(self, width: float, height: float):
        """
        Add a pedestal/pier on top of the footing.

        Args:
            width: Pedestal width (square)
            height: Pedestal height
        """
        self.pedestal_width = width
        self.pedestal_height = height
        self.invalidate()

    def move(self, vector: Vector3D):
        """Move footing by vector."""
        self.center_point = self.center_point + vector
        self.invalidate()

    def copy(self) -> "Footing":
        """Create a copy of this footing."""
        new_footing = Footing(
            self.center_point.copy(),
            self.width,
            self.length,
            self.depth,
            self._material,
            self._name
        )
        new_footing.footing_type = self.footing_type
        new_footing.pedestal_width = self.pedestal_width
        new_footing.pedestal_height = self.pedestal_height
        new_footing.rotation = self.rotation
        return new_footing

    @classmethod
    def create_pad_footing(
        cls,
        center: Point3D,
        size: float,
        depth: float,
        material: Material = None,
        name: str = ""
    ) -> "Footing":
        """
        Create a square pad footing.

        Args:
            center: Footing center point
            size: Footing size (width = length)
            depth: Footing depth
            material: Material
            name: Element name

        Returns:
            New Footing instance
        """
        footing = cls(center, size, size, depth, material, name)
        footing.footing_type = "pad"
        return footing

    @classmethod
    def create_strip_footing(
        cls,
        start_point: Point3D,
        end_point: Point3D,
        width: float,
        depth: float,
        material: Material = None,
        name: str = ""
    ) -> "Footing":
        """
        Create a strip (continuous) footing.

        Args:
            start_point: Strip footing start
            end_point: Strip footing end
            width: Footing width (perpendicular to length)
            depth: Footing depth
            material: Material
            name: Element name

        Returns:
            New Footing instance
        """
        # Calculate center and length
        center = start_point.midpoint_to(end_point)
        length = start_point.distance_to(end_point)

        footing = cls(center, width, length, depth, material, name)
        footing.footing_type = "strip"

        # Calculate rotation to align with start-end direction
        import math
        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        footing.rotation = math.degrees(math.atan2(dy, dx))

        return footing

    def __repr__(self) -> str:
        return f"Footing(id={self._id}, {self.width}x{self.length}x{self.depth}mm, type={self.footing_type})"
