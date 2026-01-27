"""
Numbering commands for Schmekla.

Provides undoable commands for element renumbering operations.
"""

from typing import Dict, TYPE_CHECKING
from uuid import UUID
from loguru import logger

if TYPE_CHECKING:
    from src.core.model import StructuralModel


class RenumberCommand:
    """Command for renumbering elements with undo support.

    This command captures the before and after state of element part numbers,
    allowing full undo/redo functionality for renumbering operations.

    Usage:
        cmd = RenumberCommand(model, "Renumber All Elements")
        cmd.capture_before_state()
        # ... perform renumbering ...
        cmd.capture_after_state()
        model.execute_command(cmd)
    """

    def __init__(self, model: "StructuralModel", description: str = "Renumber elements"):
        """
        Initialize the renumber command.

        Args:
            model: The structural model containing elements to renumber
            description: Human-readable description for undo/redo display
        """
        self.model = model
        self.description = description
        # Store old numbers: {element_id: old_part_number}
        self._old_numbers: Dict[UUID, str] = {}
        # Store new numbers: {element_id: new_part_number}
        self._new_numbers: Dict[UUID, str] = {}

    def capture_before_state(self):
        """Capture current part numbers before renumbering.

        Call this BEFORE performing any renumbering operations.
        """
        self._old_numbers.clear()
        for element in self.model.get_all_elements():
            self._old_numbers[element.id] = element.part_number
        logger.debug(f"Captured before state: {len(self._old_numbers)} elements")

    def capture_after_state(self):
        """Capture new part numbers after renumbering.

        Call this AFTER performing all renumbering operations.
        """
        self._new_numbers.clear()
        for element in self.model.get_all_elements():
            self._new_numbers[element.id] = element.part_number
        logger.debug(f"Captured after state: {len(self._new_numbers)} elements")

    def execute(self, model: "StructuralModel"):
        """Execute is called by model - just emit changed signal.

        Note: The actual renumbering has already been done before this command
        is pushed to the undo stack. This method just emits the change signal.

        Args:
            model: The structural model (passed by model.execute_command)
        """
        # Signal is emitted by model.execute_command after this returns
        logger.info(f"Renumber executed: {len(self._new_numbers)} elements")

    def undo(self, model: "StructuralModel"):
        """Restore old part numbers.

        Args:
            model: The structural model (passed by model.undo)
        """
        for elem_id, old_number in self._old_numbers.items():
            element = model.get_element(elem_id)
            if element:
                element.part_number = old_number
        logger.info(f"Renumber undone: restored {len(self._old_numbers)} part numbers")

    def redo(self, model: "StructuralModel"):
        """Re-apply new part numbers.

        Note: The model's redo() method calls execute(), not redo().
        This method is provided for completeness but won't be called
        by the current model implementation.

        Args:
            model: The structural model
        """
        for elem_id, new_number in self._new_numbers.items():
            element = model.get_element(elem_id)
            if element:
                element.part_number = new_number
        logger.info(f"Renumber redone: {len(self._new_numbers)} elements")
