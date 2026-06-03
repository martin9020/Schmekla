# First Deployable Vertical Slice Architecture Plan

Date: 2026-06-03
Issue: SUP-3
Branch: sup-3-architecture

## Goal

Deliver the smallest production-grade Schmekla workflow that creates a simple structural model, preserves it through save/reload, exports a valid IFC file, and gives reviewers a repeatable verification path before broader UI, AI, and detailing work resumes.

## Recommended Approach

Use a model-first vertical slice with thin UI integration. The implementation should stabilize core data contracts, persistence, and IFC export before adding more interactive features.

Considered approaches:

1. Model-first slice, then wire to UI.
   - Best fit because the current tests are mostly non-UI and the release risk is data correctness.
   - Allows fast automated coverage for creation, round-trip persistence, and IFC export.

2. UI-first slice through the existing desktop workflow.
   - Gives a more visible demo sooner.
   - Higher risk because PySide6/PyVista interactions are harder to test and debug before persistence/export contracts are stable.

3. IFC-first export hardening only.
   - Reduces Tekla risk quickly.
   - Not enough for a deployable workflow because model identity and save/reload remain unproven.

Decision: implement option 1, with a minimal UI smoke path only after the core slice is passing.

## Slice Definition

The first deployable slice includes:

- Create a named model with project metadata and millimeter units.
- Add a rectangular grid and at least two levels.
- Add columns, beams, and one plate with required identity, name, profile/material, geometry, part number, and level/spatial assignment metadata.
- Save the model to a deterministic project file.
- Reload the model without changing UUIDs, names, profiles, materials, coordinates, rotations, offsets, levels, grids, or part numbers.
- Export IFC2X3 with project/site/building/storey structure, millimeter units, object names, materials, profiles where supported, and spatial containment.
- Validate the IFC file with automated checks and a manual external viewer/Tekla checklist where available.

## Non-Goals

- AI plan import and Claude command execution.
- Complex connections, weld/bolt IFC export, reinforcement, cuts, copes, openings, curved beams, slabs, walls, and footings.
- Full GUI workflow coverage beyond one smoke path.
- Multi-user collaboration, cloud sync, installer packaging, and licensing.
- Broad refactors of PyVista interaction or selection behavior.
- Replacing CadQuery, IfcOpenShell, PySide6, or the current element class hierarchy.

## Architecture

The slice should introduce explicit data contracts around the existing element model instead of serializing arbitrary object state. A new persistence module should own schema versioning, JSON conversion, validation, and migration hooks. Existing element classes should expose focused `to_data()` and `from_data()` helpers or equivalent adapter functions so persistence does not need to inspect private attributes throughout the codebase.

IFC export should remain behind `IFCExporter`, but the slice needs a validation/reporting layer that returns structured export results instead of relying only on logs. Export should fail loudly for unsupported required slice data and skip only explicitly deferred element types.

The UI should consume the same model APIs used by tests. If a UI command cannot be tested without a display, it should be treated as a smoke check, not the primary acceptance signal.

## Files

Create:

- `src/core/persistence.py`
  - Own JSON schema version, model serialization, deserialization, and validation errors.
- `src/core/slice_builder.py`
  - Build the canonical first-slice model used by tests, examples, and manual verification.
- `src/ifc/validation.py`
  - Inspect exported IFC files for required project structure, units, entity counts, names, materials, and containment.
- `tests/unit/test_persistence.py`
  - Unit tests for model round-trip behavior and validation errors.
- `tests/unit/test_slice_builder.py`
  - Unit tests for the canonical slice model contents.
- `tests/integration/test_vertical_slice.py`
  - End-to-end model creation, save, reload, IFC export, and validation.
- `docs/company/vertical-slice-verification.md`
  - Manual verification checklist for IFC viewer/Tekla and release signoff.

Modify:

- `src/core/model.py`
  - Add public `save(path)` and `load(path)` methods that delegate to `src.core.persistence`.
  - Add explicit model metadata fields required by export and persistence if missing.
- `src/core/element.py`
  - Add a stable element data contract or adapter support for UUID, type, name, material, profile, part number, phase, and common properties.
- `src/core/beam.py`
  - Ensure start/end points, rotation, endpoint offsets, profile, material, name, and part number round-trip.
- `src/core/column.py`
  - Ensure start/end points, rotation, endpoint offsets, profile, material, name, and part number round-trip.
- `src/core/plate.py`
  - Ensure four points, thickness, holes if retained, material, name, and part number round-trip.
- `src/core/grid.py`
  - Ensure grid names, axes, spacings, and origin round-trip.
- `src/core/level.py`
  - Ensure level name and elevation round-trip and drive IFC storeys.
