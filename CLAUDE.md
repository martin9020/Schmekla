# CLAUDE.md - Schmekla Development Guide

## IMPORTANT: Session Startup Protocol

**Before starting any work, read these files to restore context:**

1. **`knowledge/LEARNED.md`** - Accumulated technical knowledge and lessons learned
2. **`projects/*/PROJECT_CONTEXT.md`** - Context for specific projects user mentions

Example: If user says "continue with Domino project", read:
- `projects/704216_domino_printing/PROJECT_CONTEXT.md`

**Before ending a session with significant work:**
1. Update `knowledge/LEARNED.md` with any new technical discoveries
2. Create/update `projects/{job}_{client}/PROJECT_CONTEXT.md` for the project

This ensures knowledge persists across Claude's context window limitations.

---

## Project Overview

**Schmekla** is a custom structural modeling application designed to create 3D structural steel/concrete models and export them to IFC format for import into Tekla Structures. The application includes Claude Code CLI integration for natural language model creation and modification.

**Version:** 0.1.0
**Target Platform:** Windows 10/11
**Python:** 3.12+ (also compatible with 3.11+)
**Status:** Alpha / Active Development

## Quick Start for Claude Code

```bash
# Navigate to project
cd Schmekla-Test-Launch

# Option 1: One-click launcher (recommended)
Schmekla.bat

# Option 2: Manual setup
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
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
├── Schmekla.bat         # One-click launcher
├── README.md
└── CLAUDE.md
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
Schmekla.bat             # Creates venv, installs deps, launches app
```

## Project Structure

