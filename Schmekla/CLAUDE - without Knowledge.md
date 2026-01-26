# CLAUDE.md - Schmekla Development Guide

## Project Overview

**Schmekla** is a custom structural modeling application designed to create 3D structural steel/concrete models and export them to IFC format for import into Tekla Structures. The application includes Claude Code CLI integration for natural language model creation and modification.

## Quick Start for Claude Code

```bash
# Navigate to project
cd Schmekla

# Option 1: Use install script (recommended)
deploy\install.bat

# Option 2: Manual setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the application
python -m src.main
```

## Deployment

**IMPORTANT**: The `venv/` folder is NOT portable between machines.

### Files to Deploy (copy these):
```
Schmekla/
├── src/
├── resources/
├── deploy/
├── Conditions/          # Project-specific data
├── requirements.txt
├── pyproject.toml
├── README.md
├── CLAUDE.md
└── run_schmekla.bat     # (created by install.bat)
```

### Files to EXCLUDE:
```
venv/                    # Contains machine-specific paths
__pycache__/             # Python cache
.claude/settings.local.json  # Machine-specific settings
*.pyc
output/                  # Generated IFC files
```

### On Target Machine:
```bash
cd Schmekla
deploy\install.bat       # Creates venv, installs deps
run_schmekla.bat         # Launch application
```

## Project Structure

