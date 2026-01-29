
import sys
import os
sys.path.append(os.getcwd())
from uuid import uuid4
from PySide6.QtWidgets import QApplication

from src.core.model import StructuralModel
from src.core.beam import Beam
from src.geometry.point import Point3D
from src.ui.windows.drawing_editor_window import DrawingEditorWindow

def test_drawing_generation():
    # Setup
    model = StructuralModel()
    beam = Beam(Point3D(0,0,0), Point3D(5000,0,0))
    model.add_element(beam)
    
    # Create Drawing
    drawing = model.drawing_manager.create_assembly_drawing(beam.id)
    assert drawing is not None
    
    # Check View Generation
    from src.drawing.view_generator import ViewGenerator
    view = ViewGenerator.generate_assembly_view(beam, "Front")
    assert len(view.lines) > 0
    assert len(view.dimensions) > 0
    assert view.dimensions[0].text == "5000.0"

if __name__ == "__main__":
    test_drawing_generation()
    print("Test passed!")