```
Schmekla/
├── CLAUDE.md                 # This file - Claude Code instructions
├── README.md                 # User-facing documentation
├── IMPLEMENTATION_PLAN.md    # Detailed implementation roadmap
├── DEVLOG.md                 # Development log for cross-AI session tracking
├── requirements.txt          # Python dependencies (83 packages)
├── pyproject.toml            # Project configuration
├── Schmekla.bat              # One-click launcher (venv + deps + launch)
├── .gitignore                # Git ignore (excludes venv, cache, etc.)
│
├── .claude/                  # Claude Code agent profiles & settings
│   ├── agents/               # 12 specialized agent definitions
│   │   ├── schmekla-boss.md      # Orchestrator (Opus)
│   │   ├── schmekla-architect.md # System Designer (Opus, renamed from architect.md)
│   │   ├── schmekla-researcher.md# Investigation Specialist (Sonnet)
│   │   ├── schmekla-coder.md     # General Implementation (Sonnet)
│   │   ├── schmekla-vtk.md       # PyVista/VTK Specialist (Sonnet)
│   │   ├── schmekla-ifc.md       # IFC/Structural Domain Expert (Sonnet)
│   │   ├── schmekla-tester.md    # Test Automation (Haiku)
│   │   ├── schmekla-reviewer.md  # Code Quality (Haiku)
│   │   ├── schmekla-security.md  # Security Audit (Sonnet)
│   │   ├── schmekla-debugger.md  # Error Resolution (Haiku)
│   │   ├── schmekla-documenter.md# Documentation (Haiku)
│   │   └── schmekla-devops.md    # Release Management (Haiku)
│   ├── package-manager.json
│   └── settings.json
│
├── knowledge/                # Knowledge base for session continuity
│   ├── LEARNED.md            # Technical lessons learned
│   ├── SESSION_*.md          # Session notes
│   └── Last Conversation.txt # Previous session transcript
│
├── deploy/                   # Deployment scripts
│   └── install.bat           # Auto-install script for new machines
│
├── Conditions/               # Project data folder (client specs, drawings)
│   └── For Installers/       # Installer documentation
│
├── src/
│   ├── __init__.py
│   ├── main.py               # Application entry point
│   │
│   ├── core/                 # Core data models
│   │   ├── __init__.py
│   │   ├── model.py          # StructuralModel - main document
│   │   ├── element.py        # Base structural element class
│   │   ├── beam.py           # Beam element
│   │   ├── column.py         # Column element
│   │   ├── plate.py          # Plate element
│   │   ├── slab.py           # Slab element
│   │   ├── wall.py           # Wall element
│   │   ├── footing.py        # Footing element
│   │   ├── bolt.py           # BoltGroup connection element
│   │   ├── weld.py           # Weld connection element
│   │   ├── curved_beam.py    # Curved beam (barrel roofs)
│   │   ├── grid.py           # Grid system
│   │   ├── level.py          # Building levels
│   │   ├── drawing.py        # Drawing entities
│   │   ├── drawing_manager.py # Drawing management logic
│   │   ├── numbering.py      # Tekla-style part numbering
│   │   ├── snap_manager.py   # Snap-to-grid/endpoint functionality
│   │   ├── material.py       # Material definitions
│   │   ├── profile.py        # Section profiles/catalogs
│   │   └── commands/         # Command pattern implementations
│   │       └── numbering_commands.py
│   │
│   ├── geometry/             # 3D geometry operations
│   │   ├── __init__.py
│   │   ├── point.py          # Point3D class
│   │   ├── vector.py         # Vector3D class
│   │   ├── line.py           # Line/segment class
│   │   ├── plane.py          # Plane class
│   │   └── transform.py      # Transformation matrices
│   │
│   ├── drawing/              # Drawing generation engine
│   │   └── view_generator.py # 2D projection engine
│   │
│   ├── ui/                   # User interface (PySide6)
│   │   ├── __init__.py
│   │   ├── main_window.py    # Main application window
│   │   ├── viewport.py       # 3D PyVista/VTK viewport
│   │   ├── interaction.py    # Interactive element creation modes
│   │   ├── dialogs/          # Dialog windows
│   │   │   ├── __init__.py
│   │   │   ├── beam_dialog.py
│   │   │   ├── column_dialog.py
│   │   │   ├── plate_dialog.py
│   │   │   ├── grid_dialog.py
│   │   │   ├── plan_import_dialog.py  # Plan upload & auto-generate
│   │   │   ├── export_dialog.py       # IFC export settings
│   │   │   ├── batch_edit_dialog.py   # Multi-element batch editing
│   │   │   └── numbering_dialog.py    # Tekla-style numbering config
│   │   ├── windows/          # Application windows
│   │   │   ├── __init__.py
│   │   │   ├── drawing_list_window.py  # Drawing List (Ctrl+L)
│   │   │   └── drawing_editor_window.py # Drawing Editor
│   │   └── widgets/          # Custom widgets
│   │       ├── __init__.py
│   │       ├── claude_terminal.py      # Claude CLI launcher widget
│   │       └── properties_panel.py     # Tekla-style properties panel
│   │
│   ├── ifc/                  # IFC export functionality
│   │   ├── __init__.py
│   │   ├── exporter.py       # Main IFC export class
│   │   ├── ifc_beam.py       # Beam → IFC conversion
│   │   ├── ifc_column.py     # Column → IFC conversion
│   │   ├── ifc_plate.py      # Plate → IFC conversion
│   │   ├── ifc_slab.py       # Slab → IFC conversion
│   │   ├── ifc_wall.py       # Wall → IFC conversion
│   │   ├── ifc_footing.py    # Footing → IFC conversion
│   │   ├── ifc_curved_beam.py # Curved beam → IFC
│   │   └── ifc_grid.py       # Grid → IFC
│   │
│   ├── claude_integration/   # Claude Code CLI integration
│   │   ├── __init__.py
│   │   ├── claude_bridge.py  # Programmatic CLI bridge
│   │   └── plan_analyzer.py  # Vision-based plan analysis
│   │
│   ├── ai/                   # AI/ML modules
│   │   ├── document_processor.py
│   │   ├── dwg_processor.py
│   │   ├── embeddings.py
│   │   ├── rag_engine.py
│   │   └── vector_store.py
│   │
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── config.py         # Configuration management
│       ├── logger.py         # Logging setup
│       └── units.py          # Unit conversion
│
├── resources/                # Static resources
│   ├── icons/               # UI icons
│   ├── profiles/            # Steel profile databases
│   │   ├── uk_sections.json  # 31 UK profiles
│   │   ├── eu_sections.json
│   │   └── us_sections.json
│   └── materials/           # Material databases
│       └── materials.json    # 7 standard materials
│
├── tests/                    # Test suite (pytest)
│   ├── __init__.py
│   ├── unit/
│   └── integration/
│
├── output/                   # Generated IFC export files
├── projects/                 # Project context files
└── docs/                     # Documentation
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.12+ (3.11+ compatible) | Primary development language |
| UI Framework | PySide6 (Qt 6) | Desktop GUI |
| 3D Rendering | PyVista + VTK | 3D viewport |
| Geometry Kernel | CadQuery + OCP (cadquery-ocp) | Parametric solid modeling |
| IFC Export | IfcOpenShell 0.8+ | IFC file generation |
| Claude Integration | subprocess + API | AI-assisted modeling |
| PDF Processing | PyMuPDF | Plan drawing import |

### CRITICAL: OCP Import Convention

The OpenCascade bindings come from `cadquery-ocp`, which uses the `OCP` namespace (**NOT** `OCC.Core`):

```python
# CORRECT:
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepBndLib import BRepBndLib
BRepBndLib.Add_s(solid, bbox)        # Note: static method with _s suffix
BRep_Tool.Triangulation_s(face, loc) # Same pattern for all static methods

