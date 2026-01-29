"""
Drawing representation for Schmekla.

Represents a 2D drawing of the structural model or parts of it.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime

class DrawingType(Enum):
    GENERAL_ARRANGEMENT = "GA"
    ASSEMBLY = "Assembly"
    SINGLE_PART = "SinglePart"
    CAST_UNIT = "CastUnit"
    MULTIDRAWING = "MultiDrawing"

class DrawingStatus(Enum):
    UP_TO_DATE = "Up to date"
    MODIFIED = "Modified"
    LOCKED = "Locked"
    FROZEN = "Frozen"
    ISSUED = "Issued"

@dataclass
class Drawing:
    """
    Represents a 2D drawing.
    """
    name: str  # Drawing number/mark (e.g. "A.1", "B.100")
    title: str # Descriptive title (e.g. "Plan at +3000")
    drawing_type: DrawingType
    
    id: UUID = field(default_factory=uuid4)
    creation_date: datetime = field(default_factory=datetime.now)
    modification_date: datetime = field(default_factory=datetime.now)
    status: DrawingStatus = DrawingStatus.UP_TO_DATE
    
    # Elements associated with this drawing
    # For Assembly drawing: the main part ID
    # For GA: list of visible elements (or empty if view-based)
    associated_element_ids: List[UUID] = field(default_factory=list)
    
    # Metadata/User properties
    user_properties: Dict[str, Any] = field(default_factory=dict)
    
    def mark_as_modified(self):
        """Mark drawing as modified (needs update)."""
        if self.status != DrawingStatus.LOCKED and self.status != DrawingStatus.FROZEN:
            self.status = DrawingStatus.MODIFIED
            self.modification_date = datetime.now()
            
    def update_status(self, new_status: DrawingStatus):
        """Update drawing status."""
        self.status = new_status
        self.modification_date = datetime.now()

    def __str__(self):
        return f"{self.name} - {self.title} ({self.drawing_type.value})"