```
Schmekla/
├── CLAUDE.md                 # This file - Claude Code instructions
├── README.md                 # User-facing documentation
├── IMPLEMENTATION_PLAN.md    # Detailed implementation roadmap
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── setup.py                 # Package setup
├── .gitignore               # Git ignore (excludes venv, cache, etc.)
├── run_schmekla.bat         # Launcher script (created by install.bat)
│
├── deploy/                  # Deployment scripts
│   └── install.bat          # Auto-install script for new machines
│
├── Conditions/              # Project data folder (client specs, drawings)
│   └── For Installers/      # Installer documentation
│
├── src/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── app.py               # Main application class
│   │
│   ├── core/                # Core data models
│   │   ├── __init__.py
│   │   ├── model.py         # StructuralModel - main document
│   │   ├── project.py       # Project management
│   │   ├── element.py       # Base structural element class
│   │   ├── beam.py          # Beam element
│   │   ├── column.py        # Column element
│   │   ├── plate.py         # Plate element
│   │   ├── slab.py          # Slab element
│   │   ├── wall.py          # Wall element
│   │   ├── footing.py       # Footing element
│   │   ├── grid.py          # Grid system
│   │   ├── level.py         # Building levels
│   │   ├── material.py      # Material definitions
│   │   └── profile.py       # Section profiles
│   │
│   ├── geometry/            # Geometric operations
│   │   ├── __init__.py
│   │   ├── point.py         # Point3D class
│   │   ├── vector.py        # Vector3D class
│   │   ├── line.py          # Line/segment class
│   │   ├── plane.py         # Plane class
│   │   ├── transform.py     # Transformation matrices
│   │   ├── solid.py         # Solid geometry operations
│   │   ├── boolean.py       # Boolean operations
│   │   └── mesh.py          # Mesh generation for display
│   │
│   ├── ui/                  # User interface (PySide6)
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main application window
│   │   ├── viewport.py      # 3D OpenGL viewport
│   │   ├── model_tree.py    # Model hierarchy tree
│   │   ├── properties.py    # Properties panel
│   │   ├── toolbar.py       # Tool bars
│   │   ├── ribbon.py        # Ribbon interface
│   │   ├── dialogs/         # Dialog windows
│   │   │   ├── __init__.py
│   │   │   ├── beam_dialog.py
│   │   │   ├── column_dialog.py
│   │   │   ├── plate_dialog.py
│   │   │   ├── grid_dialog.py
│   │   │   ├── profile_dialog.py
│   │   │   ├── material_dialog.py
│   │   │   ├── export_dialog.py
│   │   │   ├── plan_import_dialog.py # Plan upload & auto-generate
│   │   │   └── claude_dialog.py      # Claude prompt interface
│   │   ├── widgets/         # Custom widgets
│   │   │   ├── __init__.py
│   │   │   ├── coordinate_input.py
│   │   │   ├── profile_selector.py
│   │   │   ├── material_selector.py
│   │   │   └── claude_terminal.py    # Claude CLI launcher widget
│   │   └── styles/          # QSS stylesheets
│   │       └── dark_theme.qss
│   │
│   ├── ifc/                 # IFC export functionality
│   │   ├── __init__.py
│   │   ├── exporter.py      # Main IFC export class
│   │   ├── ifc_model.py     # IFC model wrapper
│   │   ├── ifc_beam.py      # Beam to IFC conversion
│   │   ├── ifc_column.py    # Column to IFC conversion
│   │   ├── ifc_plate.py     # Plate to IFC conversion
│   │   ├── ifc_slab.py      # Slab to IFC conversion
│   │   ├── ifc_wall.py      # Wall to IFC conversion
│   │   ├── ifc_footing.py   # Footing to IFC conversion
│   │   ├── ifc_profile.py   # Profile definitions for IFC
│   │   ├── ifc_material.py  # Material mapping for IFC
│   │   ├── ifc_grid.py      # Grid export to IFC
│   │   └── ifc_utils.py     # IFC utility functions
│   │
│   ├── claude_integration/  # Claude Code CLI integration
│   │   ├── __init__.py
│   │   ├── claude_bridge.py # Bridge to Claude Code CLI
│   │   ├── plan_analyzer.py # Analyze drawings with Claude Vision
│   │   ├── prompt_parser.py # Parse natural language to commands
│   │   ├── model_commands.py# Execute model modifications
│   │   ├── context_builder.py# Build context for Claude
│   │   └── response_handler.py# Handle Claude responses
│   │
│   ├── components/          # Parametric component library
│   │   ├── __init__.py
│   │   ├── base_component.py
│   │   ├── portal_frame.py  # Portal frame generator
│   │   ├── bracing.py       # Bracing patterns
│   │   ├── purlin_system.py # Purlin/girt system
│   │   └── floor_system.py  # Floor framing system
│   │
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── config.py        # Configuration management
│       ├── logger.py        # Logging setup
│       ├── units.py         # Unit conversion
│       ├── serialization.py # Save/load project files
│       └── validators.py    # Input validation
│
├── resources/               # Static resources
│   ├── icons/              # UI icons
│   ├── profiles/           # Steel profile databases
│   │   ├── uk_sections.json
│   │   ├── eu_sections.json
│   │   └── us_sections.json
│   └── materials/          # Material databases
│       └── materials.json
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── unit/
│   │   ├── test_geometry.py
│   │   ├── test_elements.py
│   │   └── test_ifc_export.py
│   └── integration/
│       ├── test_model_operations.py
│       └── test_claude_integration.py
│
├── docs/                    # Documentation
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── data_model.md
│   │   └── ifc_mapping.md
│   └── api/
│       └── api_reference.md
│
└── examples/                # Example scripts
    ├── simple_frame.py
    ├── portal_frame.py
    └── multi_story.py
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Primary development language |
| UI Framework | PySide6 (Qt 6) | Desktop GUI |
| 3D Rendering | PyVista + VTK | 3D viewport |
| Geometry Kernel | CadQuery + OCC | Parametric solid modeling |
| IFC Export | IfcOpenShell | IFC file generation |
| Claude Integration | subprocess + API | AI-assisted modeling |

## Key Design Decisions

### 1. Element-Based Architecture
All structural elements inherit from `StructuralElement` base class:
- Unique identifier (UUID)
- Geometric representation (solid + mesh)
- Properties (material, profile, etc.)
- IFC mapping information

### 2. Observer Pattern for UI Updates
Model changes emit signals that update:
- 3D viewport
- Model tree
- Properties panel

### 3. Command Pattern for Undo/Redo
All model modifications go through command objects:
- `CreateElementCommand`
- `ModifyElementCommand`
- `DeleteElementCommand`
- `TransformElementCommand`

### 4. IFC Export Strategy
Export uses IFC2X3 (Tekla certified):
- Each element type has dedicated IFC mapper
- Profiles map to IfcParameterizedProfileDef where possible
- Materials map to IfcMaterial with properties

## Claude Integration Architecture

Schmekla integrates with Claude Code CLI in two ways:

### 1. External Terminal Launcher (Primary - Full Interactive)

The Claude Terminal panel in Schmekla launches Claude CLI in a proper terminal window:

```
┌─────────────────────────────────────────────┐
│  Schmekla Application                        │
│  ┌───────────────────────────────────────┐  │
│  │  Claude Terminal Panel                 │  │
│  │  [🚀 Open Claude in Terminal]          │  │
│  │  [📂 Open in Conditions Folder]        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    ▼ Opens Windows Terminal / cmd.exe
┌─────────────────────────────────────────────┐
│  Claude Code CLI (Full Interactive)          │
│  - Full file read/write access               │
│  - Permission prompts visible                │
│  - Can modify Schmekla code                  │
│  - Can read project files (Conditions, etc.) │
└─────────────────────────────────────────────┘
```

**Key files:**
- `src/ui/widgets/claude_terminal.py` - Terminal launcher widget

### 2. Programmatic Bridge (For Plan Import)

For automated tasks like plan analysis:

```
User Uploads Plan Image (PNG/JPG/PDF)
        │
        ▼
┌─────────────────────────┐
│   PlanAnalyzer          │
│   - Call Claude CLI     │
│   - --print mode        │
│   - Pass image + prompt │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   ClaudeBridge          │
│   - Parse JSON commands │
│   - Execute on model    │
│   - Auto-read files     │
└───────────┬─────────────┘
            │
            ▼
    Model Updated + UI Refresh