- `src/core/profile.py`
  - Provide a safe profile lookup/serialization path by profile name and type.
- `src/core/material.py`
  - Provide a safe material lookup/serialization path by material name and grade.
- `src/ifc/exporter.py`
  - Return an export result containing file path, schema, exported/skipped counts, warnings, and errors.
  - Treat unsupported required slice elements as errors.
- `src/ifc/ifc_beam.py`
  - Verify exported beam name, profile/material assignment, placement, and representation are populated.
- `src/ifc/ifc_column.py`
  - Verify exported column name, profile/material assignment, placement, and representation are populated.
- `src/ifc/ifc_plate.py`
  - Verify exported plate name, material assignment, placement, and representation are populated.
- `README.md`
  - Add a short "First vertical slice verification" section after implementation.
- `pyproject.toml`
  - Add integration test markers if needed and settle the Python version target with Release Engineer.

## Test Targets

Core commands:

```powershell
python -m pytest tests/unit/test_slice_builder.py -v
python -m pytest tests/unit/test_persistence.py -v
python -m pytest tests/integration/test_vertical_slice.py -v
python -m pytest
```

Environment/release commands:

```powershell
py -3.12 -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m pytest
venv\Scripts\python -m pip check
```

Manual validation:

- Open exported IFC in an external IFC viewer.
- If Tekla is available, import the IFC as a reference model and attempt object conversion.
- Record whether columns, beams, and plate preserve names, materials, profiles where supported, and storey placement.

## Phase Gates

### Gate 0: Environment Baseline

Owner: Release Engineer.

Exit criteria:

- Python target is explicit, preferably 3.12 for the first release baseline.
- Clean project-local virtualenv installs requirements.
- `python -m pip check` has no Schmekla-blocking conflicts inside the project virtualenv.
- Existing test suite passes before code changes.

### Gate 1: Canonical Slice Model

Owner: Lead Engineer.

Exit criteria:

- `src/core/slice_builder.py` creates the canonical model without UI.
- Unit tests assert counts, names, profiles, materials, coordinates, grids, levels, and part numbers.
- No IFC or persistence code is required for this gate.

### Gate 2: Persistence Round Trip

Owner: Lead Engineer.

Exit criteria:

- Save file has a schema version and deterministic JSON structure.
- Reload preserves identity and required properties.
- Invalid files produce actionable validation errors.
- Round-trip tests pass from a clean temp directory.

### Gate 3: IFC Export and Validation

Owner: Lead Engineer with Release Engineer review.

Exit criteria:

- IFC export writes IFC2X3 successfully from the reloaded model.
- Automated validation confirms project/site/building/storey, millimeter units, expected entity counts, object names, materials, and containment.
- Export result reports skipped deferred types separately from errors.

### Gate 4: User-Facing Smoke Path

Owner: Lead Engineer.

Exit criteria:

- Existing app entry point can create or load the canonical slice through a documented route.
- Manual smoke steps are documented without requiring AI import.
- No crash on startup, save, reload, or export on the target environment.

### Gate 5: Review and Release Signoff

Owners: Code Reviewer and Release Engineer.

Exit criteria:

- Code Reviewer approves implementation diff and test design.
- Release Engineer confirms environment setup, release checklist, and manual IFC/Tekla checklist outcome.
- Known limitations are documented in `docs/company/vertical-slice-verification.md`.

## Implementation Order

1. Stabilize the release Python environment and baseline tests.
2. Add the canonical slice builder and unit tests.
3. Add persistence schema and round-trip tests.
4. Add IFC validation helpers and integration tests.
5. Harden IFC exporter behavior for slice-required element types.
6. Add manual verification documentation.
7. Run full automated and manual gates.
8. Submit Code Reviewer and Release Engineer signoff tasks.

## Risks

- Current dependency setup is not isolated; global Python conflicts were observed in SUP-2.
- `IMPLEMENTATION_PLAN.md` contains stale and corrupted content, so it should not be used as the source of truth for this slice.
- Existing tests do not cover persistence or IFC export.
- IFC export logs failures and continues today; production slice needs structured errors for required elements.
- Tekla availability may be limited, so the release checklist must distinguish automated IFC validation from Tekla-specific manual confirmation.

## Review Gates

Code Reviewer should review:

- Persistence schema boundaries and round-trip tests.
- Whether the architecture avoids broad unrelated UI or AI refactors.
- Whether exact files and test targets are sufficient for a TDD implementation plan.

Release Engineer should review:

- Python version target.
- Virtualenv/install commands.
- IFC viewer/Tekla manual checklist.
- Release gate wording and artifact expectations.
