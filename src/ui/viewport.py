"""
3D Viewport for Schmekla.

PyVista-based 3D visualization widget.
"""

from typing import Dict, List, Set, Optional, Tuple
from uuid import UUID
from loguru import logger

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Qt

from src.core.model import StructuralModel
from src.core.element import StructuralElement
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D


# =============================================================================
# Custom QtInteractor that intercepts mouse events at Qt level
# =============================================================================

try:
    from pyvistaqt import QtInteractor

    class SelectionQtInteractor(QtInteractor):
        """Custom QtInteractor that handles mouse events at Qt level.

        This is CRITICAL: VTK interactor style overrides don't work because
        PyVista's QVTKRenderWindowInteractor.mouseMoveEvent() unconditionally
        sends all mouse events to VTK. The only way to prevent left-drag
        rotation is to intercept events at the Qt level BEFORE they reach VTK.

        Interaction model:
        - Left click: Select element (handled by viewport)
        - Left drag: Box selection (handled by viewport)
        - Ctrl + Right drag: Rotate viewport
        - Right drag (no Ctrl): Zoom
        - Middle drag: Pan
        - Scroll wheel: Zoom
        """

        def __init__(self, viewport, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.viewport = viewport
            self._left_button_down = False
            self._drag_start = None
            self._is_dragging = False
            self._ctrl_pressed = False
            self._middle_rotating = False  # For Ctrl+Middle rotation

        def mousePressEvent(self, event):
            """Intercept mouse press BEFORE VTK processes it."""
            button = event.button()
            modifiers = event.modifiers()
            self._ctrl_pressed = bool(modifiers & Qt.KeyboardModifier.ControlModifier)

            if button == Qt.MouseButton.LeftButton:
                # Check current mode - in creation modes, let VTK handle for ground picking
                current_mode = getattr(self.viewport, '_current_mode', 'IDLE')
                if current_mode != 'IDLE':
                    # Creation/Copy/Move mode - let VTK handle for ground plane picking
                    super().mousePressEvent(event)
                    return

                # IDLE mode - handle left button ourselves for selection
                self._left_button_down = True
                self._drag_start = (event.position().x(), event.position().y())
                self._is_dragging = False

                # Sync state with viewport
                self.viewport._ctrl_pressed = self._ctrl_pressed
                self.viewport._selection_start = (int(self._drag_start[0]), int(self._drag_start[1]))
                self.viewport._selection_dragging = False
                self.viewport._is_selecting = True

                # NO super() call - VTK never sees LeftButtonPressEvent in IDLE mode
                return

            elif button == Qt.MouseButton.RightButton:
                if self._ctrl_pressed:
                    # Ctrl+Right = Rotate - let VTK handle as left button (rotation)
                    # We fake a left button press for VTK
                    self._fake_left_button_for_rotate(event, press=True)
                    return
                # Regular right button = Context menu (copy, paste, etc.)
                # Don't pass to VTK - let Qt handle for context menu
                # The context menu will be shown by the viewport widget
                return

            elif button == Qt.MouseButton.MiddleButton:
                if self._ctrl_pressed:
                    # Ctrl+Middle = Rotate - same as Ctrl+Right
                    self._middle_rotating = True
                    self._fake_left_button_for_rotate(event, press=True)
                    return
                # Regular middle button = Pan (default VTK behavior)
                super().mousePressEvent(event)
                return

            # Other buttons: let parent handle normally
            super().mousePressEvent(event)

        def mouseReleaseEvent(self, event):
            """Intercept mouse release."""
            button = event.button()

            if button == Qt.MouseButton.LeftButton:
                # Check current mode - in creation modes, let VTK handle
                current_mode = getattr(self.viewport, '_current_mode', 'IDLE')
                if current_mode != 'IDLE':
                    # Creation/Copy/Move mode - let VTK handle
                    super().mouseReleaseEvent(event)
                    return

                # IDLE mode - handle our selection logic
                if self._left_button_down:
                    x, y = int(event.position().x()), int(event.position().y())

                    if self._is_dragging:
                        # End of drag - finish box selection
                        self.viewport.finish_selection_box(x, y)
                    else:
                        # Single click - do element picking
                        self.viewport._do_element_pick(x, y)

                    # Reset state
                    self._left_button_down = False
                    self._drag_start = None
                    self._is_dragging = False
                    self.viewport._selection_start = None
                    self.viewport._selection_dragging = False
                    self.viewport._is_selecting = False

                # NO super() call in IDLE mode
                return

            elif button == Qt.MouseButton.RightButton:
                if self._ctrl_pressed:
                    # End Ctrl+Right rotation
                    self._fake_left_button_for_rotate(event, press=False)
                    self._ctrl_pressed = False
                    return
                # Regular right button release - show context menu
                self.viewport._show_context_menu(event.globalPosition().toPoint())
                return

            elif button == Qt.MouseButton.MiddleButton:
                if getattr(self, '_middle_rotating', False):
                    # End Ctrl+Middle rotation
                    self._fake_left_button_for_rotate(event, press=False)
                    self._middle_rotating = False
                    return
                # Regular middle button release
                super().mouseReleaseEvent(event)
                return

            super().mouseReleaseEvent(event)

        def mouseMoveEvent(self, event):
            """Intercept mouse move - CRITICAL to prevent rotation in IDLE mode."""
            # Update ctrl state
            modifiers = event.modifiers()
            self._ctrl_pressed = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            self.viewport._ctrl_pressed = self._ctrl_pressed

            # Check current mode
            current_mode = getattr(self.viewport, '_current_mode', 'IDLE')

            # In creation/copy/move modes, let VTK handle (for snap indicator via parent)
            if current_mode != 'IDLE':
                # Update snap indicator
                is_creation = current_mode.startswith("CREATE_")
                is_copy_move = current_mode in ("COPY", "MOVE")
                if is_creation or is_copy_move:
                    x, y = int(event.position().x()), int(event.position().y())
                    self.viewport._update_snap_indicator_at_mouse(x, y)
                # Let VTK handle mouse move in creation modes
                super().mouseMoveEvent(event)
                return

            # IDLE mode - handle box selection if left button is down
            if self._left_button_down and self._drag_start:
                x, y = event.position().x(), event.position().y()
                dx = abs(x - self._drag_start[0])
                dy = abs(y - self._drag_start[1])

                if not self._is_dragging and (dx > 5 or dy > 5):
                    # Started dragging - threshold crossed
                    self._is_dragging = True
                    self.viewport._selection_dragging = True

                if self._is_dragging:
                    # Update box selection rectangle
                    self.viewport._draw_selection_rect(int(x), int(y))

                # NO super() call - VTK MouseMoveEvent is NEVER called in IDLE with left button
                # This prevents rotation!
                return

            # Left button not down in IDLE mode - let parent handle (camera control for other buttons)
            super().mouseMoveEvent(event)

        def _fake_left_button_for_rotate(self, event, press=True):
            """Fake a left button event to VTK for Ctrl+Right rotation.

            VTK's trackball camera uses left button for rotation. We intercept
            Ctrl+Right and translate it to left button for VTK.
            """
            try:
                # Get interactor
                iren = self._Iren
                if iren is None:
                    return

                # Set event position
                x, y = int(event.position().x()), int(event.position().y())
                iren.SetEventInformation(x, self.height() - y - 1)

                if press:
                    iren.LeftButtonPressEvent()
                else:
                    iren.LeftButtonReleaseEvent()
            except Exception as e:
                logger.debug(f"Error faking button event: {e}")

except ImportError:
    SelectionQtInteractor = None
    logger.warning("pyvistaqt not available - SelectionQtInteractor disabled")


class Viewport3D(QWidget):
    """
    3D viewport for model visualization.

    Uses PyVista/VTK for rendering.
    """

    # Signals
    element_selected = Signal(object)
    point_picked = Signal(object)
    selection_changed = Signal(list)
    snap_feedback = Signal(str)  # Signal to update status bar with snap info

    # Context menu signals
    copy_requested = Signal()
    paste_requested = Signal()
    delete_requested = Signal()

    def __init__(self, model: StructuralModel, interaction_manager=None, parent=None):
        super().__init__(parent)

        self.model = model
        self.interaction_manager = interaction_manager
        self._actors: Dict[UUID, object] = {}
        self._selected_ids: Set[UUID] = set()
        self._creation_mode: Optional[str] = None

        # Alt+drag selection state
        self._alt_pressed = False
        self._ctrl_pressed = False  # For Ctrl+click multi-selection
        self._selection_start = None  # (x, y) screen coords
        self._selection_dragging = False
        self._selection_rect_actor = None
        self._is_window_selection = True  # Left-to-right = window, right-to-left = crossing
        self._is_selecting = False  # True while actively box-selecting (blocks camera rotation)

        # Snap indicator
        self._snap_indicator_actor = None

        # Start/End point markers tracking
        self._start_end_markers: Dict[UUID, Tuple] = {}  # element_id -> (start_actor, end_actor)
        self._show_start_end_markers: bool = True

        self._setup_ui()
        self._connect_model_signals()

        if self.interaction_manager:
            # Connect picking signal to interaction manager
            self.point_picked.connect(self.interaction_manager.handle_click)
            # Listen to mode changes to switch interactor styles
            self.interaction_manager.mode_changed.connect(self.set_interaction_mode)

        logger.info("Viewport3D initialized")

    def _setup_ui(self):
        """Initialize viewport UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            import pyvista as pv

            # Use our custom SelectionQtInteractor that handles mouse at Qt level
            # This is CRITICAL - regular QtInteractor sends all mouse events to VTK
            # which causes left-drag to rotate. Our custom class intercepts at Qt level.
            if SelectionQtInteractor is not None:
                self.plotter = SelectionQtInteractor(self, parent=self)
                logger.info("Using SelectionQtInteractor (Qt-level mouse handling)")
            else:
                from pyvistaqt import QtInteractor
                self.plotter = QtInteractor(self)
                logger.warning("Using standard QtInteractor (custom mouse handling unavailable)")

            layout.addWidget(self.plotter.interactor)

            # Configure plotter
            self.plotter.set_background('#2b2b2b')
            self.plotter.add_axes()
            self.plotter.enable_anti_aliasing()

            # Add ground grid
            self._add_grid_plane()

            # Set initial view
            self.plotter.camera_position = 'iso'
            self.plotter.reset_camera()

            # Store interactor for style changes
            self._interactor = self.plotter.iren.interactor

            # Start in IDLE mode (selection/navigation)
            self._current_mode = "IDLE"
            self._enable_selection_picking()

            # Install Alt+drag selection interactor
            self._install_selection_interactor()

            # Pre-warm the ground plane picking callback to avoid first-time delay
            # This initializes VTK coordinate conversion objects in advance
            self._prewarm_picking()

            logger.info("PyVista viewport created successfully")

        except ImportError as e:
            logger.warning(f"PyVista not available: {e}")
            self.plotter = None

            # Create placeholder
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt
            label = QLabel("3D Viewport\n\nPyVista not available")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 16px; background: #2b2b2b;")
            layout.addWidget(label)

    def _add_grid_plane(self):
        """Add ground grid plane."""
        if self.plotter is None:
            return

        import pyvista as pv
        import numpy as np

        # Create grid lines
        grid_size = 20000  # 20m grid
        grid_spacing = 1000  # 1m spacing

        points = []
        lines = []
        idx = 0

        # X-direction lines
        for y in np.arange(-grid_size, grid_size + grid_spacing, grid_spacing):
            points.extend([[-grid_size, y, 0], [grid_size, y, 0]])
            lines.extend([2, idx, idx + 1])
            idx += 2

        # Y-direction lines
        for x in np.arange(-grid_size, grid_size + grid_spacing, grid_spacing):
            points.extend([[x, -grid_size, 0], [x, grid_size, 0]])
            lines.extend([2, idx, idx + 1])
            idx += 2

        if points:
            grid = pv.PolyData(np.array(points))
            grid.lines = np.array(lines)
            self.plotter.add_mesh(grid, color='#404040', line_width=1, name='grid')

    def _connect_model_signals(self):
        """Connect to model signals."""
        self.model.element_added.connect(self._on_element_added)
        self.model.element_removed.connect(self._on_element_removed)
        self.model.element_modified.connect(self._on_element_modified)
        self.model.selection_changed.connect(self._on_selection_changed)

    def _on_element_added(self, element: StructuralElement):
        """Handle element added."""
        if self.plotter is None:
            return

        mesh = element.get_mesh()
        if mesh is not None:
            color = self._get_element_color(element)
            actor = self.plotter.add_mesh(
                mesh,
                color=color,
                opacity=1.0,
                name=str(element.id)
            )
            self._actors[element.id] = actor
            self.plotter.render()
        else:
            # Fallback to simple visualization
            self._add_simple_element(element)
            self.plotter.render()

    def _on_element_removed(self, element: StructuralElement):
        """Handle element removed."""
        if self.plotter is None:
            return

        if element.id in self._actors:
            self.plotter.remove_actor(str(element.id))
            del self._actors[element.id]
            self.plotter.render()

    def _on_element_modified(self, element: StructuralElement):
        """Handle element modified."""
        self._on_element_removed(element)
        self._on_element_added(element)

    def _on_selection_changed(self, selected_ids: list):
        """Handle selection change."""
        old_selection = self._selected_ids.copy()
        self._selected_ids = set(selected_ids)

        # Update colors for elements that changed selection state
        changed_ids = old_selection.symmetric_difference(self._selected_ids)
        for elem_id in changed_ids:
            if elem_id in self._actors:
                actor = self._actors[elem_id]
                element = self.model.get_element(elem_id)
                if element and actor:
                    # Update actor color directly
                    color = self._get_element_color(element)
                    try:
                        prop = actor.GetProperty()
                        # Convert hex color to RGB
                        r = int(color[1:3], 16) / 255.0
                        g = int(color[3:5], 16) / 255.0
                        b = int(color[5:7], 16) / 255.0
                        prop.SetColor(r, g, b)
                    except Exception as e:
                        logger.debug(f"Could not update actor color: {e}")

            # Handle start/end markers for changed elements
            if elem_id in self._selected_ids:
                # Element was selected - show markers
                self.show_start_end_markers(elem_id)
            else:
                # Element was deselected - hide markers
                self.hide_start_end_markers(elem_id)

        self.refresh()

    def _get_element_color(self, element: StructuralElement) -> str:
        """Get color for element based on type and selection."""
        if element.id in self._selected_ids:
            return '#ffff00'  # Yellow for selected

        # Color by element type
        type_colors = {
            'beam': '#4a90d9',
            'column': '#5cb85c',
            'plate': '#d9534f',
            'slab': '#777777',
            'wall': '#888888',
            'footing': '#996633',
        }
        return type_colors.get(element.element_type.value, '#aaaaaa')

    def set_view(self, view_name: str):
        """Set standard view."""
        if self.plotter is None:
            return

        views = {
            'front': 'xz',
            'back': '-xz',
            'top': 'xy',
            'bottom': '-xy',
            'right': 'yz',
            'left': '-yz',
            'iso': 'iso'
        }

        if view_name in views:
            self.plotter.camera_position = views[view_name]
            self.plotter.reset_camera()

    def zoom_to_fit(self):
        """Zoom to fit all elements."""
        if self.plotter:
            self.plotter.reset_camera()

    def zoom_to_selection(self):
        """Zoom to selected elements."""
        # TODO: Implement zoom to selection
        pass

    def refresh(self):
        """Force viewport refresh."""
        if self.plotter:
            self.plotter.render()

    def start_beam_creation(self):
        """Enter beam creation mode (legacy - now handled by set_interaction_mode)."""
        self._creation_mode = 'beam'
        # Picking is now handled via set_interaction_mode signal from InteractionManager

    def set_interaction_mode(self, mode_name: str):
        """
        Switch interactor style based on mode.
        - IDLE: Standard trackball camera for navigation, click picks elements
        - CREATE_*: Enable ground plane picking for point placement (except CREATE_WELD)
        - COPY: Enable ground plane picking for copy base/destination points
        - MOVE: Enable ground plane picking for move base/destination points
        """
        if self.plotter is None:
            return

        # Skip if mode hasn't actually changed (avoids expensive picker re-init)
        if hasattr(self, '_current_mode') and self._current_mode == mode_name:
            logger.debug(f"Mode already {mode_name}, skipping picker re-init")
            return

        # Track previous mode for smart transitions
        previous_mode = getattr(self, '_current_mode', None)
        self._current_mode = mode_name
        logger.info(f"Viewport mode changed to: {mode_name}")

        # IDLE and CREATE_WELD allow selection
        if mode_name == "IDLE" or mode_name == "CREATE_WELD":
            # Only disable and re-enable if coming from a picking mode
            if previous_mode and previous_mode != "IDLE" and previous_mode != "CREATE_WELD":
                try:
                    self.plotter.disable_picking()
                except Exception:
                    pass
                # Enable element selection on click
                self._enable_selection_picking()
                # Hide snap indicator when leaving picking mode
                self.hide_snap_indicator()
        else:
            # Check if this is a mode that needs ground plane picking
            is_creation_mode = mode_name.startswith("CREATE_") and mode_name != "CREATE_WELD"
            is_copy_mode = mode_name == "COPY"
            is_move_mode = mode_name == "MOVE"
            needs_ground_picking = is_creation_mode or is_copy_mode or is_move_mode

            # Check if previous mode also used ground plane picking
            was_creation_mode = previous_mode and previous_mode.startswith("CREATE_") and previous_mode != "CREATE_WELD" if previous_mode else False
            was_copy_mode = previous_mode == "COPY" if previous_mode else False
            was_move_mode = previous_mode == "MOVE" if previous_mode else False
            had_ground_picking = was_creation_mode or was_copy_mode or was_move_mode

            if needs_ground_picking and not had_ground_picking:
                # Switching from IDLE to a picking mode - need to set up ground plane picking
                self._enable_ground_plane_picking()
            # else: Already in a picking mode, ground plane picking is already active

    def _enable_selection_picking(self):
        """Enable element selection picking for IDLE mode."""
        if self.plotter is None:
            return

        # Use point picking with left click to select elements
        # The callback receives the picked point, but we can get the actor from the picker
        self.plotter.enable_point_picking(
            callback=self._on_selection_pick,
            show_message=False,
            show_point=False,
            picker='cell'  # Use cell picker to get actor info
        )
        logger.info("Selection picking enabled")

    def _on_selection_pick(self, picked_point):
        """Handle element selection in IDLE mode via point picking."""
        import time
        import numpy as np

        # Debounce
        current_time = time.time()
        if hasattr(self, '_last_pick_time'):
            if current_time - self._last_pick_time < 0.2:
                return
        self._last_pick_time = current_time

        logger.info(f"Selection pick at: {picked_point}")

        if picked_point is None:
            # Clicked on empty space - clear selection
            logger.info("Selection cleared (clicked empty space)")
            self.model.clear_selection()
            return

        # Find which element contains this point by checking distance to each element
        picked_pt = np.array(picked_point[:3])
        closest_elem_id = None
        min_distance = float('inf')

        for elem_id, actor in self._actors.items():
            # Get the mesh bounds from the actor
            if hasattr(actor, 'GetBounds'):
                bounds = actor.GetBounds()  # (xmin, xmax, ymin, ymax, zmin, zmax)
                # Check if point is within or near the bounds
                center = np.array([
                    (bounds[0] + bounds[1]) / 2,
                    (bounds[2] + bounds[3]) / 2,
                    (bounds[4] + bounds[5]) / 2
                ])
                dist = np.linalg.norm(picked_pt - center)

                # Also check if point is within expanded bounds
                margin = 500  # 500mm tolerance
                in_bounds = (bounds[0] - margin <= picked_pt[0] <= bounds[1] + margin and
                             bounds[2] - margin <= picked_pt[1] <= bounds[3] + margin and
                             bounds[4] - margin <= picked_pt[2] <= bounds[5] + margin)

                if in_bounds and dist < min_distance:
                    min_distance = dist
                    closest_elem_id = elem_id

        if closest_elem_id:
            # Ctrl+click toggles selection (add/remove from multi-selection)
            if self._ctrl_pressed:
                if closest_elem_id in self._selected_ids:
                    # Already selected - deselect it
                    logger.info(f"Ctrl+click deselect: {closest_elem_id}")
                    self.model.deselect_element(closest_elem_id)
                else:
                    # Not selected - add to selection
                    logger.info(f"Ctrl+click add to selection: {closest_elem_id}")
                    self.model.select_element(closest_elem_id, add_to_selection=True)
            else:
                # Normal click - replace selection
                logger.info(f"Element selected: {closest_elem_id}")
                self.model.select_element(closest_elem_id, add_to_selection=False)
            self.element_selected.emit(closest_elem_id)
        else:
            # Clicked on grid or unknown - clear selection (unless Ctrl is held)
            if not self._ctrl_pressed:
                logger.info("Clicked non-element - clearing selection")
                self.model.clear_selection()

    def _prewarm_picking(self):
        """
        Pre-initialize VTK coordinate conversion objects to avoid first-use delay.
        This is called once during viewport setup to 'warm up' the picking pipeline.
        """
        try:
            from vtkmodules.vtkRenderingCore import vtkCoordinate

            # Create and configure coordinate converter (cached by VTK internally)
            coord = vtkCoordinate()
            coord.SetCoordinateSystemToDisplay()
            coord.SetValue(0, 0, 0)

            # Perform a dummy conversion to initialize VTK internals
            if self.plotter and self.plotter.renderer:
                _ = coord.GetComputedWorldValue(self.plotter.renderer)

            # Cache the vtkCoordinate class reference for faster access later
            self._vtk_coordinate_class = vtkCoordinate

            logger.debug("Picking pipeline pre-warmed successfully")
        except Exception as e:
            logger.debug(f"Could not prewarm picking: {e}")

    def _enable_ground_plane_picking(self):
        """Enable picking on the XY ground plane for element creation."""
        if self.plotter is None:
            return

        # Disable any previous picking first
        try:
            self.plotter.disable_picking()
        except Exception:
            pass

        # Use track_click_position to get screen coordinates
        # Then manually raycast to find intersection with Z=0 plane
        self.plotter.track_click_position(
            callback=self._on_viewport_click,
            side="left",
            double=False
        )

    def _on_viewport_click(self, click_pos):
        """
        Handle left-click in creation mode.
        click_pos is a 3D world position from pick_click_position().
        If clicked on empty space, we project to Z=0 plane.
        """
        if self.plotter is None:
            return

        # Only handle clicks in creation modes
        if self._current_mode == "IDLE":
            return

        # Debounce: prevent double-triggering within 200ms
        import time
        current_time = time.time()
        if hasattr(self, '_last_click_time'):
            if current_time - self._last_click_time < 0.2:
                logger.debug("Click debounced (too fast)")
                return
        self._last_click_time = current_time

        import numpy as np

        logger.info(f"Click position received: {click_pos}")

        # click_pos is (x, y, z) from pick_click_position()
        # If it's a valid 3D point on a mesh, use it
        # If clicking on empty space, click_pos might be (0,0,0) or the camera position

        if click_pos is not None and len(click_pos) >= 3:
            # Check if it's a valid picked point (not at origin or camera)
            cam_pos = np.array(self.plotter.camera.position)
            picked = np.array(click_pos[:3])

            # If picked point is very close to camera, it means nothing was hit
            # In that case, do ray-plane intersection to Z=0
            dist_to_cam = np.linalg.norm(picked - cam_pos)

            if dist_to_cam < 1.0:  # Too close to camera = no hit
                # Do ray-plane intersection
                pt = self._intersect_ray_with_ground_plane()
            else:
                # Valid pick on a mesh - but we want to snap to Z=0 for creation
                # Use the X, Y from pick and Z=0
                pt = Point3D(click_pos[0], click_pos[1], 0.0)
        else:
            pt = self._intersect_ray_with_ground_plane()

        if pt:
            logger.info(f"Final pick point: {pt}")
            self.point_picked.emit(pt)
        else:
            logger.warning("No point could be determined from click")

    def _intersect_ray_with_ground_plane(self) -> Optional[Point3D]:
        """Intersect camera ray through mouse position with Z=0 plane."""
        import numpy as np

        if self.plotter is None:
            return None

        # Get mouse position in display coordinates
        interactor = self.plotter.iren.interactor
        mouse_pos = interactor.GetEventPosition()

        # Use VTK picker to cast ray
        renderer = self.plotter.renderer

        # Use cached vtkCoordinate class if available (from _prewarm_picking)
        vtkCoordinate = getattr(self, '_vtk_coordinate_class', None)
        if vtkCoordinate is None:
            from vtkmodules.vtkRenderingCore import vtkCoordinate

        # Convert display to world (on the near plane)
        coord = vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(mouse_pos[0], mouse_pos[1], 0)
        near_world = np.array(coord.GetComputedWorldValue(renderer))

        coord.SetValue(mouse_pos[0], mouse_pos[1], 1)
        far_world = np.array(coord.GetComputedWorldValue(renderer))

        # Ray direction
        ray_dir = far_world - near_world
        if np.linalg.norm(ray_dir) < 1e-10:
            return None
        ray_dir = ray_dir / np.linalg.norm(ray_dir)

        # Intersect with Z=0 plane
        if abs(ray_dir[2]) < 1e-10:
            logger.warning("Ray parallel to ground plane")
            return None

        t = -near_world[2] / ray_dir[2]
        if t < 0:
            logger.warning("Ground plane behind camera")
            return None

        intersection = near_world + t * ray_dir
        return Point3D(intersection[0], intersection[1], 0.0)

    def _on_point_picked(self, point):
        """Handle point picked during creation (legacy callback)."""
        if point is not None:
            pt = Point3D(point[0], point[1], point[2])
            self.point_picked.emit(pt)

    def cancel_creation(self):
        """Cancel current creation mode."""
        self._creation_mode = None
        if self.plotter:
            self.plotter.disable_picking()

    def update_display(self):
        """Update display with all model elements."""
        if self.plotter is None:
            return

        # Clear existing actors (except grid)
        for elem_id in list(self._actors.keys()):
            self.plotter.remove_actor(str(elem_id))
        self._actors.clear()

        # Add all elements
        for element in self.model.get_all_elements():
            self._add_element_mesh(element)

        # Add structural grids if defined
        self._draw_structural_grids()

        self.plotter.reset_camera()
        self.plotter.render()

    def _add_element_mesh(self, element: StructuralElement):
        """Add element mesh to plotter with fallback for simple geometry."""
        if self.plotter is None:
            return

        elem_type = element.element_type.value
        logger.debug(f"Adding element mesh: {element.id} ({elem_type})")

        try:
            # Try to get mesh from element
            mesh = element.get_mesh()
            if mesh is not None:
                color = self._get_element_color(element)
                actor = self.plotter.add_mesh(
                    mesh,
                    color=color,
                    opacity=1.0,
                    name=str(element.id)
                )
                self._actors[element.id] = actor
                logger.debug(f"Element {element.id} ({elem_type}) added via get_mesh(), actor={actor}")
                # Add part number label
                self._add_part_number_label(element)
                return
        except Exception as e:
            logger.debug(f"Could not get mesh for {element.id} ({elem_type}): {e}")

        # Fallback: create simple representation
        logger.debug(f"Element {element.id} ({elem_type}) falling back to simple representation")
        self._add_simple_element(element)
        # Add part number label for simple elements too
        self._add_part_number_label(element)

    def _add_simple_element(self, element: StructuralElement):
        """Add simple geometric representation for element."""
        import pyvista as pv
        import numpy as np

        elem_type = element.element_type.value
        color = self._get_element_color(element)

        try:
            if elem_type == 'beam':
                # Check if it's a curved beam first
                from src.core.curved_beam import CurvedBeam
                if isinstance(element, CurvedBeam):
                    # Draw curved beam as arc with thickness
                    arc_points = element.get_arc_points()
                    points_array = np.array([[p.x, p.y, p.z] for p in arc_points])

                    # Create spline through points
                    spline = pv.Spline(points_array, len(arc_points) * 2)

                    # Get tube radius from profile
                    radius = 30  # Default
                    if element.profile:
                        radius = max(element.profile.b or 30, element.profile.h or 30) / 2

                    tube = spline.tube(radius=radius)
                    actor = self.plotter.add_mesh(tube, color=color, name=str(element.id))
                    self._actors[element.id] = actor
                    return

                # Draw straight beam as line with thickness
                from src.core.beam import Beam
                if isinstance(element, Beam):
                    start = element.start_point
                    end = element.end_point
                    line = pv.Line(
                        [start.x, start.y, start.z],
                        [end.x, end.y, end.z]
                    )
                    # Get tube radius from profile
                    radius = 50  # Default
                    if element.profile:
                        radius = max(element.profile.b or 50, element.profile.h or 50) / 2

                    tube = line.tube(radius=radius)
                    actor = self.plotter.add_mesh(tube, color=color, name=str(element.id))
                    self._actors[element.id] = actor

            elif elem_type == 'column':
                # Draw column as vertical cylinder/box
                from src.core.column import Column
                if isinstance(element, Column):
                    base = element.base_point
                    # Create box
                    size = 200  # Default size
                    if element.profile:
                        size = max(element.profile.b or 200, element.profile.h or 200)
                    height = element.height
                    logger.debug(f"Creating column box: base={base}, size={size}, height={height}")
                    box = pv.Box(bounds=[
                        base.x - size/2, base.x + size/2,
                        base.y - size/2, base.y + size/2,
                        base.z, base.z + height
                    ])
                    actor = self.plotter.add_mesh(box, color=color, name=str(element.id))
                    self._actors[element.id] = actor
                    logger.debug(f"Column {element.id} added to _actors, actor={actor}")
                else:
                    logger.warning(f"Column element {element.id} failed isinstance check")

            elif elem_type in ('plate', 'slab'):
                # Draw as flat polygon
                if hasattr(element, 'points') and element.points:
                    points = np.array([[p.x, p.y, p.z] for p in element.points])
                    # Create polygon face
                    n_pts = len(points)
                    faces = [n_pts] + list(range(n_pts))
                    poly = pv.PolyData(points, faces=faces)
                    actor = self.plotter.add_mesh(poly, color=color, opacity=0.8, name=str(element.id))
                    self._actors[element.id] = actor

            elif elem_type == 'wall':
                # Draw wall as box
                from src.core.wall import Wall
                if isinstance(element, Wall):
                    sp, ep = element.start_point, element.end_point
                    mid = sp.midpoint_to(ep)
                    # Simple box approximation
                    box = pv.Box(bounds=[
                        min(sp.x, ep.x) - element.thickness/2,
                        max(sp.x, ep.x) + element.thickness/2,
                        min(sp.y, ep.y) - element.thickness/2,
                        max(sp.y, ep.y) + element.thickness/2,
                        sp.z, sp.z + element.height
                    ])
                    actor = self.plotter.add_mesh(box, color=color, name=str(element.id))
                    self._actors[element.id] = actor

            elif elem_type == 'footing':
                # Draw footing as box
                from src.core.footing import Footing
                if isinstance(element, Footing):
                    c = element.center_point
                    box = pv.Box(bounds=[
                        c.x - element.width/2, c.x + element.width/2,
                        c.y - element.length/2, c.y + element.length/2,
                        c.z - element.depth, c.z
                    ])
                    actor = self.plotter.add_mesh(box, color=color, name=str(element.id))
                    self._actors[element.id] = actor
            
            elif elem_type == 'bolt_group':
                # Draw bolts as cylinders
                if hasattr(element, 'get_bolt_positions'):
                    positions = element.get_bolt_positions()
                    if positions:
                        meshes = []
                        dia = getattr(element, 'bolt_diameter', 20.0)
                        # Default Z direction for now
                        for pos in positions:
                            cyl = pv.Cylinder(center=(pos.x, pos.y, pos.z), direction=(0,0,1), radius=dia/2, height=100)
                            meshes.append(cyl)
                        
                        if meshes:
                            # Merge meshes
                            merged = meshes[0]
                            for m in meshes[1:]:
                                merged = merged.merge(m)
                            actor = self.plotter.add_mesh(merged, color='#888888', name=str(element.id))
                            self._actors[element.id] = actor
                            
            elif elem_type == 'weld':
                # Draw weld as small sphere
                pos = getattr(element, 'position', None)
                if pos:
                    sphere = pv.Sphere(radius=15, center=(pos.x, pos.y, pos.z))
                    actor = self.plotter.add_mesh(sphere, color='#ff00ff', name=str(element.id))
                    self._actors[element.id] = actor

        except Exception as e:
            logger.warning(f"Failed to create simple element {element.id}: {e}")

    def _draw_structural_grids(self):
        """Draw structural grid lines."""
        if self.plotter is None:
            return

        import pyvista as pv
        import numpy as np

        grids = getattr(self.model, '_grids', None)
        if not grids:
            return

        # Get model extent for grid lines
        min_pt, max_pt = self.model.get_bounding_box()
        extend = 2000  # Extend 2m beyond model

        x_min = min_pt.x - extend
        x_max = max_pt.x + extend
        y_min = min_pt.y - extend
        y_max = max_pt.y + extend
        z_max = max_pt.z + extend

        # Draw X grids (vertical planes perpendicular to X)
        for grid in grids.get('x_grids', []):
            x = grid.get('position', 0)
            name = grid.get('name', '')
            # Create line from y_min to y_max at this X
            line = pv.Line([x, y_min, 0], [x, y_max, 0])
            self.plotter.add_mesh(line, color='#6060ff', line_width=2, name=f'grid_x_{name}')

            # Add label
            self.plotter.add_point_labels(
                [[x, y_min - 500, 0]],
                [name],
                font_size=12,
                text_color='#6060ff',
                name=f'label_x_{name}'
            )

        # Draw Y grids
        for grid in grids.get('y_grids', []):
            y = grid.get('position', 0)
            name = grid.get('name', '')
            line = pv.Line([x_min, y, 0], [x_max, y, 0])
            self.plotter.add_mesh(line, color='#ff6060', line_width=2, name=f'grid_y_{name}')

            # Add label
            self.plotter.add_point_labels(
                [[x_min - 500, y, 0]],
                [name],
                font_size=12,
                text_color='#ff6060',
                name=f'label_y_{name}'
            )

    def highlight_element(self, element_id: UUID, highlight: bool = True):
        """Highlight or unhighlight an element."""
        if self.plotter is None:
            return

        if element_id in self._actors:
            element = self.model.get_element(element_id)
            if element:
                color = '#ffff00' if highlight else self._get_element_color(element)
                # Re-add mesh with new color
                self._on_element_modified(element)

    def screenshot(self, filename: str):
        """Save viewport screenshot."""
        if self.plotter:
            self.plotter.screenshot(filename)

    # ========================
    # Alt+Drag Selection
    # ========================

    def _abort_vtk_event(self, obj):
        """Safely abort a VTK event to prevent default handling."""
        try:
            if obj and hasattr(obj, 'SetAbortFlag'):
                obj.SetAbortFlag(1)
                return True
        except Exception as e:
            logger.debug(f"Could not abort VTK event: {e}")
        return False

    def _install_selection_interactor(self):
        """Install keyboard event handlers.

        NOTE: Mouse interaction is now handled at the Qt level by
        SelectionQtInteractor (see top of file). This method only sets up
        keyboard event observers for shortcuts (M, G, E keys).

        The Qt-level approach is necessary because PyVista's
        QVTKRenderWindowInteractor.mouseMoveEvent() unconditionally sends
        all mouse events to VTK, bypassing any VTK interactor style overrides.
        """
        if self.plotter is None:
            return

        try:
            interactor = self.plotter.iren.interactor

            # Keep key observers for keyboard shortcuts
            interactor.AddObserver("KeyPressEvent", self._on_key_press)
            interactor.AddObserver("KeyReleaseEvent", self._on_key_release)

            logger.info("Selection interactor installed - Left: select/box, Ctrl+Right: rotate")
        except Exception as e:
            logger.warning(f"Could not install selection interactor: {e}")

    def _on_key_press(self, obj, event):
        """Handle key press for modifier keys and shortcuts.

        Modifier keys:
        - Ctrl: Multi-select mode, Ctrl+Middle for rotation
        - Alt: Reserved for future use

        Shortcuts:
        - M: Toggle start/end markers
        - G: Toggle grid snap
        - E: Toggle endpoint snap
        """
        try:
            key = obj.GetKeySym()
            if key in ("Alt_L", "Alt_R", "Alt"):
                self._alt_pressed = True
            elif key in ("Control_L", "Control_R", "Control"):
                self._ctrl_pressed = True
                logger.debug("Ctrl pressed - multi-select / rotate mode")
            elif key in ("m", "M"):
                # Toggle start/end markers visibility
                self.toggle_start_end_markers()
            elif key in ("g", "G"):
                # Toggle grid snap
                if self.interaction_manager:
                    self.interaction_manager.toggle_grid_snap()
            elif key in ("e", "E"):
                # Toggle endpoint snap
                if self.interaction_manager:
                    self.interaction_manager.toggle_endpoint_snap()
        except Exception:
            pass

    def _on_key_release(self, obj, event):
        """Handle key release for modifier keys."""
        try:
            key = obj.GetKeySym()
            if key in ("Alt_L", "Alt_R", "Alt"):
                self._alt_pressed = False
            elif key in ("Control_L", "Control_R", "Control"):
                self._ctrl_pressed = False
                logger.debug("Ctrl released")
        except Exception:
            pass

    # NOTE: _on_left_button_press, _on_left_button_release, and _on_mouse_move
    # have been removed. All mouse interaction logic is now handled in the
    # SelectionInteractorStyle class (see _install_selection_interactor).
    # This is necessary because VTK processes interactor style methods BEFORE
    # observers, so using observers for mouse handling doesn't work properly.

    def _do_element_pick(self, screen_x: int, screen_y: int):
        """Perform element picking at screen coordinates.

        Finds the element under the cursor and updates selection.
        Ctrl+click adds to selection, regular click replaces selection.

        IMPORTANT: Qt uses Y=0 at top of widget, VTK uses Y=0 at bottom.
        We must convert Qt screen coordinates to VTK display coordinates.
        """
        if self.plotter is None:
            return

        import numpy as np
        from vtkmodules.vtkRenderingCore import vtkCellPicker

        try:
            # Create a cell picker for accurate element picking
            picker = vtkCellPicker()
            picker.SetTolerance(0.005)

            # CRITICAL: Convert Qt Y coordinate (Y=0 at top) to VTK display coordinate (Y=0 at bottom)
            widget_height = self.plotter.interactor.height()
            vtk_y = widget_height - screen_y - 1

            # Pick at screen coordinates (using VTK coordinate system)
            renderer = self.plotter.renderer
            picker.Pick(screen_x, vtk_y, 0, renderer)

            # Get picked position
            picked_pos = picker.GetPickPosition()
            picked_actor = picker.GetActor()

            # Debug: log pick result and actor count
            logger.debug(f"Pick at ({screen_x}, {screen_y}): actor={picked_actor is not None}, pos={picked_pos}, actors_count={len(self._actors)}")

            if picked_actor is None:
                # Clicked on empty space - clear selection (unless Ctrl held)
                if not self._ctrl_pressed:
                    logger.info("Clicked empty space - clearing selection")
                    self.model.clear_selection()
                return

            # Find which element this actor belongs to
            picked_pt = np.array(picked_pos[:3])
            closest_elem_id = None
            min_distance = float('inf')

            # Get the mapper from the picked actor for reliable comparison
            # PyVista actors wrap VTK actors, but the picker returns the underlying
            # VTK actor. Comparing mappers is reliable because each mesh has a unique mapper.
            picked_mapper = picked_actor.GetMapper() if picked_actor else None
            logger.debug(f"Picked actor mapper: {picked_mapper}")

            for elem_id, actor in self._actors.items():
                # Get element type for debugging
                element = self.model.get_element(elem_id)
                elem_type = element.element_type.value if element else "unknown"

                # Compare mappers instead of actor references
                # This reliably matches PyVista actors with VTK picker results
                if picked_mapper is not None and hasattr(actor, 'GetMapper'):
                    actor_mapper = actor.GetMapper()
                    logger.debug(f"Checking element {elem_id} ({elem_type}): mapper={actor_mapper}")
                    if actor_mapper is not None and actor_mapper is picked_mapper:
                        closest_elem_id = elem_id
                        logger.debug(f"Actor matched by mapper for element {elem_id} ({elem_type})")
                        break

            # Fallback: if mapper comparison didn't find a match, use bounds-based matching
            if closest_elem_id is None:
                logger.debug("Mapper comparison failed, trying bounds-based matching")
                for elem_id, actor in self._actors.items():
                    if hasattr(actor, 'GetBounds'):
                        bounds = actor.GetBounds()
                        center = np.array([
                            (bounds[0] + bounds[1]) / 2,
                            (bounds[2] + bounds[3]) / 2,
                            (bounds[4] + bounds[5]) / 2
                        ])
                        dist = np.linalg.norm(picked_pt - center)

                        margin = 500
                        in_bounds = (bounds[0] - margin <= picked_pt[0] <= bounds[1] + margin and
                                     bounds[2] - margin <= picked_pt[1] <= bounds[3] + margin and
                                     bounds[4] - margin <= picked_pt[2] <= bounds[5] + margin)

                        element = self.model.get_element(elem_id)
                        elem_type = element.element_type.value if element else "unknown"
                        logger.debug(f"Bounds check {elem_id} ({elem_type}): bounds={bounds}, in_bounds={in_bounds}, dist={dist:.1f}")

                        if in_bounds and dist < min_distance:
                            min_distance = dist
                            closest_elem_id = elem_id

            if closest_elem_id:
                if self._ctrl_pressed:
                    # Toggle selection
                    if closest_elem_id in self._selected_ids:
                        logger.info(f"Ctrl+click deselect: {closest_elem_id}")
                        self.model.deselect_element(closest_elem_id)
                    else:
                        logger.info(f"Ctrl+click add: {closest_elem_id}")
                        self.model.select_element(closest_elem_id, add_to_selection=True)
                else:
                    # Replace selection
                    logger.info(f"Selected element: {closest_elem_id}")
                    self.model.select_element(closest_elem_id, add_to_selection=False)
                self.element_selected.emit(closest_elem_id)
            else:
                # Clicked on non-element (e.g., grid)
                if not self._ctrl_pressed:
                    logger.info("Clicked non-element - clearing selection")
                    self.model.clear_selection()

        except Exception as e:
            logger.debug(f"Error in element pick: {e}")

    def _update_snap_indicator_at_mouse(self, screen_x: int, screen_y: int):
        """Update snap indicator based on current mouse position in creation mode.

        Projects screen coordinates to ground plane and finds nearest snap point.
        """
        if self.plotter is None or self.interaction_manager is None:
            return

        import numpy as np

        try:
            # Project screen to world (Z=0 plane)
            renderer = self.plotter.renderer
            vtkCoordinate = getattr(self, '_vtk_coordinate_class', None)
            if vtkCoordinate is None:
                from vtkmodules.vtkRenderingCore import vtkCoordinate

            # Convert display to world using ray intersection with Z=0
            coord = vtkCoordinate()
            coord.SetCoordinateSystemToDisplay()
            coord.SetValue(screen_x, screen_y, 0)
            near_world = np.array(coord.GetComputedWorldValue(renderer))

            coord.SetValue(screen_x, screen_y, 1)
            far_world = np.array(coord.GetComputedWorldValue(renderer))

            # Ray direction
            ray_dir = far_world - near_world
            if np.linalg.norm(ray_dir) < 1e-10:
                self.hide_snap_indicator()
                return
            ray_dir = ray_dir / np.linalg.norm(ray_dir)

            # Intersect with Z=0 plane
            if abs(ray_dir[2]) < 1e-10:
                self.hide_snap_indicator()
                return

            t = -near_world[2] / ray_dir[2]
            if t < 0:
                self.hide_snap_indicator()
                return

            intersection = near_world + t * ray_dir
            mouse_point = Point3D(intersection[0], intersection[1], 0.0)

            # Get snap manager from interaction_manager
            snap_manager = getattr(self.interaction_manager, 'snap_manager', None)
            if snap_manager is None:
                self.hide_snap_indicator()
                return

            # Find nearest snap point
            snap_point, snap_type = snap_manager.find_nearest_snap(mouse_point)

            if snap_point and snap_type:
                self.show_snap_indicator(snap_point, snap_type)
            else:
                self.hide_snap_indicator()
                # Update status with current mouse coordinates (no snap)
                coord_str = f"X: {mouse_point.x:.0f} Y: {mouse_point.y:.0f} Z: {mouse_point.z:.0f}"
                self.snap_feedback.emit(coord_str)

        except Exception as e:
            logger.debug(f"Error updating snap indicator: {e}")
            self.hide_snap_indicator()

    def _draw_selection_rect(self, x: int, y: int):
        """Draw rubber band selection rectangle as a 2D screen overlay.

        This draws directly on the screen in 2D, so the rectangle stays aligned
        with the viewport regardless of camera rotation. This is the correct
        CAD-like behavior for selection rectangles.

        Uses distinct colors based on selection direction:
        - Blue (#3399ff) for window selection (left-to-right): only fully enclosed elements
        - Green (#33ff33) for crossing selection (right-to-left): any intersecting elements
        """
        if self._selection_start is None or self.plotter is None:
            return

        # Clear previous rectangle
        self._clear_selection_rect()

        x1, y1 = self._selection_start
        x2, y2 = x, y

        # Determine selection type based on drag direction
        # Left-to-right = window selection (blue), Right-to-left = crossing selection (green)
        is_window_selection = x2 >= x1

        # Store selection type for use in finish_selection_box
        self._is_window_selection = is_window_selection

        # Color based on selection type (RGB 0-1 range for VTK)
        if is_window_selection:
            rect_color = (0.2, 0.6, 1.0)  # Blue for window selection
        else:
            rect_color = (0.2, 1.0, 0.2)  # Green for crossing selection

        try:
            from vtkmodules.vtkRenderingCore import vtkActor2D, vtkPolyDataMapper2D, vtkCoordinate
            from vtkmodules.vtkCommonDataModel import vtkPolyData
            from vtkmodules.vtkCommonCore import vtkPoints, vtkFloatArray
            from vtkmodules.vtkFiltersCore import vtkAppendPolyData
            import vtk

            # Convert Qt Y coordinates (Y=0 at top) to VTK display coordinates (Y=0 at bottom)
            widget_height = self.plotter.interactor.height()
            y1_vtk = widget_height - y1
            y2_vtk = widget_height - y2

            # Create points for rectangle corners in display coordinates
            points = vtkPoints()
            points.InsertNextPoint(x1, y1_vtk, 0)  # Bottom-left (in VTK coords)
            points.InsertNextPoint(x2, y1_vtk, 0)  # Bottom-right
            points.InsertNextPoint(x2, y2_vtk, 0)  # Top-right
            points.InsertNextPoint(x1, y2_vtk, 0)  # Top-left

            # Create lines connecting the corners (closed rectangle)
            lines = vtk.vtkCellArray()
            # Line 0-1
            lines.InsertNextCell(2)
            lines.InsertCellPoint(0)
            lines.InsertCellPoint(1)
            # Line 1-2
            lines.InsertNextCell(2)
            lines.InsertCellPoint(1)
            lines.InsertCellPoint(2)
            # Line 2-3
            lines.InsertNextCell(2)
            lines.InsertCellPoint(2)
            lines.InsertCellPoint(3)
            # Line 3-0 (close the rectangle)
            lines.InsertNextCell(2)
            lines.InsertCellPoint(3)
            lines.InsertCellPoint(0)

            # Create polydata for the rectangle outline
            poly_data = vtkPolyData()
            poly_data.SetPoints(points)
            poly_data.SetLines(lines)

            # Set up coordinate system for 2D display
            coord = vtkCoordinate()
            coord.SetCoordinateSystemToDisplay()

            # Create mapper for 2D rendering
            mapper = vtkPolyDataMapper2D()
            mapper.SetInputData(poly_data)
            mapper.SetTransformCoordinate(coord)

            # Create 2D actor
            actor = vtkActor2D()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(rect_color[0], rect_color[1], rect_color[2])
            actor.GetProperty().SetLineWidth(2.0)

            # Add to renderer (not plotter.add_mesh, which is for 3D)
            renderer = self.plotter.renderer
            renderer.AddActor2D(actor)

            # Store reference for cleanup
            self._selection_rect_actor = actor

            self.plotter.render()

        except Exception as e:
            logger.debug(f"Could not draw selection rect: {e}")

    def start_selection_box(self, x: int, y: int):
        """Start drawing selection box from screen position."""
        self._selection_start = (x, y)
        logger.debug(f"Selection box started at ({x}, {y})")

    def update_selection_box(self, x: int, y: int):
        """Update selection box to current mouse position."""
        if self._selection_start is None:
            return
        self._draw_selection_rect(x, y)

    def finish_selection_box(self, x: int, y: int):
        """Finish selection box and select elements within.

        Selection behavior depends on drag direction:
        - Window selection (left-to-right): selects only elements fully enclosed
        - Crossing selection (right-to-left): selects elements that intersect the box
        """
        if self._selection_start is None:
            return

        import numpy as np

        x1, y1 = self._selection_start
        x2, y2 = x, y

        # CRITICAL: Convert Qt coordinates (Y=0 at top) to VTK coordinates (Y=0 at bottom)
        # VTK's GetComputedDisplayValue returns Y with 0 at bottom of viewport
        widget_height = self.plotter.interactor.height()
        y1_vtk = widget_height - y1
        y2_vtk = widget_height - y2

        # Normalize bounds (using VTK coordinates now)
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1_vtk, y2_vtk), max(y1_vtk, y2_vtk)

        # Only proceed if we have a meaningful selection area
        if (max_x - min_x) < 5 and (max_y - min_y) < 5:
            logger.debug("Selection area too small, ignoring")
            self._selection_start = None
            self._is_window_selection = True
            self._clear_selection_rect()
            return

        # Get selection type (set during _draw_selection_rect)
        is_window_selection = getattr(self, '_is_window_selection', True)
        selection_type = "window" if is_window_selection else "crossing"

        # Find elements based on selection type
        selected_ids = []
        renderer = self.plotter.renderer

        from vtkmodules.vtkRenderingCore import vtkCoordinate

        for elem_id, actor in self._actors.items():
            try:
                if not hasattr(actor, 'GetBounds'):
                    continue

                # Get actor bounding box corners for accurate selection
                bounds = actor.GetBounds()  # (xmin, xmax, ymin, ymax, zmin, zmax)

                # Project all 8 corners of the 3D bounding box to screen space
                corners_3d = [
                    (bounds[0], bounds[2], bounds[4]),  # min x, min y, min z
                    (bounds[1], bounds[2], bounds[4]),  # max x, min y, min z
                    (bounds[0], bounds[3], bounds[4]),  # min x, max y, min z
                    (bounds[1], bounds[3], bounds[4]),  # max x, max y, min z
                    (bounds[0], bounds[2], bounds[5]),  # min x, min y, max z
                    (bounds[1], bounds[2], bounds[5]),  # max x, min y, max z
                    (bounds[0], bounds[3], bounds[5]),  # min x, max y, max z
                    (bounds[1], bounds[3], bounds[5]),  # max x, max y, max z
                ]

                screen_coords = []
                for cx, cy, cz in corners_3d:
                    coord = vtkCoordinate()
                    coord.SetCoordinateSystemToWorld()
                    coord.SetValue(cx, cy, cz)
                    screen_pos = coord.GetComputedDisplayValue(renderer)
                    screen_coords.append(screen_pos)

                # Get screen-space bounding box of element
                elem_min_x = min(p[0] for p in screen_coords)
                elem_max_x = max(p[0] for p in screen_coords)
                elem_min_y = min(p[1] for p in screen_coords)
                elem_max_y = max(p[1] for p in screen_coords)

                if is_window_selection:
                    # Window selection: element must be fully enclosed
                    fully_inside = (elem_min_x >= min_x and elem_max_x <= max_x and
                                    elem_min_y >= min_y and elem_max_y <= max_y)
                    if fully_inside:
                        selected_ids.append(elem_id)
                else:
                    # Crossing selection: element just needs to intersect
                    intersects = not (elem_max_x < min_x or elem_min_x > max_x or
                                      elem_max_y < min_y or elem_min_y > max_y)
                    if intersects:
                        selected_ids.append(elem_id)

            except Exception as e:
                logger.debug(f"Could not check element {elem_id}: {e}")

        # Update model selection
        if selected_ids:
            # Clear current selection first, then add all box-selected elements
            self.model.clear_selection()
            for eid in selected_ids:
                self.model.select_element(eid, add_to_selection=True)
            logger.info(f"{selection_type.title()} selected {len(selected_ids)} elements")

        self._selection_start = None
        self._is_window_selection = True
        self._clear_selection_rect()

    def _clear_selection_rect(self):
        """Clear selection rectangle indicator.

        The selection rectangle is a 2D actor added directly to the renderer,
        not a 3D mesh added via plotter.add_mesh(), so we must use
        renderer.RemoveActor2D() instead of plotter.remove_actor().
        """
        if self._selection_rect_actor and self.plotter:
            try:
                # Remove 2D actor from renderer (not plotter)
                renderer = self.plotter.renderer
                renderer.RemoveActor2D(self._selection_rect_actor)
                self.plotter.render()
            except Exception:
                pass
            self._selection_rect_actor = None

    # ========================
    # Context Menu
    # ========================

    def _show_context_menu(self, global_pos):
        """Show context menu at the given global position.

        Provides quick access to common operations:
        - Copy (Ctrl+C)
        - Paste (Ctrl+V)
        - Delete (Del)
        - Select All (Ctrl+A)
        """
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction

        menu = QMenu(self)

        # Get selected elements count for context
        selected_count = len(self._selected_ids)
        has_selection = selected_count > 0

        # Copy action
        copy_action = QAction(f"Copy ({selected_count} selected)" if has_selection else "Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(has_selection)
        copy_action.triggered.connect(self._context_copy)
        menu.addAction(copy_action)

        # Paste action
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self._context_paste)
        menu.addAction(paste_action)

        menu.addSeparator()

        # Delete action
        delete_action = QAction(f"Delete ({selected_count} selected)" if has_selection else "Delete", self)
        delete_action.setShortcut("Del")
        delete_action.setEnabled(has_selection)
        delete_action.triggered.connect(self._context_delete)
        menu.addAction(delete_action)

        menu.addSeparator()

        # Select All action
        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self._context_select_all)
        menu.addAction(select_all_action)

        # Deselect All action
        deselect_action = QAction("Deselect All", self)
        deselect_action.setShortcut("Esc")
        deselect_action.setEnabled(has_selection)
        deselect_action.triggered.connect(self._context_deselect_all)
        menu.addAction(deselect_action)

        menu.exec(global_pos)

    def _context_copy(self):
        """Handle Copy from context menu."""
        if self._selected_ids:
            # Emit signal to trigger copy mode in main window
            self.copy_requested.emit()
            logger.info(f"Copy requested for {len(self._selected_ids)} elements")

    def _context_paste(self):
        """Handle Paste from context menu."""
        # Emit signal to trigger paste in main window
        self.paste_requested.emit()
        logger.info("Paste requested")

    def _context_delete(self):
        """Handle Delete from context menu."""
        if self._selected_ids:
            # Emit signal to trigger delete in main window
            self.delete_requested.emit()
            logger.info(f"Delete requested for {len(self._selected_ids)} elements")

    def _context_select_all(self):
        """Handle Select All from context menu."""
        # Select all elements in the model
        for elem_id in self._actors.keys():
            self.model.select_element(elem_id, add_to_selection=True)
        logger.info(f"Selected all {len(self._actors)} elements")

    def _context_deselect_all(self):
        """Handle Deselect All from context menu."""
        self.model.clear_selection()
        logger.info("Deselected all elements")

    # ========================
    # Snap Indicator
    # ========================

    # Snap type color mapping
    SNAP_COLORS = {
        "grid": '#ffff00',      # Yellow for grid intersections
        "endpoint": '#00ffff',   # Cyan for element endpoints
        "midpoint": '#ff00ff',   # Magenta for midpoints
        "default": '#00ff00',    # Green fallback
    }

    # Start/End point marker colors (Tekla standard)
    START_POINT_COLOR = '#ffff00'   # Yellow for start
    END_POINT_COLOR = '#ff00ff'     # Magenta for end
    MARKER_RADIUS = 75              # Sphere radius in mm

    def show_snap_indicator(self, point: Point3D, snap_type: str = "grid"):
        """Show snap indicator at point.

        Args:
            point: The Point3D location to show the indicator
            snap_type: Type of snap - "grid", "endpoint", "midpoint"
                       Different types display different colors:
                       - grid: yellow
                       - endpoint: cyan
                       - midpoint: magenta
        """
        if self.plotter is None:
            return

        import pyvista as pv

        self.hide_snap_indicator()

        try:
            # Create small sphere at snap point
            sphere = pv.Sphere(radius=100, center=[point.x, point.y, point.z])

            # Get color based on snap type
            color = self.SNAP_COLORS.get(snap_type, self.SNAP_COLORS["default"])

            self._snap_indicator_actor = self.plotter.add_mesh(
                sphere,
                color=color,
                opacity=0.8,
                name='snap_indicator'
            )
            self.plotter.render()

            # Emit feedback signal for status bar with coordinates
            coord_str = f"X: {point.x:.0f} Y: {point.y:.0f} Z: {point.z:.0f}"
            self.snap_feedback.emit(f"Snap: {snap_type} | {coord_str}")

        except Exception as e:
            logger.debug(f"Could not show snap indicator: {e}")

    def hide_snap_indicator(self):
        """Hide snap indicator and clear status."""
        if self._snap_indicator_actor and self.plotter:
            try:
                self.plotter.remove_actor('snap_indicator')
            except Exception:
                pass
            self._snap_indicator_actor = None

    # ========================
    # Copy/Move Preview
    # ========================

    def show_copy_preview(self, elements: List[UUID], displacement: Vector3D):
        """Show ghost preview of elements at new position.

        This method provides visual feedback during copy/move operations by
        showing a semi-transparent preview of where elements will be placed.

        Args:
            elements: List of element UUIDs to show preview for
            displacement: Vector3D representing the offset from original position

        Note:
            For now, this is a placeholder implementation that highlights
            selected elements. Future enhancement could render ghost meshes
            at the displaced position.
        """
        if self.plotter is None:
            return

        # For now, just highlight selected elements
        # This could be enhanced to show semi-transparent ghost meshes at new position
        for elem_id in elements:
            if elem_id in self._actors:
                element = self.model.get_element(elem_id)
                if element:
                    # Highlight element to show it's being copied/moved
                    try:
                        actor = self._actors[elem_id]
                        prop = actor.GetProperty()
                        # Cyan highlight for copy/move preview
                        prop.SetColor(0.0, 1.0, 1.0)
                    except Exception as e:
                        logger.debug(f"Could not highlight element {elem_id}: {e}")

        self.refresh()
        logger.debug(f"Copy preview shown for {len(elements)} elements with displacement {displacement}")

    def hide_copy_preview(self):
        """Hide copy/move preview and restore element colors.

        Resets all selected elements to their normal selection color.
        """
        if self.plotter is None:
            return

        # Restore colors for all selected elements
        for elem_id in self._selected_ids:
            if elem_id in self._actors:
                element = self.model.get_element(elem_id)
                if element:
                    try:
                        actor = self._actors[elem_id]
                        prop = actor.GetProperty()
                        # Restore to selection color (yellow)
                        prop.SetColor(1.0, 1.0, 0.0)
                    except Exception as e:
                        logger.debug(f"Could not restore element {elem_id} color: {e}")

        self.refresh()
        logger.debug("Copy preview hidden")

    # ========================
    # Start/End Point Markers
    # ========================

    def show_start_end_markers(self, element_id: UUID):
        """Show start and end point markers for an element.

        Creates yellow sphere at start point and magenta sphere at end point.
        Uses get_actual_start_point() and get_actual_end_point() if available,
        otherwise falls back to start_point and end_point attributes.

        Args:
            element_id: UUID of the element to show markers for
        """
        if self.plotter is None or not self._show_start_end_markers:
            return

        # Don't duplicate markers
        if element_id in self._start_end_markers:
            return

        element = self.model.get_element(element_id)
        if element is None:
            return

        import pyvista as pv

        try:
            # Get start point - prefer get_actual_start_point() if available
            start_point = None
            if hasattr(element, 'get_actual_start_point'):
                start_point = element.get_actual_start_point()
            elif hasattr(element, 'start_point'):
                start_point = element.start_point

            # Get end point - prefer get_actual_end_point() if available
            end_point = None
            if hasattr(element, 'get_actual_end_point'):
                end_point = element.get_actual_end_point()
            elif hasattr(element, 'end_point'):
                end_point = element.end_point

            start_actor = None
            end_actor = None

            # Create start point marker (yellow sphere)
            if start_point is not None:
                start_sphere = pv.Sphere(
                    radius=self.MARKER_RADIUS,
                    center=[start_point.x, start_point.y, start_point.z]
                )
                start_actor = self.plotter.add_mesh(
                    start_sphere,
                    color=self.START_POINT_COLOR,
                    opacity=0.9,
                    name=f'start_marker_{element_id}'
                )

            # Create end point marker (magenta sphere)
            if end_point is not None:
                end_sphere = pv.Sphere(
                    radius=self.MARKER_RADIUS,
                    center=[end_point.x, end_point.y, end_point.z]
                )
                end_actor = self.plotter.add_mesh(
                    end_sphere,
                    color=self.END_POINT_COLOR,
                    opacity=0.9,
                    name=f'end_marker_{element_id}'
                )

            # Store marker references
            if start_actor or end_actor:
                self._start_end_markers[element_id] = (start_actor, end_actor)
                self.plotter.render()
                logger.debug(f"Start/End markers shown for element {element_id}")

        except Exception as e:
            logger.debug(f"Could not show start/end markers for {element_id}: {e}")

    def hide_start_end_markers(self, element_id: Optional[UUID] = None):
        """Hide start and end point markers.

        Args:
            element_id: UUID of specific element to hide markers for.
                       If None, hides all start/end markers.
        """
        if self.plotter is None:
            return

        if element_id is not None:
            # Hide markers for specific element
            if element_id in self._start_end_markers:
                try:
                    self.plotter.remove_actor(f'start_marker_{element_id}')
                except Exception:
                    pass
                try:
                    self.plotter.remove_actor(f'end_marker_{element_id}')
                except Exception:
                    pass
                del self._start_end_markers[element_id]
                self.plotter.render()
                logger.debug(f"Start/End markers hidden for element {element_id}")
        else:
            # Hide all markers
            for eid in list(self._start_end_markers.keys()):
                try:
                    self.plotter.remove_actor(f'start_marker_{eid}')
                except Exception:
                    pass
                try:
                    self.plotter.remove_actor(f'end_marker_{eid}')
                except Exception:
                    pass
            self._start_end_markers.clear()
            self.plotter.render()
            logger.debug("All start/end markers hidden")

    def toggle_start_end_markers(self):
        """Toggle visibility of start/end point markers.

        When toggled on, shows markers for currently selected elements.
        When toggled off, hides all markers.
        """
        self._show_start_end_markers = not self._show_start_end_markers

        if self._show_start_end_markers:
            # Show markers for selected elements
            for elem_id in self._selected_ids:
                self.show_start_end_markers(elem_id)
            logger.info("Start/End markers enabled")
        else:
            # Hide all markers
            self.hide_start_end_markers()
            logger.info("Start/End markers disabled")

    # ========================
    # Part Number Labels
    # ========================

    def _add_part_number_label(self, element):
        """Add part number label near element centroid."""
        if self.plotter is None or not element.part_number:
            return

        try:
            import numpy as np

            # Get element bounding box to find label position
            min_pt, max_pt = element.get_bounding_box()

            # Position label at center-top of bounding box
            label_pos = np.array([
                (min_pt.x + max_pt.x) / 2,
                (min_pt.y + max_pt.y) / 2,
                max_pt.z + 150  # 150mm above element
            ])

            self.plotter.add_point_labels(
                [label_pos],
                [element.part_number],
                font_size=10,
                text_color='white',
                shape_color='#333333',
                shape_opacity=0.7,
                name=f'label_{element.id}'
            )
        except Exception as e:
            logger.debug(f"Could not add part number label for {element.id}: {e}")