```

**Key files:**
- `src/claude_integration/claude_bridge.py` - Programmatic CLI bridge with file reading
- `src/claude_integration/plan_analyzer.py` - Vision-based plan analysis

## Plan Import Architecture (Vision-Based Auto-Generation)

The Plan Import feature uses Claude's vision capabilities to analyze structural drawings and automatically generate models:

```
User Uploads Plan Image (PNG/JPG/PDF)
        │
        ▼
┌─────────────────────────┐
│   PlanImportDialog      │
│   - File selection      │
│   - Plan type setting   │
│   - Scale setting       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   AnalysisWorker        │
│   (QThread background)  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   PlanAnalyzer          │
│   - Call Claude CLI     │
│   - Pass image + prompt │
│   - Parse JSON response │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   ClaudeBridge          │
│   - Execute commands    │
│   - Create elements     │
│   - Track created items │
└───────────┬─────────────┘
            │
            ▼
    Model Populated + 3D View Updated
```

### Supported Plan Types

| Plan Type | Detection Capabilities |
|-----------|------------------------|
| Floor Plan | Columns at grid intersections, beam layouts, wall locations |
| Elevation View | Vertical element heights, level positions |
| Grid Layout | Grid line positions and spacings |
| Section View | Cross-section dimensions, internal structure |

### Key Files

- `src/claude_integration/plan_analyzer.py` - Vision analysis and command generation
- `src/ui/dialogs/plan_import_dialog.py` - User interface for plan upload
- `src/claude_integration/claude_bridge.py` - Command execution

## Common Development Tasks

### Adding a New Element Type

1. Create class in `src/core/new_element.py`:
```python
from src.core.element import StructuralElement

class NewElement(StructuralElement):
    element_type = "NEW_ELEMENT"

    def __init__(self, ...):
        super().__init__()
        # Element-specific initialization

    def generate_solid(self):
        # Return OCC solid geometry
        pass

    def to_ifc(self, ifc_model):
        # Return IFC entity
        pass
```

2. Create IFC mapper in `src/ifc/ifc_new_element.py`

3. Add dialog in `src/ui/dialogs/new_element_dialog.py`

4. Register in element factory

5. Add tests in `tests/unit/test_new_element.py`

### Adding a Claude Command

1. Add command definition to `src/claude_integration/model_commands.py`:
```python
@register_command("create_beam")
def create_beam_command(model, params):
    """Create a beam from start to end point."""
    start = Point3D(*params["start"])
    end = Point3D(*params["end"])
    profile = params.get("profile", "UB 305x165x40")
    beam = Beam(start, end, profile)
    model.add_element(beam)
    return {"success": True, "element_id": str(beam.id)}
```

2. Update context in `src/claude_integration/context_builder.py`

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_geometry.py

# With coverage
pytest --cov=src
```

### Building Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile --windowed src/main.py --name Schmekla
```

## IFC Export Checklist

For Tekla compatibility, ensure:

- [ ] IFC schema version is IFC2X3
- [ ] All elements have valid IfcGloballyUniqueId
- [ ] Profiles use IfcParameterizedProfileDef when possible
- [ ] Materials have IfcMaterial assigned
- [ ] Coordinate system matches expected orientation
- [ ] Units are consistent (millimeters recommended)
- [ ] Property sets include required attributes

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints for all public methods
- Docstrings for all classes and public methods
- Maximum line length: 100 characters

### Naming Conventions
- Classes: PascalCase (`StructuralElement`)
- Functions/methods: snake_case (`create_beam`)
- Constants: UPPER_SNAKE_CASE (`DEFAULT_MATERIAL`)
- Private: leading underscore (`_internal_method`)

### Error Handling
- Use custom exceptions from `src/utils/exceptions.py`
- Always log errors before raising
- Provide meaningful error messages

## Dependencies Quick Reference

```python
# Core
import ifcopenshell           # IFC creation
from OCC.Core import ...      # OpenCascade geometry
import cadquery as cq         # High-level CAD

# UI
from PySide6.QtWidgets import ...
from PySide6.QtCore import ...
from PySide6.QtOpenGL import ...
import pyvista as pv          # 3D visualization

# Utils
import numpy as np            # Numerical operations
from loguru import logger     # Logging
```

## Debugging Tips

### 3D Viewport Issues
- Check OpenGL context is created before rendering
- Verify mesh normals are correct
- Use `pyvista.global_theme.background = 'white'` for visibility

### IFC Export Issues
- Use IFC viewer (BIM Vision, FZK Viewer) to inspect output
- Check `ifcopenshell.validate` for schema compliance
- Log all IFC entity creations

### Claude Integration Issues
- Test CLI bridge independently first
- Log full prompts and responses
- Validate JSON responses before parsing

## Contact & Resources

- IfcOpenShell docs: https://ifcopenshell.org/
- PySide6 docs: https://doc.qt.io/qtforpython/
- CadQuery docs: https://cadquery.readthedocs.io/
- PyVista docs: https://docs.pyvista.org/

---

**Note for Claude Code:** When implementing features, always:
1. Read existing code patterns first
2. Follow established architecture
3. Add tests for new functionality
4. Update this CLAUDE.md if architecture changes