# WRONG (old pythonocc convention - DO NOT USE):
from OCC.Core.gp import gp_Pnt   # WILL FAIL
```

## Agent Ecosystem

Schmekla uses a 12-agent orchestration system defined in `.claude/agents/`:

### Orchestration Layer (Opus)
| Agent | Role | Key Responsibility |
|-------|------|--------------------|
| **schmekla-boss** | Project Manager | Task decomposition, coordination, quality gates |
| **schmekla-architect** | System Designer | Architecture design, trade-off analysis |

### Implementation Layer (Sonnet)
| Agent | Role | Key Responsibility |
|-------|------|--------------------|
| **schmekla-researcher** | Investigation | Bug tracing, API research, code exploration (read-only) |
| **schmekla-coder** | General Dev | Python implementation, environment setup, dependency management |
| **schmekla-vtk** | VTK Specialist | 3D viewport, picking, coordinate transforms, VTK actors |
| **schmekla-ifc** | IFC Expert | IFC export, IfcOpenShell, Tekla compatibility |
| **schmekla-security** | Security Audit | Vulnerability detection, dependency scanning |

### Quality Assurance Layer (Haiku)
| Agent | Role | Key Responsibility |
|-------|------|--------------------|
| **schmekla-tester** | Test Automation | pytest, pytest-qt, coverage (80%+ target) |
| **schmekla-reviewer** | Code Quality | Pattern compliance, code review |
| **schmekla-debugger** | Error Resolution | Minimal-diff surgical fixes |
| **schmekla-documenter** | Documentation | LEARNED.md, DEVLOG.md, phase tracking |
| **schmekla-devops** | Release Mgmt | Environment, builds, packaging, versioning |

### Quality Gates
| Gate | Name | When |
|------|------|------|
| QG-01 | Requirements Validation | Before design |
| QG-02 | Design Review | Before implementation |
| QG-03 | Build Verification | After code changes |
| QG-04 | Code Review | Before merge |
| QG-05 | Test Coverage | Before feature complete |
| QG-06 | Security Scan | Before release |
| QG-07 | Documentation Check | Before feature complete |
| QG-08 | Application Verification | Before task closure |

### Workflow Patterns
- **New Feature:** Boss → Architect → [Coder/VTK/IFC] → Tester → Reviewer → Boss
- **Bug Fix:** Boss → Researcher → Debugger → Tester → Reviewer → Boss
- **Release:** Boss → Tester → Security → Reviewer → Documenter → DevOps → Boss

## Recent Features (Jan 2026)

### 1. Connection Elements
- **BoltGroup**: Parametric bolt arrays (linear/grid). Interactive creation via "Modeling" > "Create Bolt Group" or toolbar.
  - One-click origin selection.
  - Visualization: Grey cylinders.
- **Weld**: Logical weld connections between Main and Secondary parts. Interactive creation via "Modeling" > "Create Weld".
  - Two-step selection (Main Part -> Secondary Part).
  - Visualization: Magenta spheres at connection point.

### 2. Interactive Modeling Workflows
- **Two-Point Creation**: Beams (pick start + end).
- **One-Click Creation**: Columns, Bolt Groups (pick position).
- **Two-Step Selection**: Welds (select main part → secondary part).
- **Multi-Point Creation**: Plates (pick 4 corner points).
- **Copy/Move Modes**: Two-point displacement (base point → destination).
- **Status Bar Prompts**: Real-time guidance during interaction modes.

### 3. Snapping System
- **Grid Snap** (F4): Snap to structural grid intersections (yellow indicator).
- **Endpoint Snap** (F5): Snap to element start/end points (cyan indicator).
- **Midpoint Snap**: Snap to element midpoints (magenta indicator).
- **Toggle All Snaps** (F3): Master snap toggle.
- **In-viewport toggles**: G (grid), E (endpoint).

### 4. Selection System
- **Single click**: Select individual element.
- **Ctrl+click**: Add/remove from multi-selection.
- **Box selection**: Left-to-right = window (enclosed), right-to-left = crossing (intersecting).
- **Batch editing**: Modify profile/material/phase on multiple elements.

### 5. Tekla-Style Numbering
- Identical parts detection (profile, material, geometry tolerance, rotation).
- Series-based numbering with configurable prefix/start/step per element type.
- Preview and renumber-all with undo support.

### 6. Dependency Management
- **Schmekla.bat**: Stepped installation (Core → UI → Geometry → Finalize) with error handling.
- **Virtual Environment**: Python 3.12+ local `venv/`.

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
All model modifications go through command objects with 100-step undo history.

### 4. IFC Export Strategy
Export uses IFC2X3 (Tekla certified):
- Each element type has dedicated IFC mapper
- Profiles map to IfcParameterizedProfileDef where possible
- Materials map to IfcMaterial with properties
- **IMPORTANT**: IfcOpenShell 0.8+ requires `products=[]` parameter (not `product=`)

## Claude Integration Architecture

Schmekla integrates with Claude Code CLI in two ways:

### 1. External Terminal Launcher (Primary - Full Interactive)

The Claude Terminal panel in Schmekla launches Claude CLI in a proper terminal window:

```
┌─────────────────────────────────────────────┐
│  Schmekla Application                        │
│  ┌───────────────────────────────────────┐  │
│  │  Claude Terminal Panel                 │  │
│  │  [Open Claude in Terminal]             │  │
│  │  [Open in Conditions Folder]           │  │
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

