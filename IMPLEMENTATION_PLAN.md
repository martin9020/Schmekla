# Schmekla Implementation Plan

## Current Status (January 2026)

### Completed Features ✅
- **Core Infrastructure**: Project setup, logging, configuration
- **Geometry**: Point3D, Vector3D, basic transforms
- **Elements**: Beam, Column, Plate, Slab, Wall, Footing, CurvedBeam
- **UI**: Main window, 3D viewport (PyVista), Model tree, Properties panel
- **IFC Export**: Full IFC2X3 export with Tekla compatibility
- **Claude Integration**:
  - External terminal launcher (opens Claude in Windows Terminal)
  - Programmatic bridge with file reading capability
  - Plan import with vision analysis

### Deployment ✅
- `deploy/install.bat` - Automatic installation script
- `run_schmekla.bat` - Application launcher
- `.gitignore` - Proper exclusions for portable deployment

### In Progress 🔄
- Refining Claude CLI integration
- Testing on multiple machines

### Known Issues ⚠️
- Virtual environment (`venv/`) is NOT portable - must run install.bat on each machine
- Claude CLI must be installed separately: `npm install -g @anthropic-ai/claude-code`

---

## Executive Summary

Schmekla is a structural modeling application that creates 3D steel/concrete models and exports to IFC format for Tekla Structures compatibility. It features Claude Code CLI integration for AI-assisted natural language modeling.

**Target Deliverable:** Fully functional desktop application capable of:
- Creating structural elements (beams, columns, plates, slabs, walls, footings)
- 3D visualization with interactive manipulation
- IFC2X3 export certified for Tekla import
- Natural language model creation via Claude integration

---

## Phase 1: Foundation (Core Infrastructure)

### 1.1 Project Setup
**Priority: CRITICAL | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **1.1.1** Create virtual environment and install base dependencies
- [ ] **1.1.2** Set up pyproject.toml with project metadata
- [ ] **1.1.3** Create requirements.txt with pinned versions
- [ ] **1.1.4** Set up logging infrastructure (loguru)
- [ ] **1.1.5** Create configuration management system
- [ ] **1.1.6** Set up pytest infrastructure

#### Files to Create:
```
pyproject.toml
requirements.txt
setup.py
src/__init__.py
src/main.py
src/utils/__init__.py
src/utils/config.py
src/utils/logger.py
tests/__init__.py
tests/conftest.py
```

#### requirements.txt Content:
```
# Core
python>=3.11

# Geometry & CAD
ifcopenshell>=0.7.0
cadquery>=2.4.0
OCP>=7.7.0  # OpenCascade Python bindings
numpy>=1.24.0
scipy>=1.11.0

# UI
PySide6>=6.6.0
pyvista>=0.43.0
pyvistaqt>=0.11.0
vtk>=9.3.0

# Utilities
loguru>=0.7.0
pydantic>=2.5.0
uuid
json
typing_extensions>=4.8.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-qt>=4.2.0

# Development
black>=23.0.0
isort>=5.12.0
mypy>=1.7.0
```

#### Acceptance Criteria:
- [ ] `python -m src.main` runs without errors
- [ ] Logging outputs to console and file
- [ ] Configuration loads from config.yaml
- [ ] All imports resolve correctly

---

### 1.2 Geometry Foundation
**Priority: CRITICAL | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **1.2.1** Implement Point3D class with full vector operations
- [ ] **1.2.2** Implement Vector3D class with dot/cross products
- [ ] **1.2.3** Implement Line3D class for beam axes
- [ ] **1.2.4** Implement Plane class for slabs/walls
- [ ] **1.2.5** Implement Transform class (translation, rotation, scale)
- [ ] **1.2.6** Create unit conversion utilities (mm, m, in, ft)
- [ ] **1.2.7** Write comprehensive geometry tests

#### Files to Create:
```
src/geometry/__init__.py
src/geometry/point.py
src/geometry/vector.py
src/geometry/line.py
src/geometry/plane.py
src/geometry/transform.py
src/utils/units.py
tests/unit/test_geometry.py
```

#### Point3D Implementation Spec:
```python
class Point3D:
    """3D point with full coordinate operations."""

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: 'Vector3D') -> 'Point3D': ...
    def __sub__(self, other: 'Point3D') -> 'Vector3D': ...
    def distance_to(self, other: 'Point3D') -> float: ...
    def midpoint_to(self, other: 'Point3D') -> 'Point3D': ...
    def transform(self, matrix: 'Transform') -> 'Point3D': ...
    def to_tuple(self) -> tuple[float, float, float]: ...
    def to_occ(self) -> gp_Pnt: ...  # OpenCascade conversion
    def to_array(self) -> np.ndarray: ...

    @classmethod
    def from_tuple(cls, coords: tuple) -> 'Point3D': ...
    @classmethod
    def origin(cls) -> 'Point3D': ...
```

#### Acceptance Criteria:
- [ ] All geometric operations pass unit tests
- [ ] Conversion to/from OpenCascade types works
- [ ] Unit conversion handles mm/m/in/ft
- [ ] Transform matrices compose correctly

---

### 1.3 Core Data Model
**Priority: CRITICAL | Estimated Effort: 12 hours**

#### Tasks:
- [ ] **1.3.1** Implement StructuralElement base class
- [ ] **1.3.2** Implement Profile class with catalog loading
- [ ] **1.3.3** Implement Material class with properties
- [ ] **1.3.4** Implement StructuralModel (document) class
- [ ] **1.3.5** Implement Grid system class
- [ ] **1.3.6** Implement Level class
- [ ] **1.3.7** Create UK steel section profile database (JSON)
- [ ] **1.3.8** Create material database (JSON)
- [ ] **1.3.9** Implement serialization (save/load projects)

#### Files to Create:
```
src/core/__init__.py
src/core/element.py
src/core/profile.py
src/core/material.py
src/core/model.py
src/core/grid.py
src/core/level.py
src/utils/serialization.py
resources/profiles/uk_sections.json
resources/materials/materials.json
tests/unit/test_core.py
```

