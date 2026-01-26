# Schmekla Architecture

This document describes the system architecture and design decisions for Schmekla.

**Last Updated**: 2026-01-26

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Schmekla Application                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Model Tree │  │  Viewport3D │  │   Properties Panel      │  │
│  │  (Left)     │  │  (Center)   │  │   (Right)               │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │ MainWindow  │                                │
│                   └──────┬──────┘                                │
│                          │                                       │
│         ┌────────────────┼────────────────┐                      │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │
│  │ Interaction │  │  Structural │  │   IFC       │              │
│  │ Manager     │  │  Model      │  │   Exporter  │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │  Elements   │                                │
│                   │ Beam/Column │                                │
│                   │ Plate/etc   │                                │
│                   └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Architecture

### 1. UI Layer (`src/ui/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| MainWindow | `main_window.py` | Application shell, menus, toolbars, dock panels |
| Viewport3D | `viewport.py` | PyVista/VTK 3D rendering, picking, camera |
| InteractionManager | `interaction.py` | State machine for creation/selection modes |
| PropertiesPanel | `widgets/properties_panel.py` | Display/edit selected element properties |
| ClaudeTerminal | `widgets/claude_terminal.py` | Launch Claude CLI in external terminal |

### 2. Core Layer (`src/core/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| StructuralModel | `model.py` | Document container, element registry, undo/redo |
| StructuralElement | `element.py` | Base class for all elements |
| Beam | `beam.py` | Linear horizontal member |
| Column | `column.py` | Vertical member |
| Plate | `plate.py` | Planar element |
| Profile | `profile.py` | Section profiles (I, SHS, CHS) |
| Material | `material.py` | Material definitions |

### 3. Geometry Layer (`src/geometry/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| Point3D | `point.py` | 3D point with distance/midpoint operations |
| Vector3D | `vector.py` | 3D vector with normalize/cross/dot |
| Plane | `plane.py` | Plane definition and intersection |

### 4. IFC Layer (`src/ifc/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| IFCExporter | `exporter.py` | Orchestrate IFC file creation |
| ifc_beam | `ifc_beam.py` | Beam → IfcBeam conversion |
| ifc_column | `ifc_column.py` | Column → IfcColumn conversion |

### 5. Claude Integration (`src/claude_integration/`)

| Component | File | Responsibility |
|-----------|------|----------------|
| ClaudeBridge | `claude_bridge.py` | Programmatic Claude CLI access |
| PlanAnalyzer | `plan_analyzer.py` | Vision-based drawing analysis |

---

## Signal Flow

### Element Creation Flow
```
User clicks "Beam" toolbar
    │
    ▼
MainWindow.create_beam()
    │
    ▼
InteractionManager.set_mode(CREATE_BEAM)
    │
    ├─► mode_changed signal ──► Viewport3D.set_interaction_mode()
    │                               └─► enable ground plane picking
    │
    └─► prompt_changed signal ──► MainWindow status bar
                                     "Pick start point..."
    │
User clicks viewport (point 1)
    │
    ▼
Viewport3D._on_viewport_click()
    │
    └─► InteractionManager.add_point(point1)
            └─► prompt_changed: "Pick end point..."
    │
User clicks viewport (point 2)
    │
    ▼
InteractionManager.add_point(point2)
    │
    └─► element_created signal ──► MainWindow._on_element_created_request()
                                       │
                                       ▼
                                   Beam() created
                                       │
                                       ▼
                                   Model.add_element(beam)
                                       │
                                       └─► element_added signal
                                               │
                                               ├─► Viewport3D._on_element_added()
                                               │       └─► add mesh to plotter
                                               │
                                               └─► MainWindow._on_element_added()
                                                       └─► add to model tree
```

### Selection Flow
```
User clicks on element in IDLE mode
    │
    ▼
Viewport3D._on_selection_pick(picked_point)
    │
    ▼
Find closest element by bounds check
    │
    ▼
Model.set_selected([element_id])
    │
    └─► selection_changed signal
            │
            ├─► Viewport3D._on_selection_changed()
            │       └─► Update actor colors (yellow for selected)
            │
            ├─► MainWindow._on_selection_changed()
            │       ├─► Update tree selection
            │       └─► Update PropertiesPanel
            │
            └─► PropertiesPanel.show_element(element)
                    └─► Display properties grouped by category
```

---

## Architecture Decision Records

### ADR-001: PyVista over Raw VTK
**Date**: 2026-01-25
**Status**: Accepted

**Context**: Need 3D rendering in Qt application.
**Decision**: Use PyVista (high-level VTK wrapper) with QtInteractor.
**Consequences**:
- (+) Simpler API for common operations
- (+) Built-in Qt integration
- (-) Some VTK features require dropping to raw VTK

### ADR-002: Bounds-Based Selection
**Date**: 2026-01-26
**Status**: Accepted

**Context**: VTK cell picker doesn't reliably return actor references in PyVista callbacks.
**Decision**: Use bounds-based element identification - check if picked point falls within actor bounds with margin.
**Consequences**:
- (+) Works reliably with simple box geometry
- (-) May have edge cases with complex overlapping geometry
- (-) Requires iterating all actors

### ADR-003: Direct Actor Color Update
**Date**: 2026-01-26
**Status**: Accepted

**Context**: Selection highlighting caused elements to disappear when re-adding meshes (OCC not available).
**Decision**: Update actor color directly via `actor.GetProperty().SetColor()` instead of removing/re-adding mesh.
**Consequences**:
- (+) No mesh regeneration needed
- (+) Works without OCC/CadQuery
- (+) No flicker on selection change

### ADR-004: Signal-Based State Machine
**Date**: 2026-01-26
**Status**: Accepted

**Context**: Need to coordinate UI state across multiple components (toolbar, viewport, status bar).
**Decision**: InteractionManager emits Qt signals for state changes; components subscribe.
**Consequences**:
- (+) Loose coupling between components
- (+) Easy to add new subscribers
- (-) Debugging signal flow can be tricky

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| UI Framework | PySide6 (Qt 6) | 6.x |
| 3D Rendering | PyVista + VTK | Latest |
| Geometry Kernel | CadQuery + OCC | Optional |
| IFC Export | IfcOpenShell | 0.8+ |
| Logging | Loguru | Latest |

---

## File Organization

```
Schmekla/
├── src/
│   ├── main.py              # Entry point
│   ├── core/                # Data models
│   ├── geometry/            # Math primitives
│   ├── ui/                  # Qt UI components
│   │   ├── widgets/         # Custom widgets
│   │   └── dialogs/         # Modal dialogs
│   ├── ifc/                 # IFC export
│   └── claude_integration/  # AI features
├── resources/
│   ├── profiles/            # Section databases (JSON)
│   └── materials/           # Material databases (JSON)
├── docs/
│   └── ARCHITECTURE.md      # This file
├── knowledge/
│   └── LEARNED.md           # Technical lessons
├── CLAUDE.md                # Dev guide
├── IMPLEMENTATION_PLAN.md   # Roadmap
└── Phase5_Plan.md           # Current phase
```

---

## Future Considerations

### Planned Components
- **SelectionManager**: Dedicated class for multi-selection, box selection
- **SnapManager**: Grid/point snapping logic
- **CommandManager**: Undo/redo command pattern
- **PluginSystem**: Extensibility for custom components

### Performance Notes
- Current: Handles 200+ elements smoothly
- Viewport uses actor caching (`_actors` dict)
- Mesh regeneration only on element invalidation

---

*Maintained by: schmekla-architect*
