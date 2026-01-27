"""
Main application window for Schmekla.

The primary window containing all UI components.
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QToolBar, QStatusBar, QMenuBar,
    QMenu, QFileDialog, QMessageBox, QLabel,
    QSplitter, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon, QShortcut

from src.core.model import StructuralModel
from src.utils.config import Config

# Pre-import frequently used modules to avoid lazy import delays
# These imports are used during interactive element creation (B, C, P keys)
from src.ui.interaction import InteractionManager, InteractionMode
from src.core.beam import Beam
from src.core.column import Column
from src.core.plate import Plate
from src.core.profile import Profile, ProfileCatalog
from src.core.material import Material, MaterialCatalog
from src.geometry.point import Point3D


class MainWindow(QMainWindow):
    """
    Main application window.

    Contains the 3D viewport, model tree, properties panel,
    and Claude terminal.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize model
        self.model = StructuralModel()
        self.config = Config.load()

        # Pre-load catalogs at startup to avoid delay on first element creation
        # This happens once during app init instead of on first B/C/P key press
        ProfileCatalog.get_instance().load_catalog()
        MaterialCatalog.get_instance().load_catalog()

        # Initialize Snap Manager
        from src.core.snap_manager import SnapManager
        self.snap_manager = SnapManager(self.model)

        # Initialize Interaction Manager with snap manager (already imported at module level)
        self.interaction_manager = InteractionManager(snap_manager=self.snap_manager)
        self.interaction_manager.prompt_changed.connect(self._on_prompt_changed)
        self.interaction_manager.element_created.connect(self._on_element_created_request)
        self.interaction_manager.copy_requested.connect(self._on_copy_requested)
        self.interaction_manager.move_requested.connect(self._on_move_requested)

        # Set window properties
        self.setWindowTitle("Schmekla - Structural Modeler")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 900)

        # Setup UI components
        self._setup_central_widget()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_docks()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._connect_signals()
        self._load_style()

        logger.info("MainWindow initialized")

    def _setup_central_widget(self):
        """Setup the central viewport widget."""
        # Try to import and use PyVista viewport
        try:
            from src.ui.viewport import Viewport3D
            self.viewport = Viewport3D(self.model, self.interaction_manager, self)
            self.setCentralWidget(self.viewport)
            logger.info("3D Viewport created with PyVista")
        except ImportError as e:
            logger.warning(f"Could not create 3D viewport: {e}")
            # Fallback to placeholder
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel("3D Viewport\n\n(Install PyVista for 3D rendering)")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 18px;")
            layout.addWidget(label)
            self.setCentralWidget(placeholder)
            self.viewport = None

    def _setup_menus(self):
        """Create menu bar and menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._create_action(
            "New", self.new_model, QKeySequence.New
        ))
        file_menu.addAction(self._create_action(
            "Open...", self.open_model, QKeySequence.Open
        ))
        file_menu.addAction(self._create_action(
            "Save", self.save_model, QKeySequence.Save
        ))
        file_menu.addAction(self._create_action(
            "Save As...", self.save_model_as, QKeySequence.SaveAs
        ))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action(
            "Export IFC...", self.export_ifc, "Ctrl+E"
        ))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action(
            "Exit", self.close, QKeySequence.Quit
        ))

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._create_action(
            "Undo", self.undo, QKeySequence.Undo
        ))
        edit_menu.addAction(self._create_action(
            "Redo", self.redo, QKeySequence.Redo
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self._create_action(
            "Select All", self.select_all, QKeySequence.SelectAll
        ))
        edit_menu.addAction(self._create_action(
            "Delete", self.delete_selected, QKeySequence.Delete
        ))
        edit_menu.addSeparator()
        edit_menu.addAction(self._create_action(
            "Copy", self.copy_selected, "Ctrl+Shift+C"
        ))
        edit_menu.addAction(self._create_action(
            "Move", self.move_selected, "Ctrl+Shift+M"
        ))

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._create_action(
            "Zoom to Fit", self.zoom_to_fit, "F"
        ))
        view_menu.addSeparator()
        view_menu.addAction(self._create_action(
            "Front View", lambda: self.set_view("front"), "1"
        ))
        view_menu.addAction(self._create_action(
            "Top View", lambda: self.set_view("top"), "2"
        ))
        view_menu.addAction(self._create_action(
            "Right View", lambda: self.set_view("right"), "3"
        ))
        view_menu.addAction(self._create_action(
            "Isometric View", lambda: self.set_view("iso"), "0"
        ))

        # Modeling menu
        modeling_menu = menubar.addMenu("&Modeling")
        modeling_menu.addAction(self._create_action(
            "Create Beam", self.create_beam, "B"
        ))
        modeling_menu.addAction(self._create_action(
            "Create Column", self.create_column, "C"
        ))
        modeling_menu.addAction(self._create_action(
            "Create Plate", self.create_plate, "P"
        ))
        modeling_menu.addSeparator()
        modeling_menu.addAction(self._create_action(
            "Create Grid...", self.create_grid, "G"
        ))

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self._create_action(
            "Numbering Settings...", self.open_numbering_settings, "Ctrl+N"
        ))
        tools_menu.addSeparator()
        tools_menu.addAction(self._create_action(
            "Toggle All Snaps", self.toggle_all_snaps, "F3"
        ))
        tools_menu.addAction(self._create_action(
            "Toggle Grid Snap", self.toggle_grid_snap, "F4"
        ))
        tools_menu.addAction(self._create_action(
            "Toggle Endpoint Snap", self.toggle_endpoint_snap, "F5"
        ))

        # Claude menu
        claude_menu = menubar.addMenu("Cla&ude")
        claude_menu.addAction(self._create_action(
            "Import Plan...", self.import_plan, "Ctrl+I"
        ))
        claude_menu.addSeparator()
        claude_menu.addAction(self._create_action(
            "Open Prompt...", self.open_claude_prompt, "Ctrl+Space"
        ))
        claude_menu.addAction(self._create_action(
            "Toggle Terminal", self.toggle_claude_terminal, "Ctrl+`"
        ))

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self._create_action(
            "About Schmekla", self.show_about
        ))

    def _setup_toolbars(self):
        """Create toolbars."""
        # Main toolbar
        main_toolbar = QToolBar("Main", self)
        main_toolbar.setIconSize(QSize(24, 24))
        main_toolbar.addAction(self._create_action("New", self.new_model))
        main_toolbar.addAction(self._create_action("Open", self.open_model))
        main_toolbar.addAction(self._create_action("Save", self.save_model))
        main_toolbar.addSeparator()
        main_toolbar.addAction(self._create_action("Undo", self.undo))
        main_toolbar.addAction(self._create_action("Redo", self.redo))
        self.addToolBar(main_toolbar)

        # Modeling toolbar
        modeling_toolbar = QToolBar("Modeling", self)
        modeling_toolbar.setIconSize(QSize(24, 24))
        modeling_toolbar.addAction(self._create_action("Beam", self.create_beam))
        modeling_toolbar.addAction(self._create_action("Column", self.create_column))
        modeling_toolbar.addAction(self._create_action("Plate", self.create_plate))
        modeling_toolbar.addSeparator()
        modeling_toolbar.addAction(self._create_action("Grid", self.create_grid))
        self.addToolBar(modeling_toolbar)

    def _setup_docks(self):
        """Create dockable panels."""
        # Model tree dock (left)
        self.tree_dock = QDockWidget("Model", self)
        self.model_tree = QTreeWidget()
        self.model_tree.setHeaderLabels(["Name", "Type"])
        self.model_tree.setMinimumWidth(200)
        self.tree_dock.setWidget(self.model_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        # Properties dock (right) - Tekla-style properties panel
        self.props_dock = QDockWidget("Properties", self)
        from src.ui.widgets.properties_panel import PropertiesPanel
        self.properties_panel = PropertiesPanel()
        self.properties_panel.property_changed.connect(self._on_property_changed)
        self.props_dock.setWidget(self.properties_panel)
        self.props_dock.setMinimumWidth(250)
        self.addDockWidget(Qt.RightDockWidgetArea, self.props_dock)

        # Claude terminal dock (bottom) - Interactive CLI
        self.claude_dock = QDockWidget("Claude Terminal", self)

        # Use interactive terminal widget
        from src.ui.widgets.claude_terminal import ClaudeTerminal
        project_dir = Path(__file__).parent.parent.parent  # Schmekla root
        self.claude_terminal = ClaudeTerminal(working_dir=project_dir, parent=self)
        self.claude_terminal.model_changed.connect(self._on_model_file_changed)

        self.claude_dock.setWidget(self.claude_terminal)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.claude_dock)

        # Start Claude session after window is shown
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.claude_terminal.start_session)

    def _setup_status_bar(self):
        """Create status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Add permanent widgets
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)

        self.coord_label = QLabel("X: 0.00 | Y: 0.00 | Z: 0.00")
        self.statusBar.addPermanentWidget(self.coord_label)

        self.element_count_label = QLabel("Elements: 0")
        self.statusBar.addPermanentWidget(self.element_count_label)

        self.units_label = QLabel("Units: mm")
        self.statusBar.addPermanentWidget(self.units_label)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # ESC - Cancel current operation / Return to IDLE
        esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc_shortcut.activated.connect(self._on_escape_pressed)

    def _on_escape_pressed(self):
        """Handle ESC key - cancel current operation."""
        if self.interaction_manager:
            self.interaction_manager.cancel()
            logger.info("ESC pressed - returned to IDLE mode")

    def _connect_signals(self):
        """Connect model signals to UI updates."""
        self.model.element_added.connect(self._on_element_added)
        self.model.element_removed.connect(self._on_element_removed)
        self.model.model_changed.connect(self._update_ui)
        self.model.selection_changed.connect(self._on_selection_changed)

        # Invalidate snap cache when model changes (elements added/removed)
        self.model.model_changed.connect(lambda: self._invalidate_snap_cache("model changed"))

        # Connect viewport snap feedback to status bar
        if self.viewport:
            try:
                self.viewport.snap_feedback.connect(self._on_snap_feedback)
                logger.debug("Connected viewport snap feedback signal")
            except AttributeError as e:
                logger.warning(f"Viewport snap feedback signal not available: {e}")

    def _on_snap_feedback(self, message: str):
        """Update coordinate label in status bar with snap feedback."""
        self.coord_label.setText(message)

    def _invalidate_snap_cache(self, reason: str = ""):
        """Invalidate snap manager cache when model structure changes.

        Args:
            reason: Optional description of why cache was invalidated
        """
        if self.snap_manager:
            self.snap_manager.invalidate_cache()
            reason_str = f" ({reason})" if reason else ""
            logger.info(f"Snap manager cache invalidated{reason_str}")

    def _load_style(self):
        """Load application stylesheet."""
        # Basic dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #3c3c3c;
                color: white;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 3px;
            }
            QDockWidget {
                color: white;
            }
            QDockWidget::title {
                background-color: #3c3c3c;
                padding: 4px;
            }
            QTreeWidget {
                background-color: #2b2b2b;
                color: white;
                border: none;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                font-family: Consolas, monospace;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)

    def _create_action(
        self,
        text: str,
        slot=None,
        shortcut=None,
        icon: str = None
    ) -> QAction:
        """Helper to create QAction."""
        action = QAction(text, self)
        if slot:
            action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        if icon:
            action.setIcon(QIcon(icon))
        return action

    # Slots
    def _on_element_added(self, element):
        """Handle element added to model."""
        item = QTreeWidgetItem([
            element.name or str(element.id)[:8],
            element.element_type.value
        ])
        item.setData(0, Qt.UserRole, element.id)
        self.model_tree.addTopLevelItem(item)
        self._update_element_count()

    def _on_element_removed(self, element):
        """Handle element removed from model."""
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == element.id:
                self.model_tree.takeTopLevelItem(i)
                break
        self._update_element_count()

    def _on_selection_changed(self, selected_ids):
        """Handle selection change."""
        # Update tree selection
        self.model_tree.clearSelection()
        for i in range(self.model_tree.topLevelItemCount()):
            item = self.model_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) in selected_ids:
                item.setSelected(True)

        # Update properties panel
        if hasattr(self, 'properties_panel'):
            if not selected_ids:
                self.properties_panel.clear()
            else:
                elements = [self.model.get_element(eid) for eid in selected_ids]
                elements = [e for e in elements if e is not None]
                self.properties_panel.show_multiple(elements)

    def _on_property_changed(self, element_id: str, prop_name: str, new_value: str):
        """Handle property change from properties panel."""
        from uuid import UUID
        try:
            elem_uuid = UUID(element_id)
            element = self.model.get_element(elem_uuid)
            if element:
                if element.set_property(prop_name, new_value):
                    logger.info(f"Property {prop_name} changed to {new_value}")
                    self.model.element_modified.emit(element)
                    if self.viewport:
                        self.viewport.update_display()
        except Exception as e:
            logger.error(f"Failed to update property: {e}")

    def _update_ui(self):
        """Update UI after model change."""
        self._update_title()
        self._update_element_count()

    def _update_title(self):
        """Update window title."""
        title = f"Schmekla - {self.model.name}"
        if self.model.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def _update_element_count(self):
        """Update element count in status bar."""
        self.element_count_label.setText(f"Elements: {self.model.element_count}")

    def get_model_elements_safe(self):
        """Safely get all model elements for external operations.

        Returns:
            list: List of all elements in the model, or empty list on error.
        """
        try:
            if self.model is None:
                return []
            return list(self.model.get_all_elements())
        except Exception as e:
            logger.error(f"Failed to get model elements: {e}")
            return []

    def _on_model_file_changed(self):
        """Handle notification that Claude may have modified model files."""
        # Refresh UI in case the model was modified
        if hasattr(self, 'viewport') and self.viewport:
            self.viewport.update_display()
        self._rebuild_tree()
        self._update_element_count()
        self.status_label.setText("Model may have been updated by Claude")

    # Action handlers
    def new_model(self):
        """Create new model."""
        if self.model.is_modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before creating new model?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if result == QMessageBox.Save:
                if not self.save_model():
                    return
            elif result == QMessageBox.Cancel:
                return

        self.model.clear()
        self.model.name = "Untitled"
        self.model.file_path = None
        self.model_tree.clear()
        self._update_ui()
        self.status_label.setText("New model created")

    def open_model(self):
        """Open model from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Model",
            str(Path.home()),
            "Schmekla Models (*.schmekla);;All Files (*)"
        )
        if file_path:
            if self.model.load(Path(file_path)):
                self._rebuild_tree()
                self.status_label.setText(f"Opened: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to open model")

    def save_model(self) -> bool:
        """Save model."""
        if self.model.file_path is None:
            return self.save_model_as()
        return self.model.save()

    def save_model_as(self) -> bool:
        """Save model with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Model",
            str(Path.home() / f"{self.model.name}.schmekla"),
            "Schmekla Models (*.schmekla)"
        )
        if file_path:
            if self.model.save(Path(file_path)):
                self.status_label.setText(f"Saved: {file_path}")
                return True
            else:
                QMessageBox.warning(self, "Error", "Failed to save model")
        return False

    def export_ifc(self):
        """Export model to IFC."""
        from src.ui.dialogs.export_dialog import ExportDialog

        dialog = ExportDialog(self, default_name=self.model.name)
        if dialog.exec() == ExportDialog.Accepted:
            file_path = dialog.get_export_path()
            settings = dialog.get_settings()

            if file_path:
                try:
                    from src.ifc.exporter import IFCExporter
                    exporter = IFCExporter(self.model)
                    exporter.export(file_path, schema=settings.get("schema", "IFC2X3"))
                    self.status_label.setText(f"Exported: {file_path}")
                    QMessageBox.information(self, "Export Complete", f"Model exported to:\n{file_path}")
                except ImportError as e:
                    QMessageBox.warning(self, "Error", f"IFC export requires ifcopenshell: {e}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def undo(self):
        """Undo last action."""
        if self.model.undo():
            self.status_label.setText("Undo")
            self._rebuild_tree()

    def redo(self):
        """Redo last undone action."""
        if self.model.redo():
            self.status_label.setText("Redo")
            self._rebuild_tree()

    def select_all(self):
        """Select all elements."""
        self.model.select_all()

    def delete_selected(self):
        """Delete selected elements."""
        for elem_id in self.model.get_selected_ids():
            self.model.remove_element(elem_id)

    def zoom_to_fit(self):
        """Zoom viewport to fit all elements."""
        if self.viewport:
            self.viewport.zoom_to_fit()

    def set_view(self, view_name: str):
        """Set viewport to standard view."""
        if self.viewport:
            self.viewport.set_view(view_name)

    def create_beam(self):
        """Enter beam creation mode."""
        # InteractionMode is now imported at module level for instant access
        if self.interaction_manager:
            self.interaction_manager.set_mode(InteractionMode.CREATE_BEAM)

    def create_column(self):
        """Enter column creation mode."""
        # InteractionMode is now imported at module level for instant access
        if self.interaction_manager:
            self.interaction_manager.set_mode(InteractionMode.CREATE_COLUMN)

    def create_plate(self):
        """Enter plate creation mode."""
        # InteractionMode is now imported at module level for instant access
        if self.interaction_manager:
            self.interaction_manager.set_mode(InteractionMode.CREATE_PLATE)

    def copy_selected(self):
        """Enter copy mode for selected elements."""
        if not self.model.get_selected_ids():
            self.status_label.setText("Select elements first")
            return
        if self.interaction_manager:
            self.interaction_manager.set_mode(InteractionMode.COPY)

    def move_selected(self):
        """Enter move mode for selected elements."""
        if not self.model.get_selected_ids():
            self.status_label.setText("Select elements first")
            return
        if self.interaction_manager:
            self.interaction_manager.set_mode(InteractionMode.MOVE)

    def create_grid(self):
        """Open grid creation dialog."""
        from src.ui.dialogs.grid_dialog import GridDialog

        dialog = GridDialog(self)
        if dialog.exec() == GridDialog.Accepted:
            grids = dialog.get_grids()
            if grids:
                # Store grids in model (implementation depends on grid handling)
                self.model._grids = grids

                # Invalidate snap manager cache so new grid intersections are used
                self._invalidate_snap_cache("grid points updated")

                # Calculate total grid intersection points for status message
                x_count = len(grids.get('x_grids', []))
                y_count = len(grids.get('y_grids', []))
                snap_points = x_count * y_count

                self.status_label.setText(
                    f"Created {x_count} X grids and {y_count} Y grids "
                    f"({snap_points} snap points)"
                )
                if self.viewport:
                    self.viewport.update_display()

    def import_plan(self):
        """Open plan import dialog for auto-building from drawings."""
        from src.ui.dialogs.plan_import_dialog import PlanImportDialog

        dialog = PlanImportDialog(self.model, self)
        dialog.exec()

        # Refresh display after import
        if self.viewport:
            self.viewport.update_display()
        self._update_ui()

    def open_claude_prompt(self):
        """Focus Claude input."""
        self.claude_dock.show()
        self.claude_terminal.setFocus()

    def toggle_claude_terminal(self):
        """Toggle Claude terminal visibility."""
        self.claude_dock.setVisible(not self.claude_dock.isVisible())

    def open_numbering_settings(self):
        """Open numbering settings dialog."""
        from src.ui.dialogs.numbering_dialog import NumberingDialog
        from src.core.numbering import NumberingManager

        # Get or create numbering manager
        if not hasattr(self, 'numbering_manager'):
            self.numbering_manager = NumberingManager()

        dialog = NumberingDialog(self.numbering_manager, self)
        dialog.exec()

    def toggle_all_snaps(self):
        """Toggle all snapping on/off (F3)."""
        if self.interaction_manager:
            enabled = self.interaction_manager.toggle_all_snaps()
            state = "ON" if enabled else "OFF"
            self.status_label.setText(f"All Snapping: {state}")
            logger.info(f"All snapping toggled: {state}")

    def toggle_grid_snap(self):
        """Toggle grid snap only (F4)."""
        if self.interaction_manager:
            enabled = self.interaction_manager.toggle_grid_snap()
            state = "ON" if enabled else "OFF"
            self.status_label.setText(f"Grid Snap: {state}")
            logger.info(f"Grid snap toggled: {state}")

    def toggle_endpoint_snap(self):
        """Toggle endpoint snap only (F5)."""
        if self.interaction_manager:
            enabled = self.interaction_manager.toggle_endpoint_snap()
            state = "ON" if enabled else "OFF"
            self.status_label.setText(f"Endpoint Snap: {state}")
            logger.info(f"Endpoint snap toggled: {state}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Schmekla",
            "Schmekla - Structural Modeler\n\n"
            "Version 0.1.0\n\n"
            "A custom structural modeling application with\n"
            "IFC export and Claude AI integration."
        )

    def _rebuild_tree(self):
        """Rebuild model tree from model."""
        self.model_tree.clear()
        for element in self.model.get_all_elements():
            self._on_element_added(element)

    # Interaction Slots
    def _on_prompt_changed(self, message: str):
        """Update status bar prompt."""
        self.status_label.setText(message)

    def _on_element_created_request(self, element_type: str, params: dict):
        """Handle element creation request from InteractionManager."""
        # All element classes (Beam, Column, Plate, Profile, Material, Point3D)
        # are now imported at module level for instant element creation
        try:
            new_element = None
            if element_type == "BEAM":
                new_element = Beam(
                    start_point=params["start"],
                    end_point=params["end"],
                    profile=Profile.from_name(params.get("profile", "UB 305x165x40")),
                    material=Material.from_name(params.get("material", "S355")),
                    name="BEAM"
                )
            elif element_type == "COLUMN":
                base = params["base"]
                height = params["height"]
                end = Point3D(base.x, base.y, base.z + height)

                new_element = Column(
                    start_point=base,
                    end_point=end,
                    profile=Profile.from_name(params.get("profile", "UC 203x203x46")),
                    material=Material.from_name(params.get("material", "S355")),
                    name="COLUMN"
                )
            elif element_type == "PLATE":
                new_element = Plate(
                    points=params["points"],
                    thickness=params.get("thickness", 10.0),
                    material=Material.from_name(params.get("material", "S355")),
                    name="PLATE"
                )

            if new_element:
                self.model.add_element(new_element)
                logger.info(f"Interactive creation: {element_type}")
                if self.viewport:
                    self.viewport.update_display()

        except Exception as e:
            logger.error(f"Failed to create element interactively: {e}")
            self.status_label.setText(f"Error: {e}")

    def _on_copy_requested(self, displacement):
        """Handle copy request from interaction manager."""
        from src.geometry.vector import Vector3D
        selected = self.model.get_selected_elements()
        new_elements = []
        for elem in selected:
            new_elem = elem.copy()
            new_elem.move(displacement)
            self.model.add_element(new_elem)
            new_elements.append(new_elem)
        self.status_label.setText(f"Copied {len(new_elements)} elements")
        if self.viewport:
            self.viewport.update_display()

    def _on_move_requested(self, displacement):
        """Handle move request from interaction manager."""
        selected = self.model.get_selected_elements()
        for elem in selected:
            elem.move(displacement)
        self.model.model_changed.emit()
        self.status_label.setText(f"Moved {len(selected)} elements")
        if self.viewport:
            self.viewport.update_display()

    def closeEvent(self, event):
        """Handle window close."""
        if self.model.is_modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if result == QMessageBox.Save:
                if not self.save_model():
                    event.ignore()
                    return
            elif result == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()