#### StructuralElement Base Class Spec:
```python
from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel

class ElementType(Enum):
    BEAM = "beam"
    COLUMN = "column"
    PLATE = "plate"
    SLAB = "slab"
    WALL = "wall"
    FOOTING = "footing"
    BRACE = "brace"
    PURLIN = "purlin"

class StructuralElement(ABC):
    """Base class for all structural elements."""

    def __init__(self):
        self.id: UUID = uuid4()
        self.name: str = ""
        self.material: Optional[Material] = None
        self.profile: Optional[Profile] = None
        self._solid: Optional[Any] = None  # OCC solid
        self._mesh: Optional[Any] = None   # Display mesh
        self._dirty: bool = True           # Needs regeneration

    @property
    @abstractmethod
    def element_type(self) -> ElementType:
        """Return the element type."""
        pass

    @abstractmethod
    def generate_solid(self) -> Any:
        """Generate OpenCascade solid geometry."""
        pass

    @abstractmethod
    def to_ifc(self, ifc_model) -> Any:
        """Export element to IFC entity."""
        pass

    def get_solid(self) -> Any:
        """Get solid, regenerating if dirty."""
        if self._dirty or self._solid is None:
            self._solid = self.generate_solid()
            self._mesh = None  # Invalidate mesh
            self._dirty = False
        return self._solid

    def get_mesh(self) -> Any:
        """Get display mesh for rendering."""
        if self._mesh is None:
            solid = self.get_solid()
            self._mesh = self._tessellate(solid)
        return self._mesh

    def invalidate(self):
        """Mark element as needing regeneration."""
        self._dirty = True

    def get_properties(self) -> dict:
        """Return element properties for UI display."""
        pass

    def set_property(self, name: str, value: Any):
        """Set element property and invalidate."""
        pass

    def get_bounding_box(self) -> tuple:
        """Return (min_point, max_point) bounding box."""
        pass

    def _tessellate(self, solid) -> Any:
        """Convert solid to mesh for display."""
        pass
```

#### StructuralModel (Document) Spec:
```python
from typing import Dict, List, Optional
from uuid import UUID
from PySide6.QtCore import QObject, Signal

class StructuralModel(QObject):
    """Main model document containing all structural elements."""

    # Signals for UI updates
    element_added = Signal(object)
    element_removed = Signal(object)
    element_modified = Signal(object)
    model_changed = Signal()

    def __init__(self):
        super().__init__()
        self.name: str = "Untitled"
        self.file_path: Optional[str] = None
        self._elements: Dict[UUID, StructuralElement] = {}
        self._grids: List[Grid] = []
        self._levels: List[Level] = []
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def add_element(self, element: StructuralElement) -> UUID:
        """Add element to model."""
        pass

    def remove_element(self, element_id: UUID) -> bool:
        """Remove element from model."""
        pass

    def get_element(self, element_id: UUID) -> Optional[StructuralElement]:
        """Get element by ID."""
        pass

    def get_elements_by_type(self, element_type: ElementType) -> List[StructuralElement]:
        """Get all elements of a specific type."""
        pass

    def get_all_elements(self) -> List[StructuralElement]:
        """Get all elements in model."""
        pass

    def execute_command(self, command: 'Command'):
        """Execute command with undo support."""
        pass

    def undo(self):
        """Undo last command."""
        pass

    def redo(self):
        """Redo last undone command."""
        pass

    def save(self, file_path: str):
        """Save model to file."""
        pass

    def load(self, file_path: str):
        """Load model from file."""
        pass

    def clear(self):
        """Clear all elements from model."""
        pass

    def get_bounding_box(self) -> tuple:
        """Get bounding box of entire model."""
        pass
```

#### UK Sections JSON Structure:
```json
{
  "UB": {
    "UB 305x165x40": {
      "type": "I",
      "h": 303.4,
      "b": 165.0,
      "tw": 6.0,
      "tf": 10.2,
      "r": 8.9,
      "area": 51.3,
      "weight": 40.3,
      "Ix": 8503,
      "Iy": 764
    }
    // ... more sections
  },
  "UC": { ... },
  "PFC": { ... },
  "SHS": { ... },
  "RHS": { ... },
  "CHS": { ... }
}
```

#### Acceptance Criteria:
- [ ] Elements can be created with all properties
- [ ] Profile catalog loads all UK sections
- [ ] Material database loads with properties
- [ ] Model serialization round-trips correctly
- [ ] Undo/redo works for all operations

---

## Phase 2: Structural Elements

### 2.1 Beam Element
**Priority: CRITICAL | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **2.1.1** Implement Beam class inheriting from StructuralElement
- [ ] **2.1.2** Implement straight beam solid generation
- [ ] **2.1.3** Implement beam with start/end offsets
- [ ] **2.1.4** Implement beam rotation around axis
- [ ] **2.1.5** Implement beam cut features (cope, notch)
- [ ] **2.1.6** Implement beam IFC export (IfcBeam)
- [ ] **2.1.7** Write beam tests

#### Files to Create:
```
src/core/beam.py
src/ifc/ifc_beam.py
tests/unit/test_beam.py
```

#### Beam Class Spec:
```python
class Beam(StructuralElement):
    """Structural beam element."""

    element_type = ElementType.BEAM

    def __init__(
        self,
        start_point: Point3D,
        end_point: Point3D,
        profile: Profile,
        material: Optional[Material] = None,
        rotation: float = 0.0,  # Degrees around beam axis
        start_offset: Optional[Vector3D] = None,
        end_offset: Optional[Vector3D] = None,
    ):
        super().__init__()
        self.start_point = start_point
        self.end_point = end_point
        self.profile = profile
        self.material = material or Material.default_steel()
        self.rotation = rotation
        self.start_offset = start_offset or Vector3D.zero()
        self.end_offset = end_offset or Vector3D.zero()

        # Beam-specific properties
        self.start_connection: Optional[str] = None
        self.end_connection: Optional[str] = None
        self.camber: float = 0.0

    @property
    def length(self) -> float:
        """Calculate beam length."""
        return self.start_point.distance_to(self.end_point)

    @property
    def direction(self) -> Vector3D:
        """Get beam direction vector."""
        return (self.end_point - self.start_point).normalize()

    def generate_solid(self):
        """Generate beam solid by sweeping profile along axis."""
        # Use CadQuery to create swept solid
        import cadquery as cq

        # Get profile cross-section
        profile_wire = self.profile.to_cadquery_wire()

        # Create path
        path = cq.Edge.makeLine(
            self.start_point.to_tuple(),
            self.end_point.to_tuple()
        )

        # Sweep profile along path
        solid = cq.Workplane().add(profile_wire).sweep(path)

        # Apply rotation
        if self.rotation != 0:
            solid = solid.rotate(
                self.start_point.to_tuple(),
                self.end_point.to_tuple(),
                self.rotation
            )

        return solid.val()

    def to_ifc(self, ifc_model):
        """Export beam to IFC."""
        from src.ifc.ifc_beam import create_ifc_beam
        return create_ifc_beam(self, ifc_model)

    def split_at_point(self, point: Point3D) -> tuple['Beam', 'Beam']:
        """Split beam at point, returning two beams."""
        pass

    def extend_to(self, target_plane: Plane) -> None:
        """Extend beam to intersect with plane."""
        pass

    def trim_to(self, target_plane: Plane) -> None:
        """Trim beam at plane intersection."""
        pass
```

#### Acceptance Criteria:
- [ ] Beam solid generates correctly for all profile types
- [ ] Rotation applies correctly
- [ ] Start/end offsets work
- [ ] IFC export creates valid IfcBeam
- [ ] Beam imports correctly in Tekla (manual test)

---

