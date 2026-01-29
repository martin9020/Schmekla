"""
Weld implementation.

Represents a weld connecting two parts.
Defines assembly hierarchy (Main Part vs Secondary Part).
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from enum import Enum

from src.core.element import ConnectionComponent, ElementType
from src.geometry.point import Point3D

class WeldType(Enum):
    FILLET = "Fillet"
    BUTT = "Butt"
    PLUG = "Plug"

@dataclass
class Weld(ConnectionComponent):
    """
    Represents a weld between two parts.
    Establishes the parent-child relationship for assemblies.
    """
    main_part_id: UUID = None
    secondary_part_id: UUID = None
    
    # Properties
    size_above: float = 6.0
    size_below: float = 0.0
    type_above: WeldType = WeldType.FILLET
    type_below: WeldType = WeldType.FILLET
    length: float = 0.0 # 0 means continuous
    
    # Position (approximate location for symbol)
    position: Point3D = field(default_factory=lambda: Point3D(0, 0, 0))
    
    def __post_init__(self):
        super().__init__()
        self._name = self._name or ""

    @property
    def element_type(self) -> ElementType:
        return ElementType.WELD

    def move(self, vector):
        self.position = Point3D(
            self.position.x + vector.x,
            self.position.y + vector.y,
            self.position.z + vector.z
        )

    def copy(self):
        return Weld(
            main_part_id=self.main_part_id,
            secondary_part_id=self.secondary_part_id,
            size_above=self.size_above,
            size_below=self.size_below,
            type_above=self.type_above,
            type_below=self.type_below,
            length=self.length,
            position=Point3D(self.position.x, self.position.y, self.position.z),
            **{}
        )

    def generate_solid(self):
        """
        Welds are usually not modeled as solids in detail, 
        but represented by a small marker or text.
        """
        return None

    def to_ifc(self, ifc_model):
        """Export to IfcFastener or specialized weld entity."""
        pass
