# Schmekla Current-State Assessment

Date: 2026-06-03
Issue: SUP-2
Branch: sup-2-assessment
Worktree: `C:\Users\Martin PC\.config\superpowers\worktrees\Schmekla\sup-2-assessment`

## Summary

The clean repository baseline can run the existing automated test suite after installing the pinned requirements. The current baseline is small and mostly covers geometry primitives plus drawing generation. The main immediate risks are environment reproducibility, a mismatch between documented Python guidance and the active interpreter, missing tracked company onboarding artifacts, and a shared global Python environment with unrelated package conflicts.

No product code was changed for this assessment.

## Repository State

- Base branch checked out for assessment: `main` at commit `75f50bf2`.
- Assessment branch: `sup-2-assessment`.
- Main checkout had pre-existing uncommitted changes and untracked `docs/company/`; those were not modified.
- Clean worktree initially had no tracked `docs/company/` or `docs/superpowers/specs/` files.
- Tracked Python source files under `src/`: 73.
- Tracked Python test files under `tests/`: 5.

## Environment

Observed interpreter:

```powershell
python --version
```

Result:

```text
Python 3.13.11
```

Project metadata:

- `pyproject.toml` declares `requires-python = ">=3.11"`.
- Classifiers list Python 3.11 and 3.12.
- README quick start says Python 3.12 or higher, then uses `py -3.12 -m venv venv`.

Environment risk:

- The clean worktree did not contain an active virtual environment.
- `python -m pip install -r requirements.txt` installed into the global Python 3.13 environment.
- A dedicated project virtualenv should be required for reproducible release and CI work.

## Dependency Setup

Initial test command failed because `pytest` was not installed in the active interpreter:

```powershell
python -m pytest
```

Initial result:

```text
C:\Users\Martin PC\AppData\Local\Programs\Python\Python313\python.exe: No module named pytest
```

After setup:

```powershell
python -m pip install -r requirements.txt
```

Result:

- Install completed.
- It installed or downgraded packages in global Python 3.13 site-packages.
- Pip reported unrelated resolver conflicts already present in the shared environment.

Package consistency check:

```powershell
python -m pip check
```

Result:

```text
mcp-server-fetch 2025.4.7 has requirement httpx<0.28, but you have httpx 0.28.1.
pymupdf4llm 0.3.4 has requirement pymupdf>=1.27.1, but you have pymupdf 1.26.7.
transformer-lens 2.16.1 has requirement beartype<0.15.0,>=0.14.1, but you have beartype 0.22.9.
```

Assessment:

- These conflicts are from packages outside Schmekla's declared requirements.
- The Schmekla install is therefore not isolated enough to be treated as a release baseline.

## Test Baseline

Command:

```powershell
python -m pytest
```

Result after dependency setup:

```text
30 passed, 22 warnings in 12.10s
```

Warnings:

- All observed warnings were third-party `PyparsingDeprecationWarning` warnings from CadQuery and ezdxf dependencies.
- No Schmekla test failures were observed.

Additional sanity checks:

```powershell
python -m compileall -q src tests
python -c "from src.core.model import StructuralModel; from src.core.beam import Beam; from src.geometry.point import Point3D; print('imports ok')"
```

Results:

- `compileall` completed successfully.
- Core imports completed successfully and printed `imports ok`.

## Module Inventory

Primary application layers:

- `src/core/`: structural model, elements, profiles, materials, drawings, numbering, snapping, and command objects.
- `src/geometry/`: point, vector, line, plane, and transform primitives.
- `src/ui/`: PySide6 main window, viewport, interaction state, dialogs, widgets, and drawing windows.
- `src/ifc/`: exporter orchestration and element-to-IFC conversion modules.
- `src/drawing/`: drawing view generation.
- `src/claude_integration/`: Claude CLI bridge and plan analysis.
- `src/ai/`: document processing, DWG processing, embeddings, RAG, and vector store modules.
- `src/utils/`: configuration, logging, and units.

Tests currently cover:

- `tests/unit/test_geometry.py`: geometry primitives and transforms.
- `tests/test_drawing_editor.py`: drawing generation.

Coverage gap:

- No automated coverage was observed for IFC export, persistence/save-load behavior, UI workflows, AI plan import, resource/profile loading, command undo-redo behavior, or release packaging.

## Documentation State

Tracked documentation in the clean branch:

- `README.md`
- `CLAUDE.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENT_WORKFLOW.md`
- `IMPLEMENTATION_PLAN.md`
- `DEVLOG.md`

Paperclip kickoff plan for SUP-1 says these repo artifacts were created:

- `docs/company/mission.md`
- `docs/company/onboarding.md`
- `docs/company/capability-matrix.md`
- `docs/company/phase-plan.md`
- `docs/company/risk-register.md`
- `README.md` planning-doc pointer

Clean branch finding:

- None of those `docs/company/*.md` files were tracked in the clean worktree.
- The main checkout had an untracked `docs/company/` directory before this work started; it was intentionally left untouched.

Documentation quality observations:

- `docs/ARCHITECTURE.md` has a last-updated date of 2026-01-26 and describes some components as future work even though corresponding modules now exist.
- `docs/ARCHITECTURE.md` references `Phase5_Plan.md`, which is not present in the clean branch.
- README and `pyproject.toml` are not perfectly aligned on supported Python versions: README emphasizes 3.12+, metadata permits 3.11+ and was verified here with 3.13.11.

## Immediate Blockers and Risks

1. Release reproducibility is not established.
   - A fresh project-local virtualenv was not created automatically in this assessment.
   - Installing requirements into global Python caused visible conflicts with unrelated tools.

2. Company onboarding artifacts are not tracked in the clean branch.
   - SUP-1 records them as created, but they are absent from Git at commit `75f50bf2`.
   - This blocks reliable handoff unless the intended files are committed or recreated.

3. Test coverage is too narrow for a production vertical slice.
   - The passing baseline is useful, but it does not prove save/load, IFC export, UI interaction, or release packaging.

4. Python version policy needs a single source of truth.
   - The project currently works under Python 3.13.11 for the observed tests.
   - Tooling and docs still point primarily at Python 3.12.

## Recommended Next Steps

1. Create a deterministic environment path for release work:
   - Prefer `py -3.12 -m venv venv`.
   - Run `venv\Scripts\python -m pip install -r requirements.txt`.
   - Run `venv\Scripts\python -m pytest`.

2. Bring company onboarding artifacts into tracked source control or move them into Paperclip issue documents with explicit links.

3. For the first deployable vertical slice, add tests around:
   - model creation and persistence,
   - IFC export smoke path,
   - profile/material resource loading,
   - command undo/redo behavior,
   - at least one UI-independent workflow that exercises the slice end to end.

4. Update `docs/ARCHITECTURE.md` after the vertical-slice plan is approved so it matches the current module layout and removes stale references.