### 2.2 Column Element
**Priority: CRITICAL | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **2.2.1** Implement Column class inheriting from StructuralElement
- [ ] **2.2.2** Implement column solid generation
- [ ] **2.2.3** Implement column with base/top offsets
- [ ] **2.2.4** Implement column rotation
- [ ] **2.2.5** Implement column IFC export (IfcColumn)
- [ ] **2.2.6** Write column tests

#### Files to Create:
```
src/core/column.py
src/ifc/ifc_column.py
tests/unit/test_column.py
```

#### Column Class Spec:
```python
class Column(StructuralElement):
    """Structural column element."""

    element_type = ElementType.COLUMN

    def __init__(
        self,
        base_point: Point3D,
        height: float,
        profile: Profile,
        material: Optional[Material] = None,
        rotation: float = 0.0,  # Rotation around Z axis
        base_offset: float = 0.0,
        top_offset: float = 0.0,
    ):
        super().__init__()
        self.base_point = base_point
        self.height = height
        self.profile = profile
        self.material = material or Material.default_steel()
        self.rotation = rotation
        self.base_offset = base_offset
        self.top_offset = top_offset

    @property
    def top_point(self) -> Point3D:
        """Calculate column top point."""
        return Point3D(
            self.base_point.x,
            self.base_point.y,
            self.base_point.z + self.height
        )

    def generate_solid(self):
        """Generate column solid by extruding profile."""
        import cadquery as cq
        # Extrude profile in Z direction
        pass

    def to_ifc(self, ifc_model):
        """Export column to IFC."""
        from src.ifc.ifc_column import create_ifc_column
        return create_ifc_column(self, ifc_model)
```

---

### 2.3 Plate Element
**Priority: HIGH | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **2.3.1** Implement Plate class
- [ ] **2.3.2** Implement rectangular plate solid
- [ ] **2.3.3** Implement polygonal plate solid
- [ ] **2.3.4** Implement plate holes (circular, rectangular)
- [ ] **2.3.5** Implement plate IFC export (IfcPlate)
- [ ] **2.3.6** Write plate tests

#### Files to Create:
```
src/core/plate.py
src/ifc/ifc_plate.py
tests/unit/test_plate.py
```

---

### 2.4 Slab Element
**Priority: HIGH | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **2.4.1** Implement Slab class
- [ ] **2.4.2** Implement rectangular slab solid
- [ ] **2.4.3** Implement polygonal slab solid
- [ ] **2.4.4** Implement slab openings
- [ ] **2.4.5** Implement slab IFC export (IfcSlab)
- [ ] **2.4.6** Write slab tests

#### Files to Create:
```
src/core/slab.py
src/ifc/ifc_slab.py
tests/unit/test_slab.py
```

---

### 2.5 Wall Element
**Priority: HIGH | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **2.5.1** Implement Wall class
- [ ] **2.5.2** Implement straight wall solid
- [ ] **2.5.3** Implement wall openings (doors, windows)
- [ ] **2.5.4** Implement wall IFC export (IfcWall)
- [ ] **2.5.5** Write wall tests

#### Files to Create:
```
src/core/wall.py
src/ifc/ifc_wall.py
tests/unit/test_wall.py
```

---

### 2.6 Footing Element
**Priority: MEDIUM | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **2.6.1** Implement Footing class
- [ ] **2.6.2** Implement pad footing solid
- [ ] **2.6.3** Implement strip footing solid
- [ ] **2.6.4** Implement footing IFC export (IfcFooting)
- [ ] **2.6.5** Write footing tests

#### Files to Create:
```
src/core/footing.py
src/ifc/ifc_footing.py
tests/unit/test_footing.py
```

---

## Phase 3: User Interface

### 3.1 Main Window Framework
**Priority: CRITICAL | Estimated Effort: 10 hours**

#### Tasks:
- [ ] **3.1.1** Create main window with menu bar
- [ ] **3.1.2** Implement dockable panel system
- [ ] **3.1.3** Create status bar with coordinates display
- [ ] **3.1.4** Implement toolbar system
- [ ] **3.1.5** Create ribbon interface (optional, fallback to toolbars)
- [ ] **3.1.6** Implement keyboard shortcuts
- [ ] **3.1.7** Create dark theme stylesheet

#### Files to Create:
```
src/ui/__init__.py
src/ui/main_window.py
src/ui/toolbar.py
src/ui/ribbon.py
src/ui/styles/dark_theme.qss
```

#### Main Window Layout:
```
┌─────────────────────────────────────────────────────────────────┐
│  File  Edit  View  Modeling  Analyze  Export  Claude  Help     │ Menu Bar
├─────────────────────────────────────────────────────────────────┤
│ [New] [Open] [Save] | [Beam] [Column] [Plate] | [Select] [Pan] │ Toolbar
├──────────────┬────────────────────────────┬─────────────────────┤
│              │                            │                     │
│   Model      │                            │    Properties       │
│   Tree       │      3D Viewport           │    Panel            │
│              │                            │                     │
│              │                            │                     │
├──────────────┤                            ├─────────────────────┤
│              │                            │                     │
│   Claude     │                            │    Object           │
│   Terminal   │                            │    Info             │
│              │                            │                     │
├──────────────┴────────────────────────────┴─────────────────────┤
│ Ready | X: 0.00 | Y: 0.00 | Z: 0.00 | Elements: 0 | Units: mm  │ Status
└─────────────────────────────────────────────────────────────────┘
```

