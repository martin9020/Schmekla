"""
Structural model (document) class for Schmekla.

The main container for all structural elements in a project.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from pathlib import Path
import json
from loguru import logger

from PySide6.QtCore import QObject, Signal

from src.core.element import StructuralElement, ElementType


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
        self._grids: List[Any] = []  # Grid objects
        self._levels: List[Any] = []  # Level objects

        # Selection
        self._selected_ids: List[UUID] = []

        # Undo/redo stacks
        self._undo_stack: List["Command"] = []
        self._redo_stack: List["Command"] = []
        self._max_undo: int = 100

        # Modification tracking
        self._modified: bool = False

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

        Args:
            element: Element to add

        Returns:
            Element UUID
        """
        self._elements[element.id] = element
        self._modified = True

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

    # Serialization
    def save(self, file_path: Path = None) -> bool:
        """
        Save model to file.

        Args:
            file_path: Path to save to (uses existing path if None)

        Returns:
            True if successful
        """
        if file_path is None:
            file_path = self.file_path

        if file_path is None:
            logger.error("No file path specified for save")
            return False

        try:
            data = self._to_dict()

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self.file_path = file_path
            self._modified = False

            logger.info(f"Saved model to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load(self, file_path: Path) -> bool:
        """
        Load model from file.

        Args:
            file_path: Path to load from

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            self._from_dict(data)
            self.file_path = file_path
            self._modified = False

            logger.info(f"Loaded model from {file_path}")
            self.model_changed.emit()
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def _to_dict(self) -> dict:
        """Serialize model to dictionary."""
        return {
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "elements": {
                str(id): self._element_to_dict(elem)
                for id, elem in self._elements.items()
            },
            "grids": [],  # TODO: Serialize grids
            "levels": [],  # TODO: Serialize levels
        }

    def _element_to_dict(self, element: StructuralElement) -> dict:
        """Serialize element to dictionary."""
        # Base properties
        data = {
            "type": element.element_type.value,
            "name": element.name,
            "material": element.material.name if element.material else None,
            "profile": element.profile.name if element.profile else None,
        }
        # Add element-specific properties
        data.update(element.get_properties())
        return data

    def _from_dict(self, data: dict):
        """Deserialize model from dictionary."""
        self.name = data.get("name", "Untitled")
        self.author = data.get("author", "")
        self.description = data.get("description", "")

        # Clear existing
        self._elements.clear()
        self._selected_ids.clear()

        # Load elements
        # TODO: Implement element deserialization
        logger.warning("Element deserialization not yet implemented")

    def clear(self):
        """Clear all elements from model."""
        self._elements.clear()
        self._selected_ids.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._grids.clear()
        self._levels.clear()
        self._modified = True

        self.model_changed.emit()
        self.selection_changed.emit([])

        logger.info("Model cleared")

    def get_bounding_box(self) -> tuple:
        """
        Get bounding box of entire model.

        Returns:
            Tuple of (min_point, max_point)
        """
        from src.geometry.point import Point3D

        if not self._elements:
            return (Point3D.origin(), Point3D(1000, 1000, 1000))

        min_pt = Point3D(float('inf'), float('inf'), float('inf'))
        max_pt = Point3D(float('-inf'), float('-inf'), float('-inf'))

        for element in self._elements.values():
            elem_min, elem_max = element.get_bounding_box()

            min_pt = Point3D(
                min(min_pt.x, elem_min.x),
                min(min_pt.y, elem_min.y),
                min(min_pt.z, elem_min.z)
            )
            max_pt = Point3D(
                max(max_pt.x, elem_max.x),
                max(max_pt.y, elem_max.y),
                max(max_pt.z, elem_max.z)
            )

        return (min_pt, max_pt)


class Command:
    """Base class for undoable commands."""

    def execute(self, model: StructuralModel):
        """Execute the command."""
        raise NotImplementedError

    def undo(self, model: StructuralModel):
        """Undo the command."""
        raise NotImplementedError


class AddElementCommand(Command):
    """Command to add an element."""

    def __init__(self, element: StructuralElement):
        self.element = element
        self.element_id = element.id

    def execute(self, model: StructuralModel):
        model._elements[self.element_id] = self.element
        model.element_added.emit(self.element)

    def undo(self, model: StructuralModel):
        if self.element_id in model._elements:
            del model._elements[self.element_id]
            model.element_removed.emit(self.element)


class RemoveElementCommand(Command):
    """Command to remove an element."""

    def __init__(self, element: StructuralElement):
        self.element = element
        self.element_id = element.id

    def execute(self, model: StructuralModel):
        if self.element_id in model._elements:
            del model._elements[self.element_id]
            model.element_removed.emit(self.element)

    def undo(self, model: StructuralModel):
        model._elements[self.element_id] = self.element
        model.element_added.emit(self.element)
