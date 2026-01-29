"""
Bolt Group implementation.

Represents a group of bolts connecting parts.
Mimics Tekla Structures BoltGroup.
"""
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import math

from src.core.element import StructuralElement, ElementType
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.geometry.transform import Transform
from src.core.material import Material
import cadquery as cq

@dataclass
class BoltGroup(StructuralElement):
    """
    Represents a group of bolts.
    Defined by an origin, direction, and spacing pattern.
    """
    origin: Point3D = field(default_factory=lambda: Point3D(0, 0, 0))
    direction_x: Vector3D = field(default_factory=lambda: Vector3D(1, 0, 0))
    direction_y: Vector3D = field(default_factory=lambda: Vector3D(0, 1, 0))
    
    # Properties
    bolt_diameter: float = 20.0
    bolt_standard: str = "8.8"
    hole_tolerance: float = 2.0
    
    # Spacing (Tekla style: "100 2*50 100")
    spacing_x: str = "100" 
    spacing_y: str = "0"
    
    # Connected parts
    part_to_bolt_to: Optional[UUID] = None # Primary part
    part_to_be_bolted: Optional[UUID] = None # Secondary part
    
    element_type_value: ElementType = ElementType.BOLT_GROUP
    
    def __post_init__(self):
        super().__init__()
        self._name = self._name or ""
        
    @property
    def hole_diameter(self) -> float:
        return self.bolt_diameter + self.hole_tolerance

    def get_bolt_positions(self) -> List[Point3D]:
        """Calculate global positions of individual bolts."""
        positions = []
        
        # Parse spacings
        dx_list = self._parse_spacing(self.spacing_x)
        dy_list = self._parse_spacing(self.spacing_y)
        
        # Determine start point (usually origin)
        # In Tekla, bolt group has an origin.
        
        current_x = 0.0
        x_coords = [0.0]
        for dx in dx_list:
            current_x += dx
            x_coords.append(current_x)
            
        current_y = 0.0
        y_coords = [0.0]
        for dy in dy_list:
            current_y += dy
            y_coords.append(current_y)
            
        # Create grid of points
        # Ensure vectors are normalized
        vx = self.direction_x.normalize()
        vy = self.direction_y.normalize()
        
        for x in x_coords:
            for y in y_coords:
                # P = O + x*Vx + y*Vy
                pos = Point3D(
                    self.origin.x + x * vx.x + y * vy.x,
                    self.origin.y + x * vx.y + y * vy.y,
                    self.origin.z + x * vx.z + y * vy.z
                )
                positions.append(pos)
                
        return positions

    def _parse_spacing(self, spacing_str: str) -> List[float]:
        """Parse Tekla-style spacing string (e.g., '100 2*50')."""
        spacings = []
        if not spacing_str:
            return []
            
        parts = spacing_str.split()
        for part in parts:
            if '*' in part:
                try:
                    count_str, val_str = part.split('*')
                    count = int(count_str)
                    val = float(val_str)
                    spacings.extend([val] * count)
                except ValueError:
                    pass
            else:
                try:
                    spacings.append(float(part))
                except ValueError:
                    pass
        return spacings

    def generate_solid(self):
        """Generate geometry for the bolts."""
        # For visualization, we create cylinders for each bolt
        positions = self.get_bolt_positions()
        if not positions:
            return None
            
        # We need a length for the bolts. 
        # Typically determined by part thickness, but for now fixed or estimated.
        length = 100.0 # Placeholder
        
        # Create one bolt cylinder and copy it
        # Direction of bolt is usually Z (normal to XY plane of bolt group)
        vz = self.direction_x.cross(self.direction_y).normalize()
        
        solids = []
        for pos in positions:
            # Create cylinder centered at pos, oriented along vz
            # CadQuery cylinder is created at origin along Z.
            
            # Start point should be slightly offset to center the grip
            start = Point3D(
                pos.x - vz.x * (length/2),
                pos.y - vz.y * (length/2),
                pos.z - vz.z * (length/2)
            )
            
            # Create cylinder from start to end
            end = Point3D(
                pos.x + vz.x * (length/2),
                pos.y + vz.y * (length/2),
                pos.z + vz.z * (length/2)
            )
            
            # Use CadQuery
            # Workplane logic might be needed
            # Simple approach: Create at origin, rotate/translate
            
            # Or use makeCylinder from Workplane
            # solid = cq.Workplane("XY").cylinder(length, self.bolt_diameter/2)
            # Transform...
            
            # Let's use a simpler representation for now if strictly needed for specific CAD kernel
            # Assuming we can return a list of shapes or a compound
            pass
            
        # Returning None for now as actual implementation depends on how Model handles compounds
        # We might need to override get_mesh instead
        return None

    @property
    def element_type(self) -> ElementType:
        return ElementType.BOLT_GROUP

    def move(self, vector: Vector3D):
        self.origin = Point3D(
            self.origin.x + vector.x,
            self.origin.y + vector.y,
            self.origin.z + vector.z
        )

    def copy(self) -> "BoltGroup":
        return BoltGroup(
            origin=Point3D(self.origin.x, self.origin.y, self.origin.z),
            direction_x=Vector3D(self.direction_x.x, self.direction_x.y, self.direction_x.z),
            direction_y=Vector3D(self.direction_y.x, self.direction_y.y, self.direction_y.z),
            bolt_diameter=self.bolt_diameter,
            bolt_standard=self.bolt_standard,
            hole_tolerance=self.hole_tolerance,
            spacing_x=self.spacing_x,
            spacing_y=self.spacing_y,
            part_to_bolt_to=self.part_to_bolt_to,
            part_to_be_bolted=self.part_to_be_bolted
        )

    def to_ifc(self, ifc_model):
        """Export to IfcMechanicalFastener."""
        # TODO: Implement IFC export
        pass
