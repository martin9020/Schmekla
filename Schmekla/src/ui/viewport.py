"""
3D Viewport for Schmekla.

PyVista-based 3D visualization widget.
"""

from typing import Dict, Set, Optional
from uuid import UUID
from loguru import logger

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from src.core.model import StructuralModel
from src.core.element import StructuralElement
from src.geometry.point import Point3D


class Viewport3D(QWidget):
    """
    3D viewport for model visualization.

    Uses PyVista/VTK for rendering.
    """

    # Signals
    element_selected = Signal(object)
    point_picked = Signal(object)
    selection_changed = Signal(list)

    def __init__(self, model: StructuralModel, interaction_manager=None, parent=None):
        super().__init__(parent)

        self.model = model
        self.interaction_manager = interaction_manager
        self._actors: Dict[UUID, object] = {}
        self._selected_ids: Set[UUID] = set()
        self._creation_mode: Optional[str] = None

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
            from pyvistaqt import QtInteractor

            # Create PyVista Qt interactor
            self.plotter = QtInteractor(self)
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
        - CREATE_*: Enable ground plane picking for point placement
        """
        if self.plotter is None:
            return

        self._current_mode = mode_name
        logger.info(f"Viewport mode changed to: {mode_name}")

        if mode_name == "IDLE":
            # Disable creation picking, enable selection picking
            try:
                self.plotter.disable_picking()
            except Exception:
                pass
            # Enable element selection on click
            self._enable_selection_picking()
        else:
            # Creation modes - enable ground plane picking
            self._enable_ground_plane_picking()

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
            logger.info(f"Element selected: {closest_elem_id}")
            # Update model selection (this will trigger highlight via signal)
            self.model.select_element(closest_elem_id, add_to_selection=False)
            self.element_selected.emit(closest_elem_id)
        else:
            # Clicked on grid or unknown - clear selection
            logger.info("Clicked non-element - clearing selection")
            self.model.clear_selection()

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
                return
        except Exception as e:
            logger.debug(f"Could not get mesh for {element.id}: {e}")

        # Fallback: create simple representation
        self._add_simple_element(element)

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
                    box = pv.Box(bounds=[
                        base.x - size/2, base.x + size/2,
                        base.y - size/2, base.y + size/2,
                        base.z, base.z + element.height
                    ])
                    actor = self.plotter.add_mesh(box, color=color, name=str(element.id))
                    self._actors[element.id] = actor

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