### Supported Plan Types

| Plan Type | Detection Capabilities |
|-----------|------------------------|
| Floor Plan | Columns at grid intersections, beam layouts, wall locations |
| Elevation View | Vertical element heights, level positions |
| Grid Layout | Grid line positions and spacings |
| Section View | Cross-section dimensions, internal structure |

### Drawing Management (Tekla-like)

- **Drawing List**: Accessible via `Ctrl+L`. Mimics Tekla Structures.
- **Numbering**: Integrated numbering engine for part marking.
- **Drawing Editor**: Double-click drawing to open. Supports auto-dimensions.

## Complete Keyboard Shortcuts

### File Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New model |
| `Ctrl+O` | Open model |
| `Ctrl+S` | Save model |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+E` | Export IFC |
| `Ctrl+Q` | Exit |

### Edit Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+A` | Select All |
| `Delete` | Delete selected |
| `Ctrl+Shift+C` | Copy mode |
| `Ctrl+Shift+M` | Move mode |
| `Esc` | Cancel / return to IDLE |

### Viewing
| Shortcut | Action |
|----------|--------|
| `F` | Zoom to Fit |
| `1` | Front View |
| `2` | Top View |
| `3` | Right View |
| `0` | Isometric View |

### Creation
| Shortcut | Action |
|----------|--------|
| `B` | Create Beam (two-point) |
| `C` | Create Column (one-point) |
| `P` | Create Plate (four-point) |
| `G` | Create Grid |

