from enum import Enum, auto
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID
from PySide6.QtCore import QObject, Signal
from loguru import logger
from src.geometry.point import Point3D

class InteractionMode(Enum):
    IDLE = auto()           # Selection / Navigation
    CREATE_BEAM = auto()    # Two-point creation
    CREATE_COLUMN = auto()  # One-point creation
    CREATE_PLATE = auto()   # Multi-point creation

class InteractionState(Enum):
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

    def __init__(self):
        super().__init__()
        self._mode = InteractionMode.IDLE
        self._state = InteractionMode.IDLE
        self._points: List[Point3D] = []
        self._selection: List[UUID] = []
        
        # Tool options
        self.current_profile_name = "UB 305x165x40"  # Default
        self.current_material_name = "S355"          # Default

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
            self.prompt_changed.emit("Ready.")
        elif mode == InteractionMode.CREATE_BEAM:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick start point")
        elif mode == InteractionMode.CREATE_COLUMN:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick column position")
        elif mode == InteractionMode.CREATE_PLATE:
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick corner point 1")

    def handle_click(self, point: Point3D):
        """
        Handle a 3D point click from the Viewport.
        """
        if self._mode == InteractionMode.IDLE:
            # Idle click logic handled by selection raycast usually
            # But if specific point logic needed (e.g. measure), do it here
            return

        if self._mode == InteractionMode.CREATE_BEAM:
            self._handle_create_beam(point)
        elif self._mode == InteractionMode.CREATE_COLUMN:
            self._handle_create_column(point)
        elif self._mode == InteractionMode.CREATE_PLATE:
            self._handle_create_plate(point)

    def _handle_create_beam(self, point: Point3D):
        if self._state == InteractionState.WAITING_FOR_POINT_1:
            self._points.append(point)
            self._state = InteractionState.WAITING_FOR_POINT_2
            self.prompt_changed.emit("Pick end point")
            
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
            self.prompt_changed.emit("Pick start point")

    def _handle_create_column(self, point: Point3D):
        # Column is single click + height property (default)
        self.element_created.emit("COLUMN", {
            "base": point,
            "height": 3000.0, # Default, should come from UI properties
            "profile": "UC 203x203x46",
            "material": self.current_material_name
        })
        self.prompt_changed.emit("Pick column position")

    def _handle_create_plate(self, point: Point3D):
        # Tekla plates usually 4 points then auto-close
        self._points.append(point)
        
        count = len(self._points)
        if count < 4:
            self._state = getattr(InteractionState, f"WAITING_FOR_POINT_{count+1}")
            self.prompt_changed.emit(f"Pick corner point {count+1}")
        else:
            # 4 points collected
            self.element_created.emit("PLATE", {
                "points": list(self._points),
                "thickness": 10.0,
                "material": self.current_material_name
            })
            self._points.clear()
            self._state = InteractionState.WAITING_FOR_POINT_1
            self.prompt_changed.emit("Pick corner point 1")

    def cancel(self):
        """Cancel current command and return to IDLE."""
        self.set_mode(InteractionMode.IDLE)