#### Main Window Spec:
```python
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QStatusBar,
    QMenuBar, QMenu, QAction, QWidget
)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schmekla - Structural Modeler")
        self.setMinimumSize(1200, 800)

        # Core components
        self.model = StructuralModel()
        self.viewport = Viewport3D(self.model)
        self.model_tree = ModelTree(self.model)
        self.properties_panel = PropertiesPanel()
        self.claude_terminal = ClaudeTerminal(self.model)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbars()
        self._setup_docks()
        self._setup_connections()
        self._load_style()

    def _setup_ui(self):
        """Initialize central widget and layout."""
        self.setCentralWidget(self.viewport)

    def _setup_menus(self):
        """Create menu bar and menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._create_action("New", "Ctrl+N", self.new_model))
        file_menu.addAction(self._create_action("Open...", "Ctrl+O", self.open_model))
        file_menu.addAction(self._create_action("Save", "Ctrl+S", self.save_model))
        file_menu.addAction(self._create_action("Save As...", "Ctrl+Shift+S", self.save_model_as))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action("Export IFC...", "Ctrl+E", self.export_ifc))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action("Exit", "Alt+F4", self.close))

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._create_action("Undo", "Ctrl+Z", self.undo))
        edit_menu.addAction(self._create_action("Redo", "Ctrl+Y", self.redo))
        edit_menu.addSeparator()
        edit_menu.addAction(self._create_action("Delete", "Delete", self.delete_selected))

        # Modeling menu
        modeling_menu = menubar.addMenu("&Modeling")
        modeling_menu.addAction(self._create_action("Create Beam", "B", self.create_beam))
        modeling_menu.addAction(self._create_action("Create Column", "C", self.create_column))
        modeling_menu.addAction(self._create_action("Create Plate", "P", self.create_plate))
        # ... more element types

        # Claude menu
        claude_menu = menubar.addMenu("Cla&ude")
        claude_menu.addAction(self._create_action("Open Prompt...", "Ctrl+Space", self.open_claude_prompt))
        claude_menu.addAction(self._create_action("Toggle Terminal", "Ctrl+`", self.toggle_claude_terminal))

    def _setup_toolbars(self):
        """Create toolbars."""
        # Main toolbar
        main_toolbar = QToolBar("Main")
        main_toolbar.addAction(self._create_action("New", icon="new.png"))
        main_toolbar.addAction(self._create_action("Open", icon="open.png"))
        main_toolbar.addAction(self._create_action("Save", icon="save.png"))
        self.addToolBar(main_toolbar)

        # Modeling toolbar
        modeling_toolbar = QToolBar("Modeling")
        modeling_toolbar.addAction(self._create_action("Beam", icon="beam.png"))
        modeling_toolbar.addAction(self._create_action("Column", icon="column.png"))
        modeling_toolbar.addAction(self._create_action("Plate", icon="plate.png"))
        self.addToolBar(modeling_toolbar)

    def _setup_docks(self):
        """Create dockable panels."""
        # Model tree dock (left)
        tree_dock = QDockWidget("Model", self)
        tree_dock.setWidget(self.model_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, tree_dock)

        # Properties dock (right)
        props_dock = QDockWidget("Properties", self)
        props_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, props_dock)

        # Claude terminal dock (bottom)
        claude_dock = QDockWidget("Claude", self)
        claude_dock.setWidget(self.claude_terminal)
        self.addDockWidget(Qt.BottomDockWidgetArea, claude_dock)
```

---

### 3.2 3D Viewport
**Priority: CRITICAL | Estimated Effort: 16 hours**

#### Tasks:
- [ ] **3.2.1** Implement OpenGL viewport with PyVista
- [ ] **3.2.2** Implement camera controls (orbit, pan, zoom)
- [ ] **3.2.3** Implement element rendering from meshes
- [ ] **3.2.4** Implement grid plane rendering
- [ ] **3.2.5** Implement element selection (click, box)
- [ ] **3.2.6** Implement element highlighting
- [ ] **3.2.7** Implement coordinate axes display
- [ ] **3.2.8** Implement view manipulation (front, top, iso)
- [ ] **3.2.9** Implement element snapping
- [ ] **3.2.10** Implement interactive element creation

#### Files to Create:
```
src/ui/viewport.py
src/ui/camera.py
src/ui/renderer.py
src/ui/selection.py
src/ui/snap.py
```

#### Viewport Spec:
```python
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

