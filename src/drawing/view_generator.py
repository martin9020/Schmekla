"""
Drawing View Generator.

Generates 2D view representations from 3D model elements.
"""
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import math

from src.core.element import StructuralElement, ElementType
from src.core.beam import Beam
from src.core.column import Column
from src.core.plate import Plate
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.geometry.plane import Plane
from src.geometry.transform import Transform

@dataclass
class DrawingLine:
    """Represents a 2D line on the drawing."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    line_type: str = "Solid" # Solid, Dashed, Center
    
@dataclass
class DrawingDimension:
    """Represents a linear dimension."""
    p1_x: float
    p1_y: float
    p2_x: float
    p2_y: float
    offset: float # Distance from line p1-p2
    text: str
    
@dataclass
class DrawingView:
    """Container for 2D view data."""
    lines: List[DrawingLine]
    dimensions: List[DrawingDimension]
    bounds: Tuple[float, float, float, float] # min_x, min_y, max_x, max_y

class ViewGenerator:
    """Generates 2D views from elements."""
    
    @staticmethod
    def generate_assembly_view(element: StructuralElement, view_type: str = "Front") -> DrawingView:
        """
        Generate 2D view for an element.
        
        Args:
            element: Structural element
            view_type: "Front", "Top", "Side"
        """
        if element.element_type == ElementType.BEAM:
            return ViewGenerator._generate_beam_view(element, view_type)
        elif element.element_type == ElementType.COLUMN:
            # Re-use beam logic but maybe rotated
             return ViewGenerator._generate_beam_view(element, view_type) # Simplified for now
        
        # Default empty view
        return DrawingView([], [], (0, 0, 0, 0))

    @staticmethod
    def _generate_beam_view(beam: Beam, view_type: str) -> DrawingView:
        """Generate view for a beam."""
        lines = []
        dimensions = []
        
        # Get local coordinate system logic
        # For simplicity, we assume beam is defined by start/end points
        # We transform these points to a local system where start is (0,0,0) and end is (L,0,0)
        
        length = beam.length
        
        # Dimensions based on profile
        width = 100.0
        height = 200.0
        if beam.profile:
            width = beam.profile.b
            height = beam.profile.h
            
        # Define 2D box based on view type
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        
        if view_type == "Front":
            # Length x Height
            # Rectangle (0, -h/2) to (L, h/2) assuming center alignment
            # Let's assume Top-Left origin for drawing system usually, 
            # but standard engineering is bottom-left. Let's use Cartesian.
            
            x1, y1 = 0, 0
            x2, y2 = length, height
            
            # Main outline
            lines.append(DrawingLine(x1, y1, x2, y1)) # Bottom
            lines.append(DrawingLine(x2, y1, x2, y2)) # Right
            lines.append(DrawingLine(x2, y2, x1, y2)) # Top
            lines.append(DrawingLine(x1, y2, x1, y1)) # Left
            
            # Dimensions
            dimensions.append(DrawingDimension(x1, y1, x2, y1, -50, f"{length:.1f}")) # Length below
            dimensions.append(DrawingDimension(x1, y1, x1, y2, -50, f"{height:.1f}")) # Height left
            
            min_x, min_y, max_x, max_y = 0, 0, length, height
            
        elif view_type == "Top":
            # Length x Width
            x1, y1 = 0, 0
            x2, y2 = length, width
            
            lines.append(DrawingLine(x1, y1, x2, y1))
            lines.append(DrawingLine(x2, y1, x2, y2))
            lines.append(DrawingLine(x2, y2, x1, y2))
            lines.append(DrawingLine(x1, y2, x1, y1))
            
            # Center line
            lines.append(DrawingLine(x1, width/2, x2, width/2, "Center"))
            
            dimensions.append(DrawingDimension(x1, y1, x2, y1, -50, f"{length:.1f}"))
            dimensions.append(DrawingDimension(x1, y1, x1, y2, -50, f"{width:.1f}"))
            
            min_x, min_y, max_x, max_y = 0, 0, length, width
            
        return DrawingView(lines, dimensions, (min_x, min_y, max_x, max_y))
