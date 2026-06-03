# Schmekla Mission

## Product Direction

Schmekla is an independent structural modeling and detailing platform for steel and mixed structural workflows. The product should support Tekla-compatible workflows where lawful and practical, but it must not copy Tekla proprietary code, user interface assets, protected documentation, licensed datasets, or trademarks beyond nominative compatibility references.

The long-term product goal is comprehensive functional parity with Tekla-style structural modeling and detailing workflows: if an engineer depends on a capability such as modeling, profiles, assemblies, numbering, drawings, reports, connection detailing, shortcuts, filters, exports, or project setup, Schmekla should eventually provide an equivalent open implementation. Functional parity means matching the job-to-be-done and professional workflow outcomes, not cloning proprietary implementation, protected assets, or private internals.

The practical target is an open structural authoring workflow:

- Model beams, columns, plates, slabs, walls, footings, grids, levels, bolt groups, weld references, and future connection components.
- Maintain clear object identity, material/profile data, numbering, drawing references, reports, and user-facing editing workflows.
- Export and validate models through open formats, primarily IFC, rather than proprietary Tekla internals.
- Treat Tekla import/conversion as a compatibility test target, not as a source to clone.

## Source Boundaries

Allowed inputs:

- Current Schmekla source code and project files.
- Public standards and public documentation.
- Open-source libraries and their documentation.
- Original design decisions made for Schmekla.
- Manual observations from lawful use of exported Schmekla files in external tools.

Disallowed inputs:

- Proprietary Tekla source code, assets, internal schemas, protected training data, or licensed content.
- Decompiled software, private APIs, or copied UI layouts.
- Unsourced claims about Tekla behavior.

## Public Standards Baseline

IFC is the interoperability foundation. buildingSMART describes Industry Foundation Classes as an open, vendor-neutral BIM standard and maintains the official IFC schema documentation:

- https://technical.buildingsmart.org/standards/ifc/
- https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/

Tekla compatibility must be proven through public import/export and reference-model conversion workflows documented by Trimble, plus our own clean test artifacts:

- https://support.tekla.com/doc/tekla-structures/2023/int_exporting_into_ifc
- https://support.tekla.com/fi/doc/tekla-structures/2026/rel_int_enhanced_ifc_interoperability

## Brainstorming Outcome

I considered three kickoff approaches:

1. Product-first roadmap: define the full product capability map before touching implementation. This gives strategic clarity but can delay verification.
2. Repo-first hardening: focus only on current code, tests, and packaging. This reduces immediate risk but can miss the larger structural-detailing target.
3. Vertical-slice strategy: document the mission and product map, then drive the first deployable slice through model creation, persistence, IFC export, and validation gates.

Recommended approach: vertical-slice strategy. It gives the company a clear long-term product direction while forcing the next engineering work to prove a small, testable workflow end to end.

## First Deployable Slice

The first production slice should prove:

1. Create a simple structural frame with grid, levels, columns, beams, plates, and representative metadata.
2. Save and reload the model without losing object identity or key properties.
3. Export IFC with stable units, spatial structure, materials, profiles, and object names.
4. Validate the IFC with automated checks where possible.
5. Manually verify import/reference-model behavior in at least one external IFC viewer and, when available, Tekla Structures.

This slice is intentionally narrow. Connections, fabrication drawings, advanced reports, reinforcement, and AI plan import remain important but should not block the first deployable proof.
