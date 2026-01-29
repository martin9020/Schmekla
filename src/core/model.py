"""
Structural model (document) class for Schmekla.

The main container for all structural elements in a project.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from uuid import UUID
from pathlib import Path
import json
from loguru import logger

from PySide6.QtCore import QObject, Signal

from src.core.element import StructuralElement, ElementType
from src.core.numbering import NumberingManager
from src.core.grid import GridSystem
from src.core.level import Level
from src.core.drawing_manager import DrawingManager


class StructuralModel(QObject):
    """
    Main model document containing all structural elements.

    Provides signals for UI updates and undo/redo support.
    """

    # Signals for UI updates
    element_added = Signal(object)      # Emitted when element added
    element_removed = Signal(object)    # Emitted when element removed
    element_modified = Signal(object)   # Emitted when element modified
    model_changed = Signal()            # Emitted on any change
    selection_changed = Signal(list)    # Emitted when selection changes

    def __init__(self, parent=None):
        super().__init__(parent)

        # Model metadata
        self.name: str = "Untitled"
        self.file_path: Optional[Path] = None
        self.author: str = ""
        self.description: str = ""

        # Elements storage
        self._elements: Dict[UUID, StructuralElement] = {}

        # Grids and levels
        self._grids: List[GridSystem] = []
        self._levels: List[Level] = []

        # Selection
        self._selected_ids: List[UUID] = []

        # Undo/redo stacks
        self._undo_stack: List["Command"] = []
        self._redo_stack: List["Command"] = []
        self._max_undo: int = 100

        # Modification tracking
        self._modified: bool = False

        # Numbering manager for automatic part numbers
        self.numbering = NumberingManager()
        
        # Drawing manager
        self.drawing_manager = DrawingManager(self)

        logger.info(f"Created new StructuralModel: {self.name}")

    @property
    def is_modified(self) -> bool:
        """Check if model has unsaved changes."""
        return self._modified

    @property
    def element_count(self) -> int:
        """Get total number of elements."""
        return len(self._elements)

    # Element management
    def add_element(self, element: StructuralElement) -> UUID:
        """
        Add element to model.

        Uses Tekla-style identical parts detection: elements with matching
        signatures (profile, material, geometry) receive the same part number.

        Args:
            element: Element to add

        Returns:
            Element UUID
        """
        # Auto-assign part number using identical parts detection
        # Skip numbering for system elements (Grids, Levels, Welds, Bolts)
        if element.element_type not in [ElementType.GRID, ElementType.LEVEL, ElementType.WELD, ElementType.BOLT_GROUP]:
            if not hasattr(element, 'part_number') or not element.part_number:
                if hasattr(self.numbering, 'get_number_for_element'):
                    element.part_number = self.numbering.get_number_for_element(element)

        self._elements[element.id] = element
        self._modified = True

        hook = getattr(element, "on_added", None)
        if callable(hook):
            try:
                hook(self)
            except Exception as e:
                logger.warning(f"on_added hook failed for {element}: {e}")

        logger.debug(f"Added element: {element}")

        self.element_added.emit(element)
        self.model_changed.emit()

        return element.id

    def remove_element(self, element_id: UUID) -> bool:
        """
        Remove element from model.

        Args:
            element_id: UUID of element to remove

        Returns:
            True if element was removed
        """
        if element_id not in self._elements:
            logger.warning(f"Element not found: {element_id}")
            return False

        element = self._elements.pop(element_id)
        self._modified = True

        # Remove from selection if selected
        if element_id in self._selected_ids:
            self._selected_ids.remove(element_id)

        logger.debug(f"Removed element: {element}")

        self.element_removed.emit(element)
        self.model_changed.emit()

        return True

    def get_element(self, element_id: UUID) -> Optional[StructuralElement]:
        """Get element by ID."""
        return self._elements.get(element_id)

    def get_elements_by_type(self, element_type: ElementType) -> List[StructuralElement]:
        """Get all elements of specific type."""
        return [e for e in self._elements.values() if e.element_type == element_type]

    def get_all_elements(self) -> List[StructuralElement]:
        """Get all elements."""
        return list(self._elements.values())

    def get_element_ids(self) -> List[UUID]:
        """Get all element IDs."""
        return list(self._elements.keys())

    def get_bounding_box(self):
        """
        Get the combined bounding box of all elements in the model.

        Returns:
            Tuple of (min_point, max_point) as Point3D
        """
        from src.geometry.point import Point3D

        if not self._elements:
            return (Point3D.origin(), Point3D(10000, 10000, 10000))

        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        has_valid = False

        for element in self._elements.values():
            try:
                el_min, el_max = element.get_bounding_box()
                if el_min.x == 0 and el_min.y == 0 and el_min.z == 0 and \
                   el_max.x == 0 and el_max.y == 0 and el_max.z == 0:
                    # Skip elements that returned origin (no valid bbox)
                    # Fall back to element positions if available
                    if hasattr(element, 'start_point') and hasattr(element, 'end_point'):
                        for pt in [element.start_point, element.end_point]:
                            min_x = min(min_x, pt.x)
                            min_y = min(min_y, pt.y)
                            min_z = min(min_z, pt.z)
                            max_x = max(max_x, pt.x)
                            max_y = max(max_y, pt.y)
                            max_z = max(max_z, pt.z)
                            has_valid = True
                    elif hasattr(element, 'base_point'):
                        pt = element.base_point
                        min_x = min(min_x, pt.x)
                        min_y = min(min_y, pt.y)
                        min_z = min(min_z, pt.z)
                        max_x = max(max_x, pt.x)
                        max_y = max(max_y, pt.y)
                        max_z = max(max_z, pt.z)
                        has_valid = True
                    continue
                min_x = min(min_x, el_min.x)
                min_y = min(min_y, el_min.y)
                min_z = min(min_z, el_min.z)
                max_x = max(max_x, el_max.x)
                max_y = max(max_y, el_max.y)
                max_z = max(max_z, el_max.z)
                has_valid = True
            except Exception:
                continue

        if not has_valid:
            return (Point3D.origin(), Point3D(10000, 10000, 10000))

        return (Point3D(min_x, min_y, min_z), Point3D(max_x, max_y, max_z))

    # Selection management
    def select_element(self, element_id: UUID, add_to_selection: bool = False):
        """
        Select an element.

        Args:
            element_id: Element to select
            add_to_selection: If True, add to existing selection; if False, replace
        """
        if element_id not in self._elements:
            return

        if not add_to_selection:
            self._selected_ids.clear()

        if element_id not in self._selected_ids:
            self._selected_ids.append(element_id)

        self.selection_changed.emit(self._selected_ids.copy())

    def deselect_element(self, element_id: UUID):
        """Deselect an element."""
        if element_id in self._selected_ids:
            self._selected_ids.remove(element_id)
            self.selection_changed.emit(self._selected_ids.copy())

    def select_all(self):
        """Select all elements."""
        self._selected_ids = list(self._elements.keys())
        self.selection_changed.emit(self._selected_ids.copy())

    def clear_selection(self):
        """Clear all selections."""
        self._selected_ids.clear()
        self.selection_changed.emit([])

    def get_selected_elements(self) -> List[StructuralElement]:
        """Get currently selected elements."""
        return [self._elements[id] for id in self._selected_ids if id in self._elements]

    def get_selected_ids(self) -> List[UUID]:
        """Get IDs of selected elements."""
        return self._selected_ids.copy()

    # Command/Undo support
    def execute_command(self, command: "Command"):
        """
        Execute command with undo support.

        Args:
            command: Command to execute
        """
        command.execute(self)
        self._undo_stack.append(command)
        self._redo_stack.clear()

        # Limit undo stack size
        while len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)

        self._modified = True
        self.model_changed.emit()

    def undo(self) -> bool:
        """
        Undo last command.

        Returns:
            True if undo was performed
        """
        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()
        command.undo(self)
        self._redo_stack.append(command)

        self.model_changed.emit()
        return True

    def redo(self) -> bool:
        """
        Redo last undone command.

        Returns:
            True if redo was performed
        """
        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()
        command.execute(self)
        self._undo_stack.append(command)

        self.model_changed.emit()
        return True

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    # Grid and Level management
    def add_grid(self, grid: GridSystem) -> UUID:
        """Add a grid system to the model."""
        self._grids.append(grid)
        # Also add to elements map for generic handling
        self.add_element(grid)
        return grid.id

    def remove_grid(self, grid_id: UUID) -> bool:
        """Remove a grid system from the model."""
        # Remove from _grids list
        grid = next((g for g in self._grids if g.id == grid_id), None)
        if grid:
            self._grids.remove(grid)
            # Remove from elements map
            self.remove_element(grid_id)
            return True
        return False

    def get_grids(self) -> List[GridSystem]:
        """Get all grid systems."""
        return self._grids.copy()

    def add_level(self, level: Level) -> UUID:
        """Add a level to the model."""
        self._levels.append(level)
        self._levels.sort(key=lambda l: l.elevation)
        # Also add to elements map
        self.add_element(level)
        return level.id

    def remove_level(self, level_id: UUID) -> bool:
        """Remove a level from the model."""
        level = next((l for l in self._levels if l.id == level_id), None)
        if level:
            self._levels.remove(level)
            self.remove_element(level_id)
            return True
        return False

    def get_levels(self) -> List[Level]:
        """Get all levels sorted by elevation."""
        return self._levels.copy()

    def get_level_at_elevation(self, elevation: float, tolerance: float = 1.0) -> Optional[Level]:
        """Get level at specific elevation."""
        for level in self._levels:
            if abs(level.elevation - elevation) < tolerance:
                return level
        return None


class Command(ABC):
    """Abstract base class for commands."""
    
    @abstractmethod
    def execute(self, model: "StructuralModel"):
        pass
        
    @abstractmethod
    def undo(self, model: "StructuralModel"):
        pass


class AddElementCommand(Command):
    """Command to add an element."""
    
    def __init__(self, element: StructuralElement):
        self.element = element
        self._added_id = None
        
    def execute(self, model: "StructuralModel"):
        # If element is already in model (redo case), ensure we don't duplicate logic if needed
        # But add_element handles it.
        self._added_id = model.add_element(self.element)
        
    def undo(self, model: "StructuralModel"):
        if self._added_id:
            model.remove_element(self._added_id)


class RemoveElementCommand(Command):
    """Command to remove an element."""
    
    def __init__(self, element_id: UUID):
        self.element_id = element_id
        self.element = None
        
    def execute(self, model: "StructuralModel"):
        self.element = model.get_element(self.element_id)
        if self.element:
            model.remove_element(self.element_id)
            
    def undo(self, model: "StructuralModel"):
        if self.element:
            model.add_element(self.element)