class Viewport3D(QWidget):
    """3D viewport for model visualization."""

    # Signals
    element_selected = Signal(object)  # Emitted when element clicked
    point_picked = Signal(object)      # Emitted during creation mode
    selection_changed = Signal(list)   # Emitted when selection changes

    def __init__(self, model: StructuralModel, parent=None):
        super().__init__(parent)
        self.model = model
        self._actors = {}  # element_id -> pyvista actor
        self._selected_ids = set()
        self._creation_mode = None

        self._setup_ui()
        self._setup_renderer()
        self._connect_model_signals()

    def _setup_ui(self):
        """Create layout with PyVista interactor."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create PyVista Qt interactor
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        # Configure plotter
        self.plotter.set_background('white')
        self.plotter.add_axes()
        self.plotter.enable_anti_aliasing()

    def _setup_renderer(self):
        """Configure rendering settings."""
        # Add ground grid
        self._add_grid_plane()

        # Set initial camera
        self.plotter.camera_position = 'iso'
        self.plotter.reset_camera()

    def _connect_model_signals(self):
        """Connect to model change signals."""
        self.model.element_added.connect(self._on_element_added)
        self.model.element_removed.connect(self._on_element_removed)
        self.model.element_modified.connect(self._on_element_modified)

    def _on_element_added(self, element: StructuralElement):
        """Handle element added to model."""
        mesh = element.get_mesh()
        actor = self.plotter.add_mesh(
            mesh,
            color=self._get_element_color(element),
            opacity=1.0,
            name=str(element.id)
        )
        self._actors[element.id] = actor

    def _on_element_removed(self, element: StructuralElement):
        """Handle element removed from model."""
        if element.id in self._actors:
            self.plotter.remove_actor(self._actors[element.id])
            del self._actors[element.id]

    def _on_element_modified(self, element: StructuralElement):
        """Handle element modified."""
        self._on_element_removed(element)
        self._on_element_added(element)

    def select_element(self, element_id):
        """Select element by ID."""
        pass

    def clear_selection(self):
        """Clear all selections."""
        pass

    def set_view(self, view_name: str):
        """Set standard view (front, top, right, iso)."""
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
        self.plotter.reset_camera()

    def zoom_to_selection(self):
        """Zoom to selected elements."""
        pass

    def start_beam_creation(self):
        """Enter beam creation mode."""
        self._creation_mode = 'beam'
        # Enable point picking
        self.plotter.enable_point_picking(callback=self._on_point_picked)

    def _on_point_picked(self, point):
        """Handle point picked during creation."""
        if self._creation_mode == 'beam':
            self.point_picked.emit(Point3D(*point))

    def refresh(self):
        """Force viewport refresh."""
        self.plotter.render()
```

---

### 3.3 Model Tree
**Priority: HIGH | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **3.3.1** Implement hierarchical tree view
- [ ] **3.3.2** Group elements by type
- [ ] **3.3.3** Implement drag-and-drop reordering
- [ ] **3.3.4** Implement context menus
- [ ] **3.3.5** Sync selection with viewport

#### Files to Create:
```
src/ui/model_tree.py
```

---

### 3.4 Properties Panel
**Priority: HIGH | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **3.4.1** Implement dynamic property display
- [ ] **3.4.2** Implement property editing widgets
- [ ] **3.4.3** Implement profile selector dropdown
- [ ] **3.4.4** Implement material selector dropdown
- [ ] **3.4.5** Implement multi-select property editing

#### Files to Create:
```
src/ui/properties.py
src/ui/widgets/profile_selector.py
src/ui/widgets/material_selector.py
src/ui/widgets/coordinate_input.py
```

---

### 3.5 Dialog Windows
**Priority: HIGH | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **3.5.1** Implement beam creation dialog
- [ ] **3.5.2** Implement column creation dialog
- [ ] **3.5.3** Implement grid creation dialog
- [ ] **3.5.4** Implement IFC export dialog
- [ ] **3.5.5** Implement settings dialog

#### Files to Create:
```
src/ui/dialogs/__init__.py
src/ui/dialogs/beam_dialog.py
src/ui/dialogs/column_dialog.py
src/ui/dialogs/grid_dialog.py
src/ui/dialogs/export_dialog.py
src/ui/dialogs/settings_dialog.py
```

---

## Phase 4: IFC Export Engine

### 4.1 IFC Core
**Priority: CRITICAL | Estimated Effort: 12 hours**

#### Tasks:
- [ ] **4.1.1** Implement IFC model wrapper class
- [ ] **4.1.2** Implement IFC project/site/building structure
- [ ] **4.1.3** Implement coordinate system setup
- [ ] **4.1.4** Implement unit assignment
- [ ] **4.1.5** Implement owner history
- [ ] **4.1.6** Implement geometry context

#### Files to Create:
```
src/ifc/__init__.py
src/ifc/exporter.py
src/ifc/ifc_model.py
src/ifc/ifc_utils.py
```

#### IFC Exporter Spec:
```python
import ifcopenshell
import ifcopenshell.api
from typing import List
from uuid import uuid4
import time

class IFCExporter:
    """Export Schmekla model to IFC2X3 format."""

    def __init__(self, model: StructuralModel):
        self.model = model
        self.ifc = None
        self._element_map = {}  # Schmekla ID -> IFC entity

    def export(self, file_path: str, schema: str = "IFC2X3"):
        """Export model to IFC file."""
        # Create new IFC file
        self.ifc = ifcopenshell.file(schema=schema)

        # Setup project structure
        self._create_project_structure()

        # Setup units (millimeters)
        self._setup_units()

        # Setup geometric contexts
        self._setup_contexts()

        # Export grids
        self._export_grids()

        # Export elements by type
        for element in self.model.get_all_elements():
            self._export_element(element)

        # Write to file
        self.ifc.write(file_path)

    def _create_project_structure(self):
        """Create IFC project, site, building, storey."""
        # Create project
        self.project = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcProject",
            name=self.model.name
        )

        # Create site
        self.site = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcSite",
            name="Site"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.project,
            product=self.site
        )

        # Create building
        self.building = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcBuilding",
            name="Building"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.site,
            product=self.building
        )

        # Create default storey
        self.storey = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcBuildingStorey",
            name="Ground Floor"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.building,
            product=self.storey
        )

    def _setup_units(self):
        """Setup IFC units (millimeters)."""
        ifcopenshell.api.run(
            "unit.assign_unit", self.ifc,
            length={"is_metric": True, "raw": "MILLIMETRE"},
            area={"is_metric": True, "raw": "SQUARE_METRE"},
            volume={"is_metric": True, "raw": "CUBIC_METRE"}
        )

    def _setup_contexts(self):
        """Setup geometric representation contexts."""
        self.body_context = ifcopenshell.api.run(
            "context.add_context", self.ifc,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW"
        )

    def _export_element(self, element: StructuralElement):
        """Export single element to IFC."""
        ifc_entity = element.to_ifc(self)
        self._element_map[element.id] = ifc_entity

        # Assign to storey
        ifcopenshell.api.run(
            "spatial.assign_container", self.ifc,
            relating_structure=self.storey,
            product=ifc_entity
        )

        # Assign material
        if element.material:
            self._assign_material(ifc_entity, element.material)

    def _assign_material(self, ifc_entity, material: Material):
        """Assign material to IFC entity."""
        ifc_material = ifcopenshell.api.run(
            "material.add_material", self.ifc,
            name=material.name
        )
        ifcopenshell.api.run(
            "material.assign_material", self.ifc,
            product=ifc_entity,
            material=ifc_material
        )

    def _export_grids(self):
        """Export grid lines to IFC."""
        for grid in self.model._grids:
            self._export_grid(grid)
```

---

### 4.2 Profile IFC Mapping
**Priority: CRITICAL | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **4.2.1** Implement I-section to IfcIShapeProfileDef
- [ ] **4.2.2** Implement rectangular section to IfcRectangleProfileDef
- [ ] **4.2.3** Implement circular section to IfcCircleProfileDef
- [ ] **4.2.4** Implement L-section to IfcLShapeProfileDef
- [ ] **4.2.5** Implement C-section to IfcCShapeProfileDef
- [ ] **4.2.6** Implement arbitrary profiles to IfcArbitraryClosedProfileDef
- [ ] **4.2.7** Write profile mapping tests

#### Files to Create:
```
src/ifc/ifc_profile.py
tests/unit/test_ifc_profile.py
```

#### Profile Mapping Spec:
```python
def create_ifc_profile(profile: Profile, ifc_model) -> Any:
    """Create IFC profile definition from Schmekla profile."""

    if profile.type == "I":
        return ifc_model.ifc.create_entity(
            "IfcIShapeProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            OverallWidth=profile.b,
            OverallDepth=profile.h,
            WebThickness=profile.tw,
            FlangeThickness=profile.tf,
            FilletRadius=profile.r
        )
    elif profile.type == "Rectangle":
        return ifc_model.ifc.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            XDim=profile.width,
            YDim=profile.height
        )
    elif profile.type == "Circle":
        return ifc_model.ifc.create_entity(
            "IfcCircleProfileDef",
            ProfileType="AREA",
            ProfileName=profile.name,
            Radius=profile.radius
        )
    # ... more profile types
```

---

### 4.3 Element IFC Mappers
**Priority: CRITICAL | Estimated Effort: 10 hours**

#### Tasks:
- [ ] **4.3.1** Implement beam to IfcBeam mapper
- [ ] **4.3.2** Implement column to IfcColumn mapper
- [ ] **4.3.3** Implement plate to IfcPlate mapper
- [ ] **4.3.4** Implement slab to IfcSlab mapper
- [ ] **4.3.5** Implement wall to IfcWall mapper
- [ ] **4.3.6** Implement footing to IfcFooting mapper
- [ ] **4.3.7** Comprehensive IFC export tests

#### Files to Create:
```
src/ifc/ifc_beam.py
src/ifc/ifc_column.py
src/ifc/ifc_plate.py
src/ifc/ifc_slab.py
src/ifc/ifc_wall.py
src/ifc/ifc_footing.py
tests/integration/test_ifc_export.py
```

#### Beam IFC Mapper Spec:
```python
import ifcopenshell
import ifcopenshell.api
from src.core.beam import Beam

def create_ifc_beam(beam: Beam, exporter: 'IFCExporter') -> Any:
    """Create IfcBeam from Schmekla Beam."""

    ifc = exporter.ifc

    # Create beam entity
    ifc_beam = ifcopenshell.api.run(
        "root.create_entity", ifc,
        ifc_class="IfcBeam",
        name=beam.name or f"Beam_{beam.id}"
    )

    # Create profile
    profile = create_ifc_profile(beam.profile, exporter)

    # Create axis placement (beam position/direction)
    axis_placement = create_axis_placement(
        beam.start_point,
        beam.direction,
        beam.rotation,
        ifc
    )

    # Create extruded area solid
    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=axis_placement,
        ExtrudedDirection=ifc.create_entity(
            "IfcDirection",
            DirectionRatios=[0.0, 0.0, 1.0]
        ),
        Depth=beam.length
    )

    # Create shape representation
    shape_rep = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=exporter.body_context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid]
    )

    # Create product definition shape
    product_shape = ifc.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_rep]
    )

    # Assign representation to beam
    ifc_beam.Representation = product_shape

    # Create local placement
    ifc_beam.ObjectPlacement = create_local_placement(
        beam.start_point, ifc
    )

    return ifc_beam
```

---

## Phase 5: Claude Integration

### 5.1 Claude Bridge
**Priority: HIGH | Estimated Effort: 10 hours**

#### Tasks:
- [ ] **5.1.1** Implement Claude Code CLI subprocess wrapper
- [ ] **5.1.2** Implement context builder (model state to text)
- [ ] **5.1.3** Implement command parser (text to operations)
- [ ] **5.1.4** Implement model command executor
- [ ] **5.1.5** Implement response handler
- [ ] **5.1.6** Implement conversation history management

#### Files to Create:
```
src/claude_integration/__init__.py
src/claude_integration/claude_bridge.py
src/claude_integration/context_builder.py
src/claude_integration/prompt_parser.py
src/claude_integration/model_commands.py
src/claude_integration/response_handler.py
```

#### Claude Bridge Spec:
```python
import subprocess
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

class ClaudeBridge:
    """Bridge between Schmekla and Claude Code CLI."""

    def __init__(self, model: StructuralModel):
        self.model = model
        self.conversation_history: List[Dict] = []
        self.context_builder = ContextBuilder(model)
        self.command_executor = ModelCommandExecutor(model)

    def send_prompt(self, user_prompt: str) -> str:
        """Send prompt to Claude and return response."""

        # Build full prompt with context
        full_prompt = self._build_full_prompt(user_prompt)

        # Call Claude Code CLI
        response = self._call_claude_cli(full_prompt)

        # Parse and execute any commands in response
        commands = self._extract_commands(response)
        for cmd in commands:
            self.command_executor.execute(cmd)

        # Store in history
        self.conversation_history.append({
            "role": "user",
            "content": user_prompt
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    def _build_full_prompt(self, user_prompt: str) -> str:
        """Build prompt with model context."""

        context = self.context_builder.build()

        system_prompt = f"""You are an AI assistant integrated into Schmekla, a structural modeling application.

