"""
Drawing List Window.

Mimics the Tekla Structures Drawing List (Ctrl+L).
"""
from typing import Optional
from loguru import logger
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QHeaderView, QToolBar, QLabel, QMessageBox,
    QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon

from src.core.model import StructuralModel
from src.core.drawing import Drawing, DrawingType, DrawingStatus
from src.core.element import ElementType

class DrawingListWindow(QMainWindow):
    """
    Drawing List Window.
    Lists all drawings in the project and provides management tools.
    """
    
    def __init__(self, model: StructuralModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.drawing_manager = model.drawing_manager
        
        self.setWindowTitle("Drawing List")
        self.resize(800, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        self._setup_ui()
        self._setup_toolbar()
        self._refresh_table()
        
        self.open_editors = []
        
        # Connect signals
        # self.model.drawing_added.connect(self._refresh_table) # Need to add signals to DrawingManager/Model
        
    def _setup_ui(self):
        """Setup main UI elements."""
        # Top controls
        top_layout = QHBoxLayout()
        
        self.search_box = QLabel("Search:") # Placeholder for search
        top_layout.addWidget(self.search_box)
        top_layout.addStretch()
        
        # Numbering button (User Request)
        self.btn_number = QPushButton("Number Modified Objects")
        self.btn_number.clicked.connect(self._on_number_modified)
        self.btn_number.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(self.btn_number)
        
        self.layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Title", "Type", "Status", "Date Modified", "ID"
        ])
        
        # Table settings
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(5) # Hide ID
        
        self.table.doubleClicked.connect(self._on_open_drawing)
        
        self.layout.addWidget(self.table)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self._on_open_drawing)
        
        self.btn_create_ga = QPushButton("Create GA Drawing")
        self.btn_create_ga.clicked.connect(self._on_create_ga)
        
        self.btn_create_assembly = QPushButton("Create Assembly Drawing")
        self.btn_create_assembly.clicked.connect(self._on_create_assembly)
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._on_delete_drawing)
        
        bottom_layout.addWidget(self.btn_open)
        bottom_layout.addWidget(self.btn_create_ga)
        bottom_layout.addWidget(self.btn_create_assembly)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_delete)
        
        self.layout.addLayout(bottom_layout)
        
    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = QToolBar("Drawing Tools")
        self.addToolBar(toolbar)
        # Add actions if needed
        
    def _refresh_table(self):
        """Refresh the drawing table."""
        self.table.setRowCount(0)
        drawings = self.drawing_manager.get_all_drawings()
        
        self.table.setRowCount(len(drawings))
        for i, drawing in enumerate(drawings):
            self.table.setItem(i, 0, QTableWidgetItem(drawing.name))
            self.table.setItem(i, 1, QTableWidgetItem(drawing.title))
            self.table.setItem(i, 2, QTableWidgetItem(drawing.drawing_type.value))
            self.table.setItem(i, 3, QTableWidgetItem(drawing.status.value))
            self.table.setItem(i, 4, QTableWidgetItem(drawing.modification_date.strftime("%Y-%m-%d %H:%M")))
            self.table.setItem(i, 5, QTableWidgetItem(str(drawing.id)))
            
    def _on_number_modified(self):
        """Handle numbering request."""
        # Check if numbering is needed
        # In a real app, we might check modification flags. 
        # Here we just run the numbering process.
        
        # TODO: Show progress dialog
        try:
            # We need to access the numbering logic. 
            # The model has a numbering manager, but the actual logic to renumber everything
            # might need to be invoked carefully.
            
            # For now, we'll renumber all elements that don't have numbers or are modified.
            # Schmekla's NumberingManager calculates signatures.
            
            elements = self.model.get_all_elements()
            count = 0
            for el in elements:
                # Calculate signature and get number
                # This logic is partly inside StructuralModel.add_element, 
                # but we should probably expose a "renumber_all" method in NumberingManager or Model.
                
                # Let's use the NumberingManager directly
                if hasattr(self.model.numbering, 'get_number_for_element'):
                    new_num = self.model.numbering.get_number_for_element(el)
                    if el.part_number != new_num:
                        el.part_number = new_num
                        count += 1
            
            QMessageBox.information(self, "Numbering", f"Numbering complete. {count} elements updated.")
            self.model.model_changed.emit()
            
        except Exception as e:
            logger.error(f"Numbering failed: {e}")
            QMessageBox.critical(self, "Error", f"Numbering failed: {e}")

    def _on_create_ga(self):
        """Create a new GA drawing."""
        # For simplicity, create a dummy GA drawing
        # In real app, would show a dialog to select view/planes
        name = f"GA-{len(self.drawing_manager.get_all_drawings()) + 1}"
        drawing = self.drawing_manager.create_ga_drawing(name, "New General Arrangement")
        self._refresh_table()
        
    def _on_create_assembly(self):
        """Create assembly drawings for selected parts."""
        selected_ids = self.model.get_selected_ids()
        if not selected_ids:
            QMessageBox.warning(self, "Selection", "Please select elements to create drawings for.")
            return
            
        count = 0
        for uid in selected_ids:
            el = self.model.get_element(uid)
            if el and el.element_type not in [ElementType.GRID, ElementType.LEVEL]:
                # Check if drawing already exists? 
                # For now just create new one
                d = self.drawing_manager.create_assembly_drawing(uid)
                if d:
                    count += 1
        
        QMessageBox.information(self, "Drawings Created", f"Created {count} assembly drawings.")
        self._refresh_table()

    def _on_delete_drawing(self):
        """Delete selected drawings."""
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not rows:
            return
            
        if QMessageBox.question(self, "Confirm", f"Delete {len(rows)} drawings?") != QMessageBox.Yes:
            return
            
        for row in rows:
            drawing_id_str = self.table.item(row, 5).text()
            self.drawing_manager.delete_drawing(drawing_id_str) # UUID conversion handled in manager? No, dict key is UUID
            # We need to convert string to UUID
            from uuid import UUID
            self.drawing_manager.delete_drawing(UUID(drawing_id_str))
            
        self._refresh_table()

    def _on_open_drawing(self):
        """Open selected drawing."""
        rows = set(index.row() for index in self.table.selectedIndexes())
        if len(rows) != 1:
            return
            
        row = list(rows)[0]
        drawing_id_str = self.table.item(row, 5).text()
        from uuid import UUID
        drawing_id = UUID(drawing_id_str)
        
        drawing = self.drawing_manager.get_drawing(drawing_id)
        if not drawing:
            QMessageBox.warning(self, "Error", "Drawing not found!")
            return

        from src.ui.windows.drawing_editor_window import DrawingEditorWindow
        editor = DrawingEditorWindow(self.model, drawing, self)
        self.open_editors.append(editor)
        editor.show()
