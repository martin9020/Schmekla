# Phase 0: AI Model Research

> **Status:** In Progress
> **Started:** 2026-01-25
> **Last Updated:** 2026-01-25

---

## Objective

Find the MOST PROBABLE AI model combination for:
- Ground extraction (terrain mesh)
- Wall detection (flat rectangles)
- Fence detection (separate from walls)
- Window detection (gaps in walls)
- Roof detection (close gaps)
- Vegetation detection

---

## E57 File Handling

### Recommended: pye57
- Python wrapper for LibE57Format
- Returns NumPy arrays
- Reads XYZ, RGB, intensity
- GitHub: https://github.com/davidcaron/pye57

### Alternative: PDAL
- Supports E57 via readers.e57
- Good for format conversion
- Has Python bindings
- Docs: https://pdal.io/en/stable/stages/readers.e57.html

---

## Ground Extraction Candidates

| Model | Type | Designed For | Confidence | Source |
|-------|------|--------------|------------|--------|
| **CSF (Cloth Simulation Filter)** | Algorithm | Ground/terrain extraction from LiDAR | HIGH | PDAL, CloudCompare |
| **GroundGrid** | Algorithm | LiDAR ground segmentation, 94.78% IoU | HIGH | https://github.com/dcmlr/groundgrid |
| **GndNet** | Deep Learning | Real-time ground estimation, 55Hz | MEDIUM | https://github.com/anshulpaigwar/GndNet |

### Recommendation: CSF (Cloth Simulation Filter)
- Specifically designed for ground extraction
- Works by simulating cloth dropping on inverted point cloud
- Integrated in PDAL (`filters.csf`) and CloudCompare
- Well-documented, proven algorithm
- Paper: Zhang et al., 2016 "Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation"

---

## Wall/Building Detection Candidates

| Model | Type | Designed For | Confidence | Source |
|-------|------|--------------|------------|--------|
| **RandLA-Net** | Deep Learning | Large-scale point clouds, building facades | HIGH | CVPR 2020 |
| **Open3D RANSAC** | Algorithm | Plane fitting, wall extraction | HIGH | Open3D library |
| **PointNet++** | Deep Learning | Hierarchical point cloud learning | MEDIUM | Stanford |

### Recommendation: Open3D RANSAC + RandLA-Net
1. **Open3D RANSAC** for plane detection (walls are planes)
   - `segment_plane()` method
   - Fast, well-documented
   - Can iteratively find multiple planes

2. **RandLA-Net** for semantic classification
   - 200x faster than other methods
   - Proven for building facade segmentation
   - Handles large-scale point clouds (1M+ points)

---

## Fence vs Wall Separation

| Approach | Method | Confidence |
|----------|--------|------------|
| **Height threshold** | After plane detection, separate by Z-height | HIGH |
| **Geometric features** | Thickness, pattern analysis | MEDIUM |
| **RandLA-Net** | If trained on fence class | MEDIUM |

### Recommendation: Two-stage approach
1. Use RANSAC to find all vertical planes
2. Classify planes by height:
   - Height < 2m = FENCE
   - Height > 2m = WALL
3. Optional: Use point density/pattern for slat detection

---

## Window Detection

| Approach | Method | Confidence |
|----------|--------|------------|
| **Gap detection** | Find rectangular holes in wall planes | HIGH |
| **Alpha shapes** | Detect boundary of wall, find internal holes | MEDIUM |

### Recommendation: Gap detection in plane
1. Project wall points onto 2D plane
2. Grid the 2D space
3. Find rectangular empty regions = windows
4. Extract window boundaries

---

## Roof Detection

| Model | Method | Confidence |
|-------|--------|------------|
| **RANSAC multi-plane** | Detect horizontal/sloped planes above building | HIGH |
| **Alpha shapes** | Fill gaps and create closed boundary | MEDIUM |

### Recommendation: RANSAC + hole filling
1. Detect roof planes with RANSAC
2. Use alpha shapes to fill scanner gaps
3. Create closed surface

---

## Export Formats for Tekla (Reference Models)

**Source:** [Tekla 2025 Reference Models Documentation](https://support.tekla.com/doc/tekla-structures/2025/int_reference_models)

| Format | Tekla Support | Best For |
|--------|---------------|----------|
| **.obj** | YES - Reference model | Simple geometry, universal |
| **.ply** | YES - Reference model | Point cloud geometry |
| **.glTF** | YES - Reference model | Modern 3D interchange |
| **.skp** | YES - Reference model | SketchUp (v2021 and earlier) |
| **.fbx** | YES - Reference model | Complex scenes, animations |
| **.dae** | YES - Reference model | COLLADA interchange |
| **.3ds** | YES - Reference model | 3DS Max legacy |
| **.stp/.STEP** | YES - Reference model | CAD interchange |
| IFC | YES - converts to native | NOT recommended (user feedback) |

### Recommendation: Export to OBJ or PLY
- Both supported as reference models in Tekla 2025
- OBJ widely compatible, includes materials
- PLY good for colored mesh geometry
- All formats auto-convert to TrimBIM (.trb) on import

---

## E57 File Stats (Fordley_Area_1.e57)

```
Points: 7,544,526
Size: 52m x 55m x 4m
Data: XYZ + RGB + Intensity
```

---

## Complete Pipeline Tools

### Core Libraries Needed

```
pye57          - Read E57 files
Open3D         - Point cloud processing, RANSAC, visualization
PDAL           - Filters (CSF ground), format conversion
NumPy          - Data handling
RandLA-Net     - Semantic segmentation (optional, for complex scenes)
```

### Installation

```bash
pip install pye57 open3d pdal numpy
```

### Processing Pipeline

```
1. pye57: Load E57 → NumPy arrays
2. Open3D: Convert to Open3D point cloud
3. PDAL CSF: Extract ground (terrain mesh)
4. Open3D RANSAC: Find vertical planes (walls/fences)
5. Height filter: Separate walls from fences
6. Gap detection: Find windows in walls
7. RANSAC: Find roof planes, fill gaps
8. Export: Save as OBJ/PLY for Tekla reference model import
```

---

## Models NOT Recommended (and why)

| Model | Reason |
|-------|--------|
| PointNet (original) | Doesn't capture local structure well |
| Generic deep learning | Needs training data we don't have |
| Commercial solutions | Cost, vendor lock-in |

---

## Next Steps

1. ✅ Research complete for core elements
2. [ ] Test pye57 on user's E57 file
3. [ ] Test CSF ground extraction
4. [ ] Test RANSAC plane fitting
5. [ ] Test height-based fence/wall separation
6. [ ] Test window gap detection
7. [ ] Combine into pipeline

---

## Research Sources

- Open3D Docs: https://www.open3d.org/docs/release/
- PDAL CSF: https://pdal.io/stages/filters.csf.html
- RandLA-Net Paper: https://openaccess.thecvf.com/content_CVPR_2020/papers/Hu_RandLA-Net_Efficient_Semantic_Segmentation_of_Large-Scale_Point_Clouds_CVPR_2020_paper.pdf
- CSF GitHub: https://github.com/jianboqi/CSF
- pye57 GitHub: https://github.com/davidcaron/pye57
- GroundGrid: https://github.com/dcmlr/groundgrid