## Current Model Context:
{context}

## Available Commands:
You can execute model commands by outputting JSON in this format:
```schmekla-command
{{"command": "create_beam", "params": {{"start": [0,0,0], "end": [6000,0,0], "profile": "UB 305x165x40"}}}}
```

Available commands:
- create_beam: Create a beam. Params: start (point), end (point), profile (string), material (string, optional)
- create_column: Create a column. Params: base (point), height (float), profile (string), material (string, optional)
- create_plate: Create a plate. Params: points (list of points), thickness (float), material (string, optional)
- modify_element: Modify element properties. Params: element_id (string), property (string), value (any)
- delete_element: Delete element. Params: element_id (string)
- select_elements: Select elements. Params: ids (list of strings)
- create_grid: Create grid lines. Params: x_spacings (list), y_spacings (list)
- create_frame: Create portal frame. Params: width (float), height (float), profile_beam (string), profile_column (string)

## Units:
All dimensions are in millimeters (mm).

## Profile Examples:
- UK I-sections: "UB 305x165x40", "UC 203x203x46"
- UK Channels: "PFC 200x90x30"
- Rectangular tubes: "RHS 200x100x10"
- Square tubes: "SHS 150x150x10"
- Circular tubes: "CHS 168.3x7.1"

## User Request:
{user_prompt}

