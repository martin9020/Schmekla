"""
Drawing manager for Schmekla.

Manages creation, deletion, and tracking of drawings.
"""
from typing import List, Dict, Optional, TYPE_CHECKING
from uuid import UUID
from loguru import logger
from datetime import datetime

from src.core.drawing import Drawing, DrawingType, DrawingStatus

if TYPE_CHECKING:
    from src.core.model import StructuralModel
    from src.core.element import StructuralElement

class DrawingManager:
    """
    Manages drawings in the model.
    """
    def __init__(self, model: "StructuralModel"):
        self.model = model
        self._drawings: Dict[UUID, Drawing] = {}
        
    def create_drawing(self, name: str, title: str, drawing_type: DrawingType, elements: List[UUID] = None) -> Drawing:
        """Create a new drawing."""
        drawing = Drawing(
            name=name,
            title=title,
            drawing_type=drawing_type,
            associated_element_ids=elements or []
        )
        self._drawings[drawing.id] = drawing
        logger.info(f"Created drawing: {drawing}")
        return drawing
        
    def delete_drawing(self, drawing_id: UUID):
        """Delete a drawing."""
        if drawing_id in self._drawings:
            del self._drawings[drawing_id]
            logger.info(f"Deleted drawing {drawing_id}")
            
    def get_drawing(self, drawing_id: UUID) -> Optional[Drawing]:
        """Get drawing by ID."""
        return self._drawings.get(drawing_id)
        
    def get_all_drawings(self) -> List[Drawing]:
        """Get all drawings."""
        return list(self._drawings.values())
        
    def get_drawings_by_type(self, drawing_type: DrawingType) -> List[Drawing]:
        """Get drawings of a specific type."""
        return [d for d in self._drawings.values() if d.drawing_type == drawing_type]

    def create_assembly_drawing(self, main_part_id: UUID) -> Optional[Drawing]:
        """Create an assembly drawing for a part."""
        element = self.model.get_element(main_part_id)
        if not element:
            logger.error(f"Element {main_part_id} not found")
            return None
            
        # Generate name (e.g. use part number)
        name = element.part_number if element.part_number else f"A-{str(element.id)[:4]}"
        title = f"Assembly - {element.name}"
        
        drawing = self.create_drawing(
            name=name,
            title=title,
            drawing_type=DrawingType.ASSEMBLY,
            elements=[main_part_id]
        )
        return drawing

    def create_ga_drawing(self, name: str, title: str) -> Drawing:
        """Create a General Arrangement drawing."""
        return self.create_drawing(
            name=name,
            title=title,
            drawing_type=DrawingType.GENERAL_ARRANGEMENT
        )
