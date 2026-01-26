"""
Slab structural element for Schmekla.

Represents a horizontal floor or roof slab.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Slab(StructuralElement):
    """
    Structural slab element.

    A horizontal element defined by boundary points and thickness.
    Typically used for floors, roofs, or foundation mats.
    """

    def __init__(
        self,
        points: List[Point3D],
        thickness: float,
        material: Material = None,
        name: str = "",
    ):
        """
        Create a slab.

        Args:
            points: List of boundary points defining slab outline (minimum 3)
            thickness: Slab thickness in mm
            material: Material (defaults to concrete)
            name: Element name/mark
        """
        super().__init__()

        if len(points) < 3:
            raise ValueError("Slab requires at least 3 points")

        self.points = [p.copy() for p in points]
        self.thickness = thickness
        self._material = material or Material.default_concrete()
        self._name = name

        # Slab-specific properties
        self.openings: List[dict] = []  # List of opening definitions
        self.level_name: str = ""       # Associated level name
        self.slab_type: str = "floor"   # floor, roof, landing, mat

        logger.debug(f"Created Slab with {len(points)} points, thickness {thickness}mm")

    @property
    def element_type(self) -> ElementType:
        return ElementType.SLAB

    @property
    def elevation(self) -> float:
        """Slab top elevation (Z coordinate)."""
        if self.points:
            return self.points[0].z
        return 0.0

    @property
    def centroid(self) -> Point3D:
        """Calculate slab centroid."""
        n = len(self.points)
        if n == 0:
            return Point3D.origin()

        cx = sum(p.x for p in self.points) / n
        cy = sum(p.y for p in self.points) / n
        cz = sum(p.z for p in self.points) / n
        return Point3D(cx, cy, cz)

    @property
    def area(self) -> float:
        """Calculate slab area using shoelace formula."""
        if len(self.points) < 3:
            return 0.0

        total = 0.0
        n = len(self.points)
        for i in range(n):
            j = (i + 1) % n
            total += self.points[i].x * self.points[j].y
            total -= self.points[j].x * self.points[i].y
        return abs(total) / 2.0

    @property
    def volume(self) -> float:
        """Calculate slab volume."""
        return self.area * self.thickness

    def generate_solid(self) -> Any:
        """
        Generate slab solid by extruding polygon downward.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for slab {self._id}")

            # Create 2D polygon and extrude downward
            pts_2d = [(p.x, p.y) for p in self.points]

            # Create workplane at slab top
            top_z = self.elevation
            wp = cq.Workplane("XY").workplane(offset=top_z)

            # Create polygon
            wp = wp.moveTo(*pts_2d[0])
            for pt in pts_2d[1:]:
                wp = wp.lineTo(*pt)
            wp = wp.close()

            # Extrude downward (negative Z)
            result = wp.extrude(-self.thickness)

            # Add openings
            for opening in self.openings:
                result = self._add_opening(result, opening)

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate slab solid: {e}")
            return None

    def _add_opening(self, solid, opening_def: dict):
        """Add an opening (void) to the slab solid."""
        import cadquery as cq

        opening_type = opening_def.get("type", "rectangular")
        points = opening_def.get("points", [])

        if opening_type == "rectangular" and len(points) >= 2:
            # Two points define corners
            p1, p2 = points[0], points[1]
            width = abs(p2[0] - p1[0])
            length = abs(p2[1] - p1[1])
            center_x = (p1[0] + p2[0]) / 2
            center_y = (p1[1] + p2[1]) / 2

            solid = (
                solid.faces(">Z").workplane()
                .center(center_x, center_y)
                .rect(width, length)
                .cutThruAll()
            )
        elif opening_type == "circular":
            center = opening_def.get("center", (0, 0))
            diameter = opening_def.get("diameter", 500)
            solid = (
                solid.faces(">Z").workplane()
                .center(center[0], center[1])
                .hole(diameter, self.thickness + 2)
            )

        return solid

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export slab to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcSlab entity
        """
        from src.ifc.ifc_slab import create_ifc_slab
        return create_ifc_slab(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get slab-specific properties."""
        return {
            "Thickness": f"{self.thickness} mm",
            "Elevation": f"{self.elevation} mm",
            "Area": f"{self.area:.1f} mm2",
            "Volume": f"{self.volume:.1f} mm3",
            "Slab Type": self.slab_type,
            "Openings": len(self.openings),
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set slab property."""
        if super().set_property(name, value):
            return True

        if name == "Thickness":
            self.thickness = float(value)
            self.invalidate()
            return True
        elif name == "Slab Type":
            self.slab_type = str(value)
            return True

        return False

    def add_rectangular_opening(self, corner1: Point3D, corner2: Point3D):
        """
        Add a rectangular opening to the slab.

        Args:
            corner1: First corner point
            corner2: Opposite corner point
        """
        self.openings.append({
            "type": "rectangular",
            "points": [(corner1.x, corner1.y), (corner2.x, corner2.y)]
        })
        self.invalidate()

    def add_circular_opening(self, center: Point3D, diameter: float):
        """
        Add a circular opening to the slab.

        Args:
            center: Opening center point
            diameter: Opening diameter in mm
        """
        self.openings.append({
            "type": "circular",
            "center": (center.x, center.y),
            "diameter": diameter
        })
        self.invalidate()

    def move(self, vector: Vector3D):
        """Move slab by vector."""
        self.points = [p + vector for p in self.points]
        self.invalidate()

    def copy(self) -> "Slab":
        """Create a copy of this slab."""
        new_slab = Slab(
            [p.copy() for p in self.points],
            self.thickness,
            self._material,
            self._name
        )
        new_slab.openings = [o.copy() for o in self.openings]
        new_slab.level_name = self.level_name
        new_slab.slab_type = self.slab_type
        return new_slab

    @classmethod
    def create_rectangular(
        cls,
        origin: Point3D,
        width: float,
        length: float,
        thickness: float,
        material: Material = None,
        name: str = ""
    ) -> "Slab":
        """
        Create a rectangular slab.

        Args:
            origin: Corner point (minimum X, Y) at top of slab
            width: Width in X direction (mm)
            length: Length in Y direction (mm)
            thickness: Slab thickness (mm)
            material: Material
            name: Element name

        Returns:
            New Slab instance
        """
        points = [
            origin,
            Point3D(origin.x + width, origin.y, origin.z),
            Point3D(origin.x + width, origin.y + length, origin.z),
            Point3D(origin.x, origin.y + length, origin.z),
        ]
        return cls(points, thickness, material, name)

    def __repr__(self) -> str:
        return f"Slab(id={self._id}, vertices={len(self.points)}, t={self.thickness}mm, type={self.slab_type})"
