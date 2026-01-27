"""
Wall structural element for Schmekla.

Represents a vertical wall (shear wall, retaining wall, etc.).
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from loguru import logger

from src.core.element import StructuralElement, ElementType
from src.core.material import Material
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D

if TYPE_CHECKING:
    from src.ifc.exporter import IFCExporter


class Wall(StructuralElement):
    """
    Structural wall element.

    A vertical element defined by a baseline, height, and thickness.
    """

    def __init__(
        self,
        start_point: Point3D,
        end_point: Point3D,
        height: float,
        thickness: float,
        material: Material = None,
        name: str = "",
    ):
        """
        Create a wall.

        Args:
            start_point: Wall baseline start point
            end_point: Wall baseline end point
            height: Wall height in mm
            thickness: Wall thickness in mm
            material: Material (defaults to concrete)
            name: Element name/mark
        """
        super().__init__()

        self.start_point = start_point
        self.end_point = end_point
        self.height = height
        self.thickness = thickness
        self._material = material or Material.default_concrete()
        self._name = name

        # Wall-specific properties
        self.openings: List[dict] = []  # List of opening definitions (doors, windows)
        self.wall_type: str = "standard"  # standard, shear, retaining, partition
        self.base_offset: float = 0.0    # Offset from base point

        logger.debug(f"Created Wall from {start_point} to {end_point}, h={height}mm, t={thickness}mm")

    @property
    def element_type(self) -> ElementType:
        return ElementType.WALL

    @property
    def length(self) -> float:
        """Wall length along baseline."""
        return self.start_point.distance_to(self.end_point)

    @property
    def direction(self) -> Vector3D:
        """Wall direction vector along baseline."""
        return (self.end_point - self.start_point).normalize()

    @property
    def normal(self) -> Vector3D:
        """Wall normal vector (perpendicular to face)."""
        dir_vec = self.direction
        # Normal is perpendicular to direction in XY plane
        return Vector3D(-dir_vec.y, dir_vec.x, 0).normalize()

    @property
    def midpoint(self) -> Point3D:
        """Wall midpoint at mid-height."""
        mid_base = self.start_point.midpoint_to(self.end_point)
        return Point3D(mid_base.x, mid_base.y, mid_base.z + self.height / 2)

    @property
    def area(self) -> float:
        """Wall face area (excluding openings)."""
        gross_area = self.length * self.height
        opening_area = sum(
            o.get("width", 0) * o.get("height", 0)
            for o in self.openings
        )
        return gross_area - opening_area

    @property
    def volume(self) -> float:
        """Wall volume."""
        return self.area * self.thickness

    def generate_solid(self) -> Any:
        """
        Generate wall solid.

        Returns:
            OpenCascade TopoDS_Shape or CadQuery solid
        """
        try:
            import cadquery as cq

            logger.debug(f"Generating solid for wall {self._id}")

            # Create wall as extruded rectangle along baseline
            # First create a rectangle perpendicular to baseline
            half_t = self.thickness / 2

            # Calculate perpendicular direction
            dir_vec = self.direction
            perp = Vector3D(-dir_vec.y, dir_vec.x, 0)

            # Calculate corner points
            sp = self.start_point
            ep = self.end_point
            base_z = sp.z + self.base_offset

            # Four corners at base
            c1 = Point3D(sp.x + perp.x * half_t, sp.y + perp.y * half_t, base_z)
            c2 = Point3D(sp.x - perp.x * half_t, sp.y - perp.y * half_t, base_z)
            c3 = Point3D(ep.x - perp.x * half_t, ep.y - perp.y * half_t, base_z)
            c4 = Point3D(ep.x + perp.x * half_t, ep.y + perp.y * half_t, base_z)

            # Create workplane and polygon
            pts_2d = [(c1.x, c1.y), (c2.x, c2.y), (c3.x, c3.y), (c4.x, c4.y)]

            wp = cq.Workplane("XY").workplane(offset=base_z)
            wp = wp.moveTo(*pts_2d[0])
            for pt in pts_2d[1:]:
                wp = wp.lineTo(*pt)
            wp = wp.close()

            # Extrude upward
            result = wp.extrude(self.height)

            # Add openings
            for opening in self.openings:
                result = self._add_opening(result, opening)

            return result.val().wrapped

        except ImportError as e:
            logger.error(f"CadQuery/OCC not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate wall solid: {e}")
            return None

    def _add_opening(self, solid, opening_def: dict):
        """Add an opening (door/window) to the wall solid."""
        import cadquery as cq

        opening_type = opening_def.get("type", "rectangular")
        width = opening_def.get("width", 1000)
        height = opening_def.get("height", 2100)
        sill_height = opening_def.get("sill_height", 0)  # Height from wall base
        position = opening_def.get("position", 0.5)  # 0-1 along wall length

        # Calculate opening center position along wall
        distance_along = self.length * position
        dir_vec = self.direction

        opening_center = Point3D(
            self.start_point.x + dir_vec.x * distance_along,
            self.start_point.y + dir_vec.y * distance_along,
            self.start_point.z + self.base_offset + sill_height + height / 2
        )

        # Create cutting box
        try:
            # This is simplified - proper implementation would use faces
            solid = (
                solid.faces("<Y").workplane()
                .center(distance_along, sill_height + height/2)
                .rect(width, height)
                .cutThruAll()
            )
        except Exception as e:
            logger.warning(f"Could not add opening: {e}")

        return solid

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export wall to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IfcWall entity
        """
        from src.ifc.ifc_wall import create_ifc_wall
        return create_ifc_wall(self, exporter)

    def _get_specific_properties(self) -> Dict[str, Any]:
        """Get wall-specific properties."""
        return {
            "Length": f"{self.length:.1f} mm",
            "Height": f"{self.height} mm",
            "Thickness": f"{self.thickness} mm",
            "Start Point": str(self.start_point),
            "End Point": str(self.end_point),
            "Wall Type": self.wall_type,
            "Openings": len(self.openings),
        }

    def set_property(self, name: str, value: Any) -> bool:
        """Set wall property."""
        if super().set_property(name, value):
            return True

        if name == "Height":
            self.height = float(value)
            self.invalidate()
            return True
        elif name == "Thickness":
            self.thickness = float(value)
            self.invalidate()
            return True
        elif name == "Wall Type":
            self.wall_type = str(value)
            return True

        return False

    def add_door_opening(
        self,
        position: float,
        width: float = 900,
        height: float = 2100
    ):
        """
        Add a door opening to the wall.

        Args:
            position: Position along wall (0-1)
            width: Door width in mm
            height: Door height in mm
        """
        self.openings.append({
            "type": "door",
            "position": position,
            "width": width,
            "height": height,
            "sill_height": 0
        })
        self.invalidate()

    def add_window_opening(
        self,
        position: float,
        width: float = 1200,
        height: float = 1500,
        sill_height: float = 900
    ):
        """
        Add a window opening to the wall.

        Args:
            position: Position along wall (0-1)
            width: Window width in mm
            height: Window height in mm
            sill_height: Height from wall base to window sill in mm
        """
        self.openings.append({
            "type": "window",
            "position": position,
            "width": width,
            "height": height,
            "sill_height": sill_height
        })
        self.invalidate()

    def move(self, vector: Vector3D):
        """Move wall by vector."""
        self.start_point = self.start_point + vector
        self.end_point = self.end_point + vector
        self.invalidate()

    def copy(self) -> "Wall":
        """Create a copy of this wall."""
        new_wall = Wall(
            self.start_point.copy(),
            self.end_point.copy(),
            self.height,
            self.thickness,
            self._material,
            self._name
        )
        new_wall.openings = [o.copy() for o in self.openings]
        new_wall.wall_type = self.wall_type
        new_wall.base_offset = self.base_offset
        return new_wall

    def __repr__(self) -> str:
        return f"Wall(id={self._id}, L={self.length:.0f}mm, h={self.height}mm, t={self.thickness}mm)"
