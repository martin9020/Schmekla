# Schmekla Capability Matrix

Legend:

- `Observed in code`: code exists and appears wired into the app, but production validation is still required.
- `Partial`: some code exists, but test/validation or workflow completeness is unclear.
- `Missing`: no meaningful current support observed.
- `Gate`: required before production confidence.

| Capability | Current Status | Evidence | Production Gate |
| --- | --- | --- | --- |
| Geometry primitives | Observed in code | `src/geometry/*`, `tests/unit/test_geometry.py` | Expand edge-case tests for transforms, tolerances, plane/line intersections |
| Structural model document | Partial | `src/core/model.py` | Round-trip save/load tests for every element type and metadata |
| Beams and columns | Observed in code | `src/core/beam.py`, `src/core/column.py` | Unit tests for offsets, local coordinates, copying, numbering signatures, IFC output |
| Plates, slabs, walls, footings | Partial | `src/core/plate.py`, `src/core/slab.py`, `src/core/wall.py`, `src/core/footing.py` | Geometry, persistence, property editing, and IFC tests |
| Curved beams | Partial | `src/core/curved_beam.py` | Rendering/export tests and documented limitations |
| Profiles and materials | Partial | `resources/profiles/uk_sections.json`, `resources/materials/materials.json` | Catalog validation, source notes, loading tests |
| Grids and levels | Partial | `src/core/grid.py`, `src/core/level.py` | Persistence, viewport, IFC spatial assignment tests |
| Snapping and selection | Partial | `src/core/snap_manager.py`, `src/ui/interaction.py`, `src/ui/viewport.py` | UI/interaction tests or scripted manual checks |
| Numbering | Partial | `src/core/numbering.py`, `src/core/commands/numbering_commands.py` | Tests for identical part grouping, series rules, undo/redo |
| Bolt groups and welds | Partial | `src/core/bolt.py`, `src/core/weld.py` | Decide IFC/export semantics; add model and UI tests |
| Drawings | Partial | `src/core/drawing*.py`, `src/drawing/view_generator.py`, `tests/test_drawing_editor.py` | Drawing generation regression tests and manual UI workflow |
| Reports/lists | Missing | No dedicated report module observed | Define report objects and export targets before implementation |
| IFC export | Partial | `src/ifc/exporter.py`, `src/ifc/ifc_*.py` | Automated IFC schema validation plus external viewer/Tekla import checklist |
| Save/load project files | Partial | `StructuralModel.save/load` | Serialization contract, versioning, migrations, full round-trip tests |
| AI plan import | Partial | `src/claude_integration/*`, `src/ai/*` | Security review, deterministic test fixtures, human approval workflow |
| Deployment | Partial | `Schmekla.bat`, `deploy/install.bat`, `requirements.txt` | Clean-machine install test, supported Python version decision, and pinned launcher path |
| Documentation | Partial | README, `CLAUDE.md`, architecture docs | Public mission, license alignment, user guide, validation evidence |
| Security/privacy | Missing | No security policy observed | Review AI file access, local data handling, dependency scan |

## Product Capability Targets

The target is comprehensive functional parity with Tekla-style structural modeling and detailing workflows, delivered as original open-source implementation. Each capability below should be tracked until Schmekla has an equivalent professional workflow, test coverage, validation evidence, and documented limitations.

### Modeling

Target: accurate enough authoring for common steel framing and mixed structural layout. Prioritize grid/level frame modeling, linear members, plates, foundation pads, and property editing before advanced connection detailing.

### Detailing

Target: part identity, assemblies, numbering, basic drawings, and reports. Avoid claiming fabrication-grade detailing until drawings, dimensions, assembly hierarchy, and report generation are tested.

### Interoperability

Target: IFC-first export with stable object mapping. Keep schema choice explicit per export and document known viewer/Tekla behavior from clean validation runs.

### Automation

Target: AI-assisted commands that produce reviewable model changes. The AI path should not bypass validation, user confirmation, or deterministic model commands.
