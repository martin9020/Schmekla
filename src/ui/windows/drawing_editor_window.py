"""
Drawing Editor Window.

Displays 2D drawing with dimensions.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsLineItem, 
    QGraphicsTextItem, QVBoxLayout, QWidget, QToolBar, QLabel,
    QGraphicsItem
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QFont, QPainter

from src.core.model import StructuralModel
from src.core.drawing import Drawing, DrawingType
from src.drawing.view_generator import ViewGenerator, DrawingView, DrawingLine, DrawingDimension

class DrawingGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
    def wheelEvent(self, event):
        """Zoom with mouse wheel."""
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)

class DrawingEditorWindow(QMainWindow):
    def __init__(self, model: StructuralModel, drawing: Drawing, parent=None):
        super().__init__(parent)
        self.model = model
        self.drawing = drawing
        
        self.setWindowTitle(f"Drawing Editor - {drawing.name} - {drawing.title}")
        self.resize(1000, 800)
        
        self._setup_ui()
        self._load_drawing()
        
    def _setup_ui(self):
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        toolbar.addAction("Save", self._save_drawing)
        toolbar.addAction("Print", self._print_drawing)
        toolbar.addSeparator()
        toolbar.addAction("Zoom Extents", self._zoom_extents)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Graphics View
        self.scene = QGraphicsScene()
        self.view = DrawingGraphicsView(self.scene)
        self.scene.setBackgroundBrush(Qt.white)
        
        layout.addWidget(self.view)
        
        # Status bar
        self.statusBar().showMessage(f"Status: {self.drawing.status.value}")
        
    def _load_drawing(self):
        """Generate and render the drawing content."""
        self.scene.clear()
        
        # Frame/Border (A3 size approx scaled down or just a box)
        # Let's assume 1 unit = 1 mm on screen for now
        
        # For each element in the drawing, generate a view
        # Currently we only support single element assembly drawings primarily
        
        start_x = 100
        start_y = 100
        
        for element_id in self.drawing.associated_element_ids:
            element = self.model.get_element(element_id)
            if not element:
                continue
                
            # Generate views
            # Front View
            view_data = ViewGenerator.generate_assembly_view(element, "Front")
            self._render_view(view_data, offset_x=start_x, offset_y=start_y, label="FRONT VIEW")
            
            # Top View (placed below)
            view_height = view_data.bounds[3]
            start_y += view_height + 150 # Spacing
            
            view_data_top = ViewGenerator.generate_assembly_view(element, "Top")
            self._render_view(view_data_top, offset_x=start_x, offset_y=start_y, label="TOP VIEW")
            
            start_y += view_data_top.bounds[3] + 100
            
        self._zoom_extents()

    def _render_view(self, view_data: DrawingView, offset_x: float, offset_y: float, label: str):
        """Render a generated view onto the scene."""
        
        # Draw Label
        text_item = self.scene.addText(label)
        text_item.setPos(offset_x, offset_y - 30)
        font = QFont("Arial", 10)
        font.setBold(True)
        text_item.setFont(font)
        
        # Draw Lines
        pen_solid = QPen(Qt.black, 2)
        pen_center = QPen(Qt.red, 1, Qt.DashDotLine)
        
        # We need to flip Y axis because QGraphicsScene Y grows downwards, 
        # but engineering coordinates Y usually grows upwards.
        # However, our ViewGenerator produced screen coords (0,0 to L,H), so Y grows down.
        # So we can map directly.
        
        for line in view_data.lines:
            pen = pen_center if line.line_type == "Center" else pen_solid
            self.scene.addLine(
                offset_x + line.start_x, offset_y + line.start_y,
                offset_x + line.end_x, offset_y + line.end_y,
                pen
            )
            
        # Draw Dimensions
        dim_pen = QPen(Qt.darkBlue, 1)
        font_dim = QFont("Arial", 8)
        
        for dim in view_data.dimensions:
            # Dimension line
            # Calculate offset position
            # Simple implementation: Perpendicular offset
            
            # For horizontal dims (y1 == y2)
            if abs(dim.p1_y - dim.p2_y) < 0.001:
                y_pos = offset_y + dim.p1_y + dim.offset
                self.scene.addLine(
                    offset_x + dim.p1_x, y_pos,
                    offset_x + dim.p2_x, y_pos,
                    dim_pen
                )
                # Extension lines
                self.scene.addLine(
                    offset_x + dim.p1_x, offset_y + dim.p1_y,
                    offset_x + dim.p1_x, y_pos,
                    dim_pen
                )
                self.scene.addLine(
                    offset_x + dim.p2_x, offset_y + dim.p2_y,
                    offset_x + dim.p2_x, y_pos,
                    dim_pen
                )
                # Text
                text = self.scene.addText(dim.text)
                text.setDefaultTextColor(Qt.darkBlue)
                text.setFont(font_dim)
                # Center text
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                center_x = offset_x + (dim.p1_x + dim.p2_x) / 2
                text.setPos(center_x - text_width/2, y_pos - text_height - 2)
                
            # For vertical dims (x1 == x2)
            elif abs(dim.p1_x - dim.p2_x) < 0.001:
                x_pos = offset_x + dim.p1_x + dim.offset
                self.scene.addLine(
                    x_pos, offset_y + dim.p1_y,
                    x_pos, offset_y + dim.p2_y,
                    dim_pen
                )
                # Extension lines
                self.scene.addLine(
                    offset_x + dim.p1_x, offset_y + dim.p1_y,
                    x_pos, offset_y + dim.p1_y,
                    dim_pen
                )
                self.scene.addLine(
                    offset_x + dim.p2_x, offset_y + dim.p2_y,
                    x_pos, offset_y + dim.p2_y,
                    dim_pen
                )
                # Text
                text = self.scene.addText(dim.text)
                text.setDefaultTextColor(Qt.darkBlue)
                text.setFont(font_dim)
                
                # Rotate text for vertical dim
                text.setRotation(-90)
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                center_y = offset_y + (dim.p1_y + dim.p2_y) / 2
                
                # Position adjustments for rotated text are tricky
                # Basic positioning:
                text.setPos(x_pos - 5, center_y + text_width/2)

    def _save_drawing(self):
        # Placeholder
        pass
        
    def _print_drawing(self):
        # Placeholder
        pass
        
    def _zoom_extents(self):
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.view.scale(0.9, 0.9) # Add some margin
