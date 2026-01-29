"""
Grid system implementation for Schmekla.
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from loguru import logger

from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.geometry.plane import Plane
from src.core.element import StructuralElement, ElementType


@dataclass
class GridLine:
    """Represents a single grid line."""
    name: str
    position: float  # Distance from origin
    
    def __repr__(self):
        return f"GridLine({self.name} @ {self.position})"


class GridSystem(StructuralElement):
    """
    Rectangular grid system defined by X and Y grid lines.
    
    The grid system has a local coordinate system defined by origin and rotation.
    X-grids are lines perpendicular to X-axis (running along Y).
    Y-grids are lines perpendicular to Y-axis (running along X).
    """
    
    def __init__(
        self,
        name: str = "Grid",
        origin: Point3D = None,
        rotation: float = 0.0,
    ):
        super().__init__()
        self.name = name
        self.origin = origin or Point3D(0, 0, 0)
        self.rotation = rotation  # Rotation around Z axis in degrees
        
        self.x_grids: List[GridLine] = []
        self.y_grids: List[GridLine] = []
        self.z_levels: List[GridLine] = []
        
        # Display settings
        self.extension_length = 2000.0  # How far grid extends past intersections
        self.bubble_radius = 500.0
        
    @property
    def element_type(self) -> ElementType:
        return ElementType.GRID

    def add_x_grid(self, name: str, position: float):
        """Add a grid line perpendicular to X axis (vertical on plan)."""
        self.x_grids.append(GridLine(name, position))
        self.x_grids.sort(key=lambda g: g.position)
        self.invalidate()

    def add_y_grid(self, name: str, position: float):
        """Add a grid line perpendicular to Y axis (horizontal on plan)."""
        self.y_grids.append(GridLine(name, position))
        self.y_grids.sort(key=lambda g: g.position)
        self.invalidate()

    def add_z_level(self, name: str, elevation: float):
        """Add a level (Z plane)."""
        self.z_levels.append(GridLine(name, elevation))
        self.z_levels.sort(key=lambda g: g.position)
        self.invalidate()
        
    def clear(self):
        """Clear all grid lines."""
        self.x_grids.clear()
        self.y_grids.clear()
        self.z_levels.clear()
        self.invalidate()
        
    def generate_solid(self) -> Any:
        """
        Generate a visual representation of the grid.
        For grids, we don't usually generate a solid volume, but a set of lines/curves.
        However, to satisfy the StructuralElement contract, we might return a compound.
        """
        # For now, we'll return None or a dummy solid. 
        # The actual visualization is usually done via custom rendering in the viewport
        # using the grid data, not by meshing a solid.
        # But if we want it to appear in IFC or generic 3D view, we can make thin cylinders.
        
        try:
            import cadquery as cq
            
            # Create a compound of lines
            lines = []
            
            # Determine bounds
            if not self.x_grids or not self.y_grids:
                return None
                
            min_x = self.x_grids[0].position - self.extension_length
            max_x = self.x_grids[-1].position + self.extension_length
            min_y = self.y_grids[0].position - self.extension_length
            max_y = self.y_grids[-1].position + self.extension_length
            
            z = self.origin.z
            
            # Create X-grids (lines along Y, at specific X)
            for x_grid in self.x_grids:
                start = Point3D(x_grid.position, min_y, z)
                end = Point3D(x_grid.position, max_y, z)
                
                # Apply rotation/origin transform
                # TODO: Implement transform logic
                
                # Make line (using thin cylinder for visibility)
                line = cq.Workplane("XY").center(x_grid.position, (min_y + max_y)/2).box(50, max_y - min_y, 50)
                lines.append(line)
                
            # Create Y-grids (lines along X, at specific Y)
            for y_grid in self.y_grids:
                line = cq.Workplane("XY").center((min_x + max_x)/2, y_grid.position).box(max_x - min_x, 50, 50)
                lines.append(line)
                
            if not lines:
                return None
                
            # Combine
            result = lines[0]
            for l in lines[1:]:
                result = result.union(l)
                
            return result.val().wrapped
            
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Error generating grid solid: {e}")
            return None

    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """Export grid to IFC."""
        try:
            from src.ifc.ifc_grid import create_ifc_grid
            return create_ifc_grid(self, exporter)
        except ImportError:
            logger.error("Failed to import create_ifc_grid")
            return None
        
    def get_intersections(self) -> List[Tuple[str, Point3D]]:
        """Get all grid intersection points with names (e.g. 'A-1')."""
        intersections = []
        for xg in self.x_grids:
            for yg in self.y_grids:
                name = f"{xg.name}-{yg.name}"
                pt = Point3D(xg.position, yg.position, self.origin.z)
                # TODO: Apply rotation
                intersections.append((name, pt))
        return intersections