### Tools
| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Drawing List |
| `F3` | Toggle All Snaps |
| `F4` | Toggle Grid Snap |
| `F5` | Toggle Endpoint Snap |

### Claude Integration
| Shortcut | Action |
|----------|--------|
| `Ctrl+I` | Import Plan |
| `Ctrl+Space` | Open Claude Prompt |
| `` Ctrl+` `` | Toggle Claude Terminal |

### In-Viewport
| Shortcut | Action |
|----------|--------|
| `M` | Toggle start/end markers |
| `G` | Toggle grid snap |
| `E` | Toggle endpoint snap |

### Mouse Controls
| Action | Effect |
|--------|--------|
| Left click | Select / pick point |
| Left drag | Box selection |
| Ctrl+click | Multi-select toggle |
| Ctrl+Right drag | Rotate viewport |
| Right drag | Zoom |
| Middle drag | Pan |
| Scroll wheel | Zoom |

## Menus Reference

### File Menu
New, Open, Save, Save As, Export IFC, Exit

### Edit Menu
Undo, Redo, Select All, Delete, Copy, Move

### View Menu
Zoom to Fit, Front/Top/Right/Isometric views

### Modeling Menu
Create Beam, Create Column, Create Plate, Create Bolt Group, Create Weld, Create Grid

### Tools Menu
Numbering Settings, Drawing List, Toggle All/Grid/Endpoint Snaps

### Claude Menu
Import Plan, Open Prompt, Toggle Terminal

### Help Menu
About Schmekla

## Common Development Tasks

### Adding a New Element Type

1. Create class in `src/core/new_element.py`:
```python
from src.core.element import StructuralElement, ElementType

class NewElement(StructuralElement):
    def __init__(self, ...):
        super().__init__()
        self.element_type = ElementType.NEW_ELEMENT

    def generate_solid(self):
        # Return OCC solid geometry
        pass

    def to_ifc(self, ifc_model):
        # Return IFC entity
        pass
```

2. Add `NEW_ELEMENT` to `ElementType` enum in `src/core/element.py`
3. Create IFC mapper in `src/ifc/ifc_new_element.py`
4. Add dialog in `src/ui/dialogs/new_element_dialog.py`
5. Register in element factory
6. Add tests in `tests/unit/test_new_element.py`

### Running Tests

```bash
pytest
pytest tests/unit/test_geometry.py
pytest --cov=src
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
- [ ] Use `products=[]` parameter (IfcOpenShell 0.8+ API)

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
- Always log errors before raising
- Provide meaningful error messages
- Use try/except with graceful fallbacks for OCP operations

## Dependencies Quick Reference

```python
# Core
import ifcopenshell           # IFC creation
from OCP.gp import gp_Pnt    # OpenCascade geometry (via cadquery-ocp)
import cadquery as cq         # High-level CAD

# UI
from PySide6.QtWidgets import ...
from PySide6.QtCore import ...
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
- Read `knowledge/LEARNED.md` for VTK interaction patterns

### IFC Export Issues
- Use IFC viewer (BIM Vision, FZK Viewer) to inspect output
- Check `ifcopenshell.validate` for schema compliance
- Log all IFC entity creations
- Use `products=[]` not `product=` (IfcOpenShell 0.8+ breaking change)

### OCP/Geometry Issues
- Import from `OCP.*` not `OCC.Core.*`
- Static methods use `_s` suffix (e.g., `BRepBndLib.Add_s()`)
- If OCP unavailable, elements fall back to simple box geometry

### Claude Integration Issues
- Test CLI bridge independently first
- Log full prompts and responses
- Validate JSON responses before parsing

## Known Issues

1. **OCC fallback rendering**: When CadQuery/OCP solid generation fails, elements render as simplified boxes/tubes instead of accurate profile shapes. The element is still created correctly in the model.
2. **Grid bounding box**: Grid lines extend based on model element positions. Empty models use a default 10m extent.
3. **Float-cast warning**: PyVista emits a harmless `Points is not a float type` warning on startup.

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
5. Document discoveries in `knowledge/LEARNED.md`
