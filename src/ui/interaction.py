from enum import Enum, auto
from typing import Optional, Tuple, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
from PySide6.QtCore import QObject, Signal
from loguru import logger
from src.geometry.point import Point3D

if TYPE_CHECKING:
    from src.core.snap_manager import SnapManager

class InteractionMode(Enum):
    IDLE = auto()           # Selection / Navigation
    CREATE_BEAM = auto()    # Two-point creation
    CREATE_COLUMN = auto()  # One-point creation
    CREATE_PLATE = auto()   # Multi-point creation
    COPY = auto()           # Two-point copy: pick base point, pick destination
    MOVE = auto()           # Two-point move: pick base point, pick destination

class InteractionState(Enum):
    IDLE = auto()                    # No active point collection
    WAITING_FOR_POINT_1 = auto()
    WAITING_FOR_POINT_2 = auto()
    WAITING_FOR_POINT_3 = auto()
    WAITING_FOR_POINT_4 = auto()

class InteractionManager(QObject):
    """
    Manages user interaction states, tool selection, and coordinate inputs.
    Follows a localized 'Tekla-like' workflow.
    """

    # Signals
    mode_changed = Signal(str)              # Emitted when tool changes
    prompt_changed = Signal(str)            # Emitted to update status bar prompt
    element_created = Signal(str, dict)     # Emitted to request element creation (type, params)
    selection_changed = Signal(list)        # Emitted when selection changes (list of UUIDs)
    snap_occurred = Signal(object, str)     # Emitted when snap occurs (point, snap_type)
    copy_requested = Signal(object)         # Emitted when copy displacement is determined (displacement vector)
    move_requested = Signal(object)         # Emitted when move displacement is determined (displacement vector)

    def __init__(self, snap_manager: "SnapManager" = None):
        super().__init__()
        self._mode = InteractionMode.IDLE
        self._state = InteractionState.IDLE
        self._points: List[Point3D] = []
        self._selection: List[UUID] = []
        self.snap_manager = snap_manager

        # Tool options
        self.current_profile_name = "UB 305x165x40"  # Default
        self.current_material_name = "S355"          # Default

        # Copy/Move state
        self._copy_base_point: Optional[Point3D] = None
        self._elements_to_copy: List[UUID] = []

    @property
    def mode(self):
        return self._mode

    def set_mode(self, mode: InteractionMode):
        """Set the current active tool/mode."""
        self._mode = mode
        self._points.clear()

        logger.info(f"Interaction Mode: {mode.name}")
        self.mode_changed.emit(mode.name)

        if mode == InteractionMode.IDLE:
            self._state = InteractionState.IDLE
            self.prompt_changed.emit("Ready.")
        elif mode == InteractionMode.CREATE_BEAM:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick start point" + self._get_snap_hint())
        elif mode == InteractionMode.CREATE_COLUMN:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick column position" + self._get_snap_hint())
        elif mode == InteractionMode.CREATE_PLATE:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick corner point 1" + self._get_snap_hint())
        elif mode == InteractionMode.COPY:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self._copy_base_point = None
            self.prompt_changed.emit("Select elements, then pick base point..." + self._get_snap_hint())
        elif mode == InteractionMode.MOVE:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self._copy_base_point = None
            self.prompt_changed.emit("Select elements, then pick base point..." + self._get_snap_hint())

    def _get_snap_hint(self) -> str:
        """Get snap status hint for status bar."""
        if self.snap_manager and self.snap_manager.snap_enabled:
            snaps = []
            if self.snap_manager.grid_snap:
                snaps.append("Grid")
            if self.snap_manager.endpoint_snap:
                snaps.append("Endpoint")
            if snaps:
                return f" [Snap: {', '.join(snaps)}]"
        return ""

    def handle_click(self, point: Point3D):
        """
        Handle a 3D point click from the Viewport.
        """
        if self._mode == InteractionMode.IDLE:
            # Idle click logic handled by selection raycast usually
            # But if specific point logic needed (e.g. measure), do it here
            return

        # Apply snapping if available
        original_point = point
        snap_type = ""
        if self.snap_manager:
            snapped, snap_type = self.snap_manager.find_nearest_snap(point)
            if snapped:
                logger.info(f"Snapped to {snap_type}: {snapped}")
                point = snapped
                # Emit snap signal for visual feedback
                self.snap_occurred.emit(point, snap_type)
                # Update status bar with snap info
                self._emit_snap_prompt(snap_type)

        if self._mode == InteractionMode.CREATE_BEAM:
            self._handle_create_beam(point, snap_type)
        elif self._mode == InteractionMode.CREATE_COLUMN:
            self._handle_create_column(point, snap_type)
        elif self._mode == InteractionMode.CREATE_PLATE:
            self._handle_create_plate(point, snap_type)
        elif self._mode == InteractionMode.COPY:
            self._handle_copy(point, snap_type)
        elif self._mode == InteractionMode.MOVE:
            self._handle_move(point, snap_type)

    def _emit_snap_prompt(self, snap_type: str):
        """Emit a prompt with snap feedback."""
        if snap_type == "grid":
            feedback = " (Snapped to grid)"
        elif snap_type == "endpoint":
            feedback = " (Snapped to endpoint)"
        elif snap_type == "midpoint":
            feedback = " (Snapped to midpoint)"
        else:
            feedback = ""
        # The feedback is included in the next prompt update

    def _handle_create_beam(self, point: Point3D, snap_type: str = ""):
        snap_info = f" [Snapped to {snap_type}]" if snap_type else ""

        if self._state == InteractionState.WAITING_FOR_POINT_1:
            self._points.append(point)
            self._state = InteractionState.WAITING_FOR_POINT_2
            self.prompt_changed.emit(f"Pick end point{self._get_snap_hint()}{snap_info}")

        elif self._state == InteractionState.WAITING_FOR_POINT_2:
            start = self._points[0]
            end = point

            # Emit creation request
            self.element_created.emit("BEAM", {
                "start": start,
                "end": end,
                "profile": self.current_profile_name,
                "material": self.current_material_name
            })

            # Reset for next beam
            self._points.clear()
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit(f"Beam created{snap_info}. Pick start point{self._get_snap_hint()}")

    def _handle_create_column(self, point: Point3D, snap_type: str = ""):
        snap_info = f" [Snapped to {snap_type}]" if snap_type else ""

        # Column is single click + height property (default)
        self.element_created.emit("COLUMN", {
            "base": point,
            "height": 3000.0, # Default, should come from UI properties
            "profile": "UC 203x203x46",
            "material": self.current_material_name
        })
        self.prompt_changed.emit(f"Column created{snap_info}. Pick column position{self._get_snap_hint()}")

    def _handle_create_plate(self, point: Point3D, snap_type: str = ""):
        snap_info = f" [Snapped to {snap_type}]" if snap_type else ""

        # Tekla plates usually 4 points then auto-close
        self._points.append(point)

        count = len(self._points)
        if count < 4:
            self._state = getattr(InteractionState, f"WAITING_FOR_POINT_{count+1}")
            self.prompt_changed.emit(f"Pick corner point {count+1}{self._get_snap_hint()}{snap_info}")
        else:
            # 4 points collected
            self.element_created.emit("PLATE", {
                "points": list(self._points),
                "thickness": 10.0,
                "material": self.current_material_name
            })
            self._points.clear()
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit(f"Plate created{snap_info}. Pick corner point 1{self._get_snap_hint()}")

    def _handle_copy(self, point: Point3D, snap_type: str = ""):
        """Handle two-point copy workflow: pick base point, then destination."""
        snap_info = f" [Snapped to {snap_type}]" if snap_type else ""

        if self._copy_base_point is None:
            # First click: set base point
            self._copy_base_point = point
            self._state = InteractionState.WAITING_FOR_POINT_2
            self.prompt_changed.emit(f"Pick destination point...{self._get_snap_hint()}{snap_info}")
        else:
            # Second click: calculate displacement and emit copy request
            displacement = point - self._copy_base_point
            logger.info(f"Copy displacement: {displacement}")
            self.copy_requested.emit(displacement)

            # Reset for next copy (keep same base point for multiple copies)
            self._copy_base_point = None
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit(f"Copy complete{snap_info}. Pick base point for next copy...{self._get_snap_hint()}")

    def _handle_move(self, point: Point3D, snap_type: str = ""):
        """Handle two-point move workflow: pick base point, then destination."""
        snap_info = f" [Snapped to {snap_type}]" if snap_type else ""

        if self._copy_base_point is None:
            # First click: set base point
            self._copy_base_point = point
            self._state = InteractionState.WAITING_FOR_POINT_2
            self.prompt_changed.emit(f"Pick destination point...{self._get_snap_hint()}{snap_info}")
        else:
            # Second click: calculate displacement and emit move request
            displacement = point - self._copy_base_point
            logger.info(f"Move displacement: {displacement}")
            self.move_requested.emit(displacement)

            # Reset and return to idle (move is a one-time operation)
            self._copy_base_point = None
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit(f"Move complete{snap_info}. Pick base point to move again...{self._get_snap_hint()}")

    def cancel(self):
        """Cancel current command and return to IDLE."""
        self.set_mode(InteractionMode.IDLE)

    def toggle_grid_snap(self) -> bool:
        """Toggle grid snapping on/off."""
        if self.snap_manager:
            self.snap_manager.toggle_grid_snap()
            state = "enabled" if self.snap_manager.grid_snap else "disabled"
            self.prompt_changed.emit(f"Grid snap {state}")
            return self.snap_manager.grid_snap
        return False

    def toggle_endpoint_snap(self) -> bool:
        """Toggle endpoint snapping on/off."""
        if self.snap_manager:
            self.snap_manager.toggle_endpoint_snap()
            state = "enabled" if self.snap_manager.endpoint_snap else "disabled"
            self.prompt_changed.emit(f"Endpoint snap {state}")
            return self.snap_manager.endpoint_snap
        return False

    def toggle_all_snaps(self) -> bool:
        """Toggle all snapping on/off."""
        if self.snap_manager:
            self.snap_manager.snap_enabled = not self.snap_manager.snap_enabled
            state = "enabled" if self.snap_manager.snap_enabled else "disabled"
            self.prompt_changed.emit(f"All snapping {state}")
            return self.snap_manager.snap_enabled
        return False
