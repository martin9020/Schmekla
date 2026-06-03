# Schmekla Company Onboarding

## Repository Snapshot

Schmekla is a Python desktop structural modeling application. The main stack is:

- Python support target is not yet a production baseline. Project metadata allows Python 3.11+, README launcher examples still target Python 3.12+, and [SUP-2](/SUP/issues/SUP-2) must establish the supported version and launcher path.
- PySide6 for the desktop UI.
- PyVista and VTK for the 3D viewport.
- CadQuery / OCP for solid geometry where available.
- IfcOpenShell for IFC export.
- pytest for tests. In the current shell, `pytest` currently runs under Python 3.13.11 with 30 passing tests, and `pytest --cov=src` currently runs under Python 3.13.11 with 30 passing tests.
- Claude Code CLI integration for user-assisted modeling and plan import.

The current repository already contains working application code rather than a greenfield scaffold.

## Main Modules

- `src/core/`: model document, structural element classes, profiles, materials, numbering, grids, levels, drawings, snaps, bolt and weld reference elements.
- `src/geometry/`: point, vector, line, plane, and transform primitives.
- `src/ifc/`: exporter and per-element IFC mappers.
- `src/ui/`: PySide6 main window, dialogs, viewport interaction, dock widgets, drawing windows, and properties panel.
- `src/drawing/`: drawing view generation.
- `src/claude_integration/`: Claude CLI bridge and plan analyzer.
- `src/ai/`: document processing, DWG processing, embeddings, RAG, and vector store modules.
- `resources/`: profiles and material catalogs.
- `tests/`: geometry and drawing tests, currently limited relative to product scope.

## Current Strengths

- The product already has recognizable structural modeling surfaces: beams, columns, plates, slabs, walls, footings, curved beams, grids, levels, snaps, selection, numbering, drawings, and IFC export.
- The code follows a layered structure that is understandable: core model, geometry primitives, UI, IFC, and AI helpers.
- `StructuralModel` emits Qt signals for UI updates and keeps undo/redo stacks.
- Element-specific IFC mapping exists for the major modeled object types.
- README and `CLAUDE.md` document user workflows, shortcuts, stack, and known issues.

## Current Gaps

- Test commands are only partly reproducible in the current shell: `pytest` and `pytest --cov=src` run under Python 3.13.11, while `py -m pytest` still launches Python 3.14 without pytest installed.
- The test suite is too small for the claimed surface area. Geometry and drawing smoke tests exist, but model persistence, IFC export validity, UI workflows, numbering, and command behavior need focused tests.
- `IMPLEMENTATION_PLAN.md` appears stale, very long, and partly corrupted with embedded NUL-style characters near appended sections.
- README currently labels the license as proprietary/internal while the mission asks for an independent open-source platform. Legal/product ownership needs a deliberate decision before public release.
- The repository has uncommitted changes in several core/UI files. Future agents must not overwrite them casually.
- Some code paths describe Tekla-style behavior without enough source or validation evidence. These should be reframed as Schmekla-original workflows inspired by public, lawful compatibility goals unless externally verified.

## Verification Baseline

Commands attempted during onboarding:

```powershell
pytest
pytest --cov=src
py -m pytest
```

Results:

- `pytest`: 30 passing tests under Python 3.13.11.
- `pytest --cov=src`: 30 passing tests under Python 3.13.11.
- `py -m pytest`: Python 3.14 launched, but pytest was not installed.

The next engineering task should establish a reproducible supported-version test environment, preferably by using the project launcher or an explicit `.venv` with the pinned requirements. Until [SUP-2](/SUP/issues/SUP-2) completes, README Python version guidance is a target rather than a production support baseline.

## Working Rules For Agents

- Read `CLAUDE.md`, this onboarding file, and relevant source files before changing code.
- Check `git status --short` before edits and preserve user changes.
- Make small changes with tests or a written test gap.
- For Tekla compatibility, cite public docs or validate with clean exported artifacts.
- Do not mark feature work done until implementation, tests, review, and documentation are all accounted for.