Respond helpfully. If the user wants to create or modify model elements, include the appropriate schmekla-command blocks.
"""

        return system_prompt

    def _call_claude_cli(self, prompt: str) -> str:
        """Call Claude Code CLI and return response."""

        # Write prompt to temp file to avoid shell escaping issues
        prompt_file = Path("temp_prompt.txt")
        prompt_file.write_text(prompt, encoding='utf-8')

        try:
            result = subprocess.run(
                ["claude", "-p", str(prompt_file), "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "Error: Claude CLI timed out"
        except FileNotFoundError:
            return "Error: Claude CLI not found. Please install claude-code."
        finally:
            prompt_file.unlink(missing_ok=True)

    def _extract_commands(self, response: str) -> List[Dict]:
        """Extract schmekla-command blocks from response."""
        import re

        commands = []
        pattern = r'```schmekla-command\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            try:
                cmd = json.loads(match)
                commands.append(cmd)
            except json.JSONDecodeError:
                continue

        return commands


class ContextBuilder:
    """Build context string describing current model state."""

    def __init__(self, model: StructuralModel):
        self.model = model

    def build(self) -> str:
        """Build context string."""
        parts = []

        # Model info
        parts.append(f"Model: {self.model.name}")
        parts.append(f"Total elements: {len(self.model.get_all_elements())}")

        # Elements by type
        for elem_type in ElementType:
            elements = self.model.get_elements_by_type(elem_type)
            if elements:
                parts.append(f"\n{elem_type.value.title()}s ({len(elements)}):")
                for elem in elements[:10]:  # Limit to 10 per type
                    parts.append(f"  - {elem.name or elem.id}: {self._describe_element(elem)}")
                if len(elements) > 10:
                    parts.append(f"  ... and {len(elements) - 10} more")

        # Grids
        if self.model._grids:
            parts.append(f"\nGrids: {len(self.model._grids)}")

        # Levels
        if self.model._levels:
            parts.append(f"\nLevels: {[l.name for l in self.model._levels]}")

        return "\n".join(parts)

    def _describe_element(self, elem: StructuralElement) -> str:
        """Create short description of element."""
        if hasattr(elem, 'start_point') and hasattr(elem, 'end_point'):
            return f"{elem.profile.name}, {elem.start_point} to {elem.end_point}"
        elif hasattr(elem, 'base_point') and hasattr(elem, 'height'):
            return f"{elem.profile.name}, {elem.base_point}, h={elem.height}"
        return str(elem.profile.name if elem.profile else "Unknown")


class ModelCommandExecutor:
    """Execute commands on the model."""

    def __init__(self, model: StructuralModel):
        self.model = model
        self._commands = {
            "create_beam": self._create_beam,
            "create_column": self._create_column,
            "create_plate": self._create_plate,
            "modify_element": self._modify_element,
            "delete_element": self._delete_element,
            "select_elements": self._select_elements,
            "create_grid": self._create_grid,
            "create_frame": self._create_frame,
        }

    def execute(self, command: Dict) -> Dict:
        """Execute a command and return result."""
        cmd_name = command.get("command")
        params = command.get("params", {})

        if cmd_name in self._commands:
            try:
                return self._commands[cmd_name](params)
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown command: {cmd_name}"}

    def _create_beam(self, params: Dict) -> Dict:
        """Create beam from params."""
        start = Point3D(*params["start"])
        end = Point3D(*params["end"])
        profile = Profile.from_name(params["profile"])
        material = Material.from_name(params.get("material", "S355"))

        beam = Beam(start, end, profile, material)
        self.model.add_element(beam)

        return {"success": True, "element_id": str(beam.id)}

    def _create_column(self, params: Dict) -> Dict:
        """Create column from params."""
        base = Point3D(*params["base"])
        height = params["height"]
        profile = Profile.from_name(params["profile"])
        material = Material.from_name(params.get("material", "S355"))

        column = Column(base, height, profile, material)
        self.model.add_element(column)

        return {"success": True, "element_id": str(column.id)}

    def _create_frame(self, params: Dict) -> Dict:
        """Create portal frame from params."""
        from src.components.portal_frame import create_portal_frame

        frame_elements = create_portal_frame(
            width=params["width"],
            height=params["height"],
            beam_profile=params["profile_beam"],
            column_profile=params["profile_column"]
        )

        ids = []
        for elem in frame_elements:
            self.model.add_element(elem)
            ids.append(str(elem.id))

        return {"success": True, "element_ids": ids}

    # ... more command implementations
```

---

### 5.2 Claude UI Components
**Priority: HIGH | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **5.2.1** Implement embedded Claude terminal widget
- [ ] **5.2.2** Implement Claude prompt dialog
- [ ] **5.2.3** Implement response display with command highlighting
- [ ] **5.2.4** Implement command preview before execution
- [ ] **5.2.5** Implement conversation history viewer

#### Files to Create:
```
src/ui/widgets/claude_terminal.py
src/ui/dialogs/claude_dialog.py
```

#### Claude Terminal Widget Spec:
```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QTextCharFormat, QColor, QFont

class ClaudeTerminal(QWidget):
    """Embedded Claude terminal for natural language modeling."""

    command_executed = Signal(dict)  # Emitted when command executed

    def __init__(self, model: StructuralModel, parent=None):
        super().__init__(parent)
        self.bridge = ClaudeBridge(model)
        self._setup_ui()

    def _setup_ui(self):
        """Create terminal UI."""
        layout = QVBoxLayout(self)

        # Output display
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        layout.addWidget(self.output)

        # Input area
        input_layout = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Claude to create or modify the model...")
        self.input.returnPressed.connect(self._send_prompt)
        input_layout.addWidget(self.input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_prompt)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

    def _send_prompt(self):
        """Send prompt to Claude."""
        prompt = self.input.text().strip()
        if not prompt:
            return

        self.input.clear()

        # Show user prompt
        self._append_text(f"\n> {prompt}\n", QColor("#0066cc"))

        # Get response
        self.output.append("Thinking...")
        response = self.bridge.send_prompt(prompt)

        # Clear "Thinking..." and show response
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()

        self._append_text(response, QColor("#333333"))

        # Highlight command blocks
        self._highlight_commands(response)

    def _append_text(self, text: str, color: QColor):
        """Append colored text to output."""
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text, fmt)
        self.output.ensureCursorVisible()

    def _highlight_commands(self, text: str):
        """Highlight command blocks in output."""
        # Implementation for highlighting schmekla-command blocks
        pass
```

---

## Phase 6: Parametric Components

### 6.1 Portal Frame Generator
**Priority: MEDIUM | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **6.1.1** Implement single-span portal frame
- [ ] **6.1.2** Implement multi-span portal frame
- [ ] **6.1.3** Implement haunched rafter option
- [ ] **6.1.4** Implement parameter validation
- [ ] **6.1.5** Write portal frame tests

#### Files to Create:
```
src/components/__init__.py
src/components/base_component.py
src/components/portal_frame.py
tests/unit/test_portal_frame.py
```

---

### 6.2 Bracing System
**Priority: MEDIUM | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **6.2.1** Implement X-bracing pattern
- [ ] **6.2.2** Implement K-bracing pattern
- [ ] **6.2.3** Implement single diagonal bracing

#### Files to Create:
```
src/components/bracing.py
```

---

### 6.3 Floor Framing System
**Priority: MEDIUM | Estimated Effort: 6 hours**

#### Tasks:
- [ ] **6.3.1** Implement secondary beam layout
- [ ] **6.3.2** Implement purlin/girt placement
- [ ] **6.3.3** Implement metal deck representation

#### Files to Create:
```
src/components/floor_system.py
src/components/purlin_system.py
```

---

## Phase 7: Testing & Validation

### 7.1 Unit Tests
**Priority: HIGH | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **7.1.1** Geometry tests (points, vectors, transforms)
- [ ] **7.1.2** Element tests (beam, column, plate creation)
- [ ] **7.1.3** Profile tests (loading, properties)
- [ ] **7.1.4** Model tests (add, remove, modify)
- [ ] **7.1.5** Serialization tests (save, load)

---

### 7.2 Integration Tests
**Priority: HIGH | Estimated Effort: 8 hours**

#### Tasks:
- [ ] **7.2.1** IFC export validation (schema compliance)
- [ ] **7.2.2** IFC import to Tekla verification (manual)
- [ ] **7.2.3** Claude integration tests
- [ ] **7.2.4** UI interaction tests

---

### 7.3 Tekla Import Validation
**Priority: CRITICAL | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **7.3.1** Export simple beam model, import to Tekla
- [ ] **7.3.2** Verify beam converts to native Tekla beam
- [ ] **7.3.3** Verify profile recognized
- [ ] **7.3.4** Verify material assigned
- [ ] **7.3.5** Test multi-element model
- [ ] **7.3.6** Document any conversion issues

---

## Phase 8: Documentation & Polish

### 8.1 User Documentation
**Priority: MEDIUM | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **8.1.1** Write README with quick start
- [ ] **8.1.2** Write user guide
- [ ] **8.1.3** Document Claude commands
- [ ] **8.1.4** Create example scripts

---

### 8.2 Code Documentation
**Priority: MEDIUM | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **8.2.1** Add docstrings to all public APIs
- [ ] **8.2.2** Generate API reference
- [ ] **8.2.3** Document architecture decisions

---

### 8.3 Build & Distribution
**Priority: LOW | Estimated Effort: 4 hours**

#### Tasks:
- [ ] **8.3.1** Create PyInstaller spec
- [ ] **8.3.2** Build Windows executable
- [ ] **8.3.3** Create installer

---

## Implementation Order Summary

### Week 1-2: Foundation
1. Project setup (1.1)
2. Geometry foundation (1.2)
3. Core data model (1.3)

### Week 3-4: Elements & UI
4. Beam element (2.1)
5. Column element (2.2)
6. Main window framework (3.1)
7. 3D Viewport (3.2)

### Week 5-6: IFC & More Elements
8. IFC core (4.1)
9. Profile IFC mapping (4.2)
10. Element IFC mappers (4.3)
11. Plate, slab, wall elements (2.3-2.5)

### Week 7-8: Claude & Components
12. Claude bridge (5.1)
13. Claude UI (5.2)
14. Portal frame generator (6.1)

### Week 9-10: Testing & Polish
15. Unit tests (7.1)
16. Integration tests (7.2)
17. Tekla validation (7.3)
18. Documentation (8.1-8.2)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| IFC not compatible with Tekla | Test early and often with Tekla imports |
| OpenCascade complexity | Use CadQuery abstraction layer |
| Claude CLI changes | Abstract CLI calls behind interface |
| Performance with large models | Implement LOD, frustum culling |
| Profile catalog incomplete | Start with UK sections, expand as needed |

---

## Success Criteria

- [ ] Create beam/column model in Schmekla
- [ ] Export to IFC2X3
- [ ] Import IFC to Tekla Structures
- [ ] Convert to native Tekla objects
- [ ] Objects are fully editable in Tekla
- [ ] Claude can create elements via natural language

---

*Implementation plan version 1.0 - Last updated: January 2026*
 
 - - -  
  
 # #   P h a s e   4 :   A I   &   K n o w l e d g e   I n g e s t i o n  
 * * P r i o r i t y :   H I G H   |   E s t i m a t e d   E f f o r t :   1 6   h o u r s * *  
  
 # # #   4 . 1   D o c u m e n t   P r o c e s s o r  
 # # # #   T a s k s :  
 -   [   ]   * * 4 . 1 . 1 * *   I m p l e m e n t   ` D o c u m e n t P r o c e s s o r `   c l a s s   f o r   P D F s   ( P y M u P D F )  
 -   [   ]   * * 4 . 1 . 2 * *   I m p l e m e n t   ` D r a w i n g P r o c e s s o r `   c l a s s   f o r   D W G s   ( e z d x f )  
 -   [   ]   * * 4 . 1 . 3 * *   c r e a t e   t e x t   c h u n k i n g   s t r a t e g y   ( s e m a n t i c   s p l i t t i n g )  
  
 # # #   4 . 2   V e c t o r   S t o r e  
 # # # #   T a s k s :  
 -   [   ]   * * 4 . 2 . 1 * *   I m p l e m e n t   ` V e c t o r S t o r e `   i n t e r f a c e   ( a b s t r a c t   b a s e )  
 -   [   ]   * * 4 . 2 . 2 * *   I m p l e m e n t   C h r o m a D B   a d a p t e r   ( l o c a l   s t o r a g e )  
 -   [   ]   * * 4 . 2 . 3 * *   I m p l e m e n t   P i n e c o n e   a d a p t e r   ( o p t i o n a l   c l o u d   s t o r a g e )  
  
 # # #   4 . 3   E m b e d d i n g s  
 # # # #   T a s k s :  
 -   [   ]   * * 4 . 3 . 1 * *   I m p l e m e n t   ` E m b e d d i n g G e n e r a t o r `   u s i n g   g e n e r i c   m o d e l   o u t p u t   ( e . g .   O p e n A I / V o y a g e   v i a   c o n f i g )  
  
 # # #   4 . 4   R A G   E n g i n e  
 # # # #   T a s k s :  
 -   [   ]   * * 4 . 4 . 1 * *   I m p l e m e n t   ` R A G E n g i n e `   t o   o r c h e s t r a t e   r e t r i e v a l  
 -   [   ]   * * 4 . 4 . 2 * *   C o n n e c t   R A G   e n g i n e   t o   C l a u d e   B r i d g e  
  
 - - -  
  
 # #   P h a s e   5 :   I n t e r a c t i v e   U I   &   S e l e c t i o n   M a n a g e r  
 * * P r i o r i t y :   H I G H   |   E s t i m a t e d   E f f o r t :   1 2   h o u r s * *  
  
 # # #   5 . 1   I n t e r a c t i o n   M a n a g e r   ( ` s r c / u i / i n t e r a c t i o n . p y ` )  
 C e n t r a l i z e d   s t a t e   m a c h i n e   h a n d l i n g   m o u s e   c l i c k s   a n d   c o m m a n d   m o d e s .  
  
 # # # #   S t a t e s :  
 -   * * I D L E * * :   L e f t   c l i c k   s e l e c t s   e l e m e n t s   ( r a y c a s t i n g   f r o m   c a m e r a ) .  
 -   * * C R E A T E _ B E A M * * :  
     -   S t e p   1 :   " P i c k   s t a r t   p o i n t "  
     -   S t e p   2 :   " P i c k   e n d   p o i n t "   - >   C r e a t e   B e a m   - >   R e t u r n   t o   I D L E   ( o r   l o o p ) .  
 -   * * C R E A T E _ C O L U M N * * :  
     -   S t e p   1 :   " P i c k   p o s i t i o n "   - >   C r e a t e   C o l u m n   ( h e i g h t   f r o m   p r o p e r t i e s )   - >   R e t u r n   t o   I D L E .  
  
 # # # #   T a s k s :  
 -   [   ]   * * 5 . 1 . 1 * *   I m p l e m e n t   ` I n t e r a c t i o n M a n a g e r `   c l a s s   ( S i g n a l - b a s e d ) .  
 -   [   ]   * * 5 . 1 . 2 * *   I m p l e m e n t   ` S e l e c t i o n M a n a g e r `   f o r   h i g h l i g h t i n g / t r a c k i n g   s e l e c t e d   U U I D s .  
 -   [   ]   * * 5 . 1 . 3 * *   U p d a t e   ` V i e w p o r t 3 D `   t o   f o r w a r d   m o u s e   e v e n t s   t o   ` I n t e r a c t i o n M a n a g e r ` .  
  
 # # #   5 . 2   R a y c a s t i n g   &   P i c k i n g  
 # # # #   T a s k s :  
 -   [   ]   * * 5 . 2 . 1 * *   I m p l e m e n t   ` s c r e e n _ t o _ w o r l d ( x ,   y ) `   i n   ` V i e w p o r t 3 D `   u s i n g   P y V i s t a / V T K   p i c k e r .  
 -   [   ]   * * 5 . 2 . 2 * *   I m p l e m e n t   " S n a p   t o   G r i d "   l o g i c   ( o p t i o n a l   b u t   r e c o m m e n d e d   f o r   T e k l a - f e e l ) .  
  
 # # #   5 . 3   C o m m a n d   T o o l s  
 # # # #   T a s k s :  
 -   [   ]   * * 5 . 3 . 1 * *   U p d a t e   T o o l b a r   a c t i o n s   t o   s e t   ` I n t e r a c t i o n M a n a g e r `   s t a t e   i n s t e a d   o f   c r e a t i n g   d u m m y   o b j e c t s   i m m e d i a t e l y .  
 -   [   ]   * * 5 . 3 . 2 * *   A d d   s t a t u s   b a r   p r o m p t s   ( " P i c k   s t a r t   p o i n t . . . " ) .  
 