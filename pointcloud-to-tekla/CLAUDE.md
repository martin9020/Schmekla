# Point Cloud to Tekla Pipeline - Project Memory

> **Last Updated:** 2026-01-25
> **Current Phase:** Phase 4 - Validation
> **Status:** OBJ/PLY meshes created, ready for Tekla import testing

---

## Quick Status

```
[x] Project understanding complete
[x] Agent architecture defined
[x] Folder structure created
[x] Phase 0: Research - Find AI models ✓ COMPLETE
[x] Phase 0.5: E57 Loading ✓ (7.5M points loaded)
[x] Phase 1: Ground Extraction ✓ (CSF via Open3D)
[x] Phase 2: Wall/Fence Segmentation ✓ (25 walls, 1 fence detected)
[x] Phase 3: Geometry ✓ (Ground mesh, wall rectangles, fence rectangle)
[ ] Phase 4: Validation - Test import in Tekla
[ ] Phase 5: Refinement - Adjust based on Tekla feedback
```

---

## Research Results (Phase 0)

### Winning Combination

| Element | Tool/Model | Confidence |
|---------|-----------|------------|
| **E57 Reading** | pye57 | HIGH |
| **Ground** | CSF (Cloth Simulation Filter) via PDAL | HIGH |
| **Walls** | Open3D RANSAC plane fitting | HIGH |
| **Fences** | RANSAC + height threshold (<2m) | HIGH |
| **Windows** | Gap detection in wall planes | HIGH |
| **Roof** | RANSAC + alpha shapes hole filling | HIGH |
| **Complex scenes** | RandLA-Net (optional) | MEDIUM |

### Core Libraries
```
pip install pye57 open3d pdal numpy
```

---

## Project Goal

Convert `.e57` point cloud files (from Leica Cyclone) into clean, importable Tekla Structures files with:
- Flat rectangular walls (no curves - must be readable in drawings)
- Windows as rectangular holes in walls
- Fences (separated from walls)
- Ground as mesh following terrain (curves OK - needed for foundations)
- Closed roof (fill gaps)
- Stairs, railings, downpipes

---

## Elements to Extract

| Element | Geometry Rule | Notes |
|---------|---------------|-------|
| GROUND | Mesh with CURVES | Follow terrain for foundations |
| WALLS | FLAT RECTANGLES | No curves, cover furthest points |
| WINDOWS | Rectangular HOLES | Gaps in walls |
| FENCES | FLAT RECTANGLES | Shorter than walls, separate them |
| ROOF | FLAT, closed | Fill scanner gaps |
| STAIRS | Rectangles | Metal structure |
| RAILINGS | Lines/tubes | Diagonal supports |
| DOWNPIPES | Cylinders/rectangles | Building exterior |
| CANTILEVERS | Separate geometry | Parts sticking out |

---

## Scanner Artifacts

| Artifact | Action |
|----------|--------|
| Registration spheres (Leica) | REMOVE (separate objects) |
| Sky noise / green lines | REMOVE (outliers) |
| Shadows | KEEP POINTS (just dark color, real geometry) |
| Scanner streaks | KEEP POINTS (smooth in geometry phase) |

**IMPORTANT:** Shadows are COLOR only, not separate points. Never remove points because they're dark - you lose real geometry.

---

## Agent Architecture

```
RESEARCHER AGENT (Outside workflow - always watching)
        ▲
        │ Receives all results
        │
════════╪══════════════════════════════════════════
        │         MAIN WORKFLOW
════════╪══════════════════════════════════════════
        │
   YOU (Boss) ──▶ ARCHITECT (Coordinator)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   MODEL HUNTER    CLEANER        SEGMENTOR
   (Phase 0)       (Phase 1)      (Phase 2)
        │               │               │
        ▼               ▼               ▼
   GEOMETRIST      VALIDATOR       EXPORTER
   (Phase 3)       (Phase 4)      (Phase 5)
```

---

## Research Approach

NOT brute force testing. Smart research:
1. Find all available AI models
2. Read documentation, papers, benchmarks
3. Match model strengths to element types
4. Narrow to TOP 2-3 candidates per element
5. Test ONLY those (~10-15 tests total)
6. Select winning combination

---

## Key Decisions Made

1. **Walls must be flat rectangles** - Curves are unreadable in Tekla drawings
2. **Ground must follow terrain** - Curves needed for foundation design
3. **Fence vs Wall** - Must segment FIRST, then process separately
4. **Shadows** - Keep all points, ignore color for geometry
5. **Research approach** - Find most probable solutions, not test everything

---

## Folder Structure

```
pointcloud-to-tekla/
├── CLAUDE.md          ← This file (project memory)
├── README.md          ← Overview
├── progress/          ← Phase-by-phase findings
├── agents/            ← Agent definitions
├── data/input/        ← Your .e57 files
├── data/output/       ← Final Tekla files
├── tests/samples/     ← Test point clouds
├── models/selected/   ← Chosen AI models info
└── scripts/           ← Processing scripts
```

---

## Current Session Log

### 2026-01-25 - Session 1
- Discussed project requirements
- Defined agent architecture
- Created folder structure
- Starting Phase 0 research

---

## Next Actions

1. Create agent definition files
2. Start MODEL HUNTER research
3. Find AI models for point cloud segmentation
4. Document findings in progress/phase-0-research.md
