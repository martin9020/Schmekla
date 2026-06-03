# Schmekla Risk Register

| ID | Risk | Severity | Owner | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R-001 | Tekla compatibility claims exceed verified evidence | High | CEO | Require public documentation or clean validation artifact for every claim | Open |
| R-002 | Proprietary/internal license conflicts with open-source mission | High | CEO | Decide license and update README/package metadata before public release | Open |
| R-003 | Python/test baseline still needs a supported-version decision | High | Lead Engineer | Establish `.venv` or documented launcher-based test flow; record supported Python version; preserve current evidence that `pytest` and `pytest --cov=src` pass under Python 3.13.11 while `py -m pytest` selects Python 3.14 without pytest | Open |
| R-004 | Test coverage is too narrow for structural modeling claims | High | Lead Engineer | Add slice-focused tests for persistence, IFC export, numbering, and model commands | Open |
| R-005 | `IMPLEMENTATION_PLAN.md` is stale and partly corrupted | Medium | Lead Engineer | Replace with scoped plans under durable docs after review | Open |
| R-006 | IFC exporter may silently skip failed elements | High | Lead Engineer | Add export result reporting and tests that fail on unexpected skipped elements | Open |
| R-007 | Save/load loses element details for some types | High | Lead Engineer | Define serialization contract and round-trip tests by element type | Open |
| R-008 | UI behavior is hard to regression-test | Medium | Lead Engineer | Add unit-level state tests and limited pytest-qt smoke tests | Open |
| R-009 | AI/Claude integration may access local files or make nondeterministic changes | High | Release Engineer | Add explicit user approval, command preview, logging, and security review | Open |
| R-010 | Dependency stack is heavy and Windows-specific | Medium | Release Engineer | Validate clean install; document supported Python and platform; isolate optional dependencies | Open |
| R-011 | Existing uncommitted changes may be overwritten by agents | Medium | All agents | Always inspect `git status --short`; preserve unrelated edits | Open |
| R-012 | Profile/material catalogs may lack traceable provenance | Medium | CEO | Add source/provenance notes and validation tests before public distribution | Open |
| R-013 | Users may rely on Schmekla output for structural design, detailing, fabrication, or construction before the product is validated or certified | Critical | CEO | Add public disclaimers, require qualified structural engineer review for all generated output, and block release claims until verification gates and liability review pass | Open |

## Immediate Top Risks

1. Reproducible test environment.
2. Structural engineering fitness-for-use and liability controls.
3. Persistence and IFC validation for the first slice.
4. License alignment with the open-source mission.
5. Clean public-source boundary for Tekla-compatible workflows.
