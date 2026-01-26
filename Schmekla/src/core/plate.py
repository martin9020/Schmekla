"""
Plate structural element for Schmekla.

Represents a flat structural plate (base plate, gusset, stiffener, etc.).
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Plate(StructuralElement):
    """
    Structural plate element.

    A flat element defined by boundary points and thickness.
    """

    def __init__(
        self,
        points: List[Point3D],
        thickness: float,
        material: Material = None,
        name: str = "",
    ):
        """
        Create a plate.

        Args:
            points: List of boundary points defining plate outline (minimum 3)
            thickness: Plate thickness in mm
            material: Material
            name: Element name/mark
        """
        super().__init__()

        if len(points) != 4:
            raise ValueError(f"Plate must be defined by exactly 4 points (Start/End logic). Got {len(points)}")

        self.points = [p.copy() for p in points]
        self.thickness = thickness
        self._material = material or Material.default_steel()
        self._name = name

        # Plate-specific properties
        self.holes: List[dict] = []  # List of hole definitions
        self.normal = self._calculate_normal()

        logger.debug(f"Created Plate with {len(points)} points, thickness {thickness}mm")

    @property
    def element_type(self) -> ElementType:
        return ElementType.PLATE

    @property
    def centroid(self) -> Point3D:
        """Calculate plate centroid."""
        n = len(self.points)
        if n == 0:
            return Point3D.origin()

        cx = sum(p.x for p in self.points) / n
        cy = sum(p.y for p in self.points) / n
        cz = sum(p.z for p in self.points) / n
        return Point3D(cx, cy, cz)

    @property
    def area(self) -> float:
        """Calculate plate area (approximate for planar polygon)."""
        if len(self.points) < 3:
            return 0.0

        # Use shoelace formula for 2D projection
        # This is approximate for 3D polygons
        total = 0.0
        n = len(self.points)
        for i in range(n):
            j = (i + 1) % n
            total += self.points[i].x * self.points[j].y
            total -= self.points[j].x * self.points[i].y
        return abs(total) / 2.0

    def _calculate_normal(self) -> Vector3D:
        """Calculate plate normal vector from first 3 points."""
        if len(self.points) < 3:
            return Vector3D.unit_z()

        v1 = self.points[1] - self.points[0]
        v2 = self.points[2] - self.points[0]
        normal = v1.cross(v2)

        if normal.length < 1e-10:
            return Vector3D.unit_z()

        return normal.normalize()

    def generate_solid(self) -> Any:
        """
        Generate plate solid by extruding polygon.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for plate {self._id}")

            # Create 2D polygon and extrude
            # Convert 3D points to 2D workplane coordinates
            pts_2d = [(p.x, p.y) for p in self.points]

            # Create workplane at first point Z level
            base_z = self.points[0].z
            wp = cq.Workplane("XY").workplane(offset=base_z)

            # Create polygon
            wp = wp.moveTo(*pts_2d[0])
            for pt in pts_2d[1:]:
                wp = wp.lineTo(*pt)
            wp = wp.close()

            # Extrude by thickness
            result = wp.extrude(self.thickness)

            # Add holes if any
            for hole in self.holes:
                result = self._add_hole(result, hole)

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate plate solid: {e}")
            return None

    def _add_hole(self, solid, hole_def: dict):
        """Add a hole to the plate solid."""
        import cadquery as cq

        hole_type = hole_def.get("type", "circular")
        center = hole_def.get("center", (0, 0))
        base_z = self.points[0].z

        if hole_type == "circular":
            diameter = hole_def.get("diameter", 20)
            solid = (
                solid.faces(">Z").workplane()
                .center(center[0], center[1])
                .hole(diameter, self.thickness + 2)
            )
        elif hole_type == "rectangular":
            width = hole_def.get("width", 50)
            height = hole_def.get("height", 50)
            solid = (
                solid.faces(">Z").workplane()
                .center(center[0], center[1])
                .rect(width, height)
                .cutThruAll()
            )

        return solid

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export plate to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcPlate entity
        """
        from src.ifc.ifc_plate import create_ifc_plate
        return create_ifc_plate(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get plate-specific properties."""
        return {
            "Thickness": f"{self.thickness} mm",
            "Vertices": len(self.points),
            "Area": f"{self.area:.1f} mm2",
            "Centroid": str(self.centroid),
            "Holes": len(self.holes),
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set plate property."""
        if super().set_property(name, value):
            return True

        if name == "Thickness":
            self.thickness = float(value)
            self.invalidate()
            return True

        return False

    def add_circular_hole(self, center: Point3D, diameter: float):
        """
        Add a circular hole to the plate.

        Args:
            center: Hole center point
            diameter: Hole diameter in mm
        """
        self.holes.append({
            "type": "circular",
            "center": (center.x, center.y),
            "diameter": diameter
        })
        self.invalidate()

    def add_rectangular_hole(self, center: Point3D, width: float, height: float):
        """
        Add a rectangular hole to the plate.

        Args:
            center: Hole center point
            width: Hole width in mm
            height: Hole height in mm
        """
        self.holes.append({
            "type": "rectangular",
            "center": (center.x, center.y),
            "width": width,
            "height": height
        })
        self.invalidate()

    def move(self, vector: Vector3D):
        """Move plate by vector."""
        self.points = [p + vector for p in self.points]
        self.invalidate()

    def copy(self) -> "Plate":
        """Create a copy of this plate."""
        new_plate = Plate(
            [p.copy() for p in self.points],
            self.thickness,
            self._material,
            self._name
        )
        new_plate.holes = [h.copy() for h in self.holes]
        return new_plate

    @classmethod
    def create_rectangular(
        cls,
        origin: Point3D,
        width: float,
        length: float,
        thickness: float,
        material: Material = None,
        name: str = ""
    ) -> "Plate":
        """
        Create a rectangular plate.

        Args:
            origin: Corner point (minimum X, Y)
            width: Width in X direction (mm)
            length: Length in Y direction (mm)
            thickness: Plate thickness (mm)
            material: Material
            name: Element name

        Returns:
            New Plate instance
        """
        points = [
            origin,
            Point3D(origin.x + width, origin.y, origin.z),
            Point3D(origin.x + width, origin.y + length, origin.z),
            Point3D(origin.x, origin.y + length, origin.z),
        ]
        return cls(points, thickness, material, name)

    def __repr__(self) -> str:
        return f"Plate(id={self._id}, vertices={len(self.points)}, t={self.thickness}mm)"
