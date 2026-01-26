# Schmekla - Learned Knowledge Base

This file accumulates lessons learned across all projects. Claude reads this at session start.

---

## IFC Export (IfcOpenShell 0.8+)

### API Changes (discovered 2026-01-25)
- `product=` parameter changed to `products=[]` (list required)
- `application_version=` changed to `version=`
- Must call `owner.create_owner_history` BEFORE creating any entities
- Affected functions:
  - `aggregate.assign_object` → use `products=[entity]`
  - `spatial.assign_container` → use `products=[entity]`
  - `material.assign_material` → use `products=[entity]`

### Working Export Pattern
```python
# 1. Create owner history FIRST
ifcopenshell.api.run("owner.add_application", ifc, version="0.1.0", ...)
ifcopenshell.api.run("owner.add_person", ifc, ...)
ifcopenshell.api.run("owner.add_organisation", ifc, ...)
ifcopenshell.api.run("owner.add_person_and_organisation", ifc, ...)
ifcopenshell.api.run("owner.create_owner_history", ifc)

# 2. Then create project structure
project = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcProject", ...)

# 3. Use products=[] for assignments
ifcopenshell.api.run("aggregate.assign_object", ifc,
    relating_object=project, products=[site])
```

---

## Barrel Roof Structures

### Geometry Approximation
- Curved barrel hoops work best with 16 segments for smooth polycarbonate cladding
- Use parabolic curve (not circular arc) for typical canopy profiles:
  ```python
  z = z_eaves + 4 * rise * t * (1 - t)  # t goes 0→1
  ```
- This gives maximum height at t=0.5 (center)

### Typical Dimensions (Oxford XL style)
- Eaves height: ~4865mm
- Ridge height: ~6980mm
- Rise: ~2115mm

---

## Profile Conventions

### SHS Profiles for Canopies
- Columns: SHS 150x150x5 (typical for spans up to 15m)
- Hoops: SHS 60x60x4 (main curved members)
- Purlins: SHS 60x60x3 (standard), SHS 60x60x4 (edge/eaves)
- Bracing: SHS 20x20x2.5 (diagonal members)

### Profile Catalog Notes
- SHS profiles in uk_sections.json use `D` for dimension, not `h` and `b`
- When creating custom profiles programmatically, set both `h` and `b` to the same value

---

## Client-Specific Knowledge

### Clovis Canopies
- Uses Oxford XL product line
- All members typically SHS (square hollow sections)
- Foundation pad sizes from drawings:
  - Corners: 1200x1200mm
  - Intermediate: 1400x1400mm
- Drawing numbering: JOBNO-SEQUENCE-Description

---

## File Organization

### Project Structure
```
projects/
└── {job_number}_{client}/
    ├── PROJECT_CONTEXT.md    # Auto-generated summary
    ├── model.schmekla        # Schmekla native format
    ├── conditions/           # Original client files
    └── exports/              # IFC and other outputs
```

---

## Performance Notes

### Very Small Models
- 168 elements exports in ~1 second
- PyVista viewport handles 200+ elements smoothly
- Batch element creation is faster than individual signals

---

---

## PyVista/VTK Viewport Picking (discovered 2026-01-26)

### Ground Plane Picking
- `enable_point_picking()` only picks on existing meshes, not empty space
- For element creation, use `track_click_position()` + ray-plane intersection
- `pick_click_position()` returns 3D world coords (x, y, z), not screen coords

### Ray-Plane Intersection Pattern
```python
# Get near/far points from screen coords
from vtkmodules.vtkRenderingCore import vtkCoordinate
coord = vtkCoordinate()
coord.SetCoordinateSystemToDisplay()
coord.SetValue(mouse_x, mouse_y, 0)  # near plane
near_world = coord.GetComputedWorldValue(renderer)
coord.SetValue(mouse_x, mouse_y, 1)  # far plane
far_world = coord.GetComputedWorldValue(renderer)

# Intersect with Z=0 plane
ray_dir = far_world - near_world
t = -near_world[2] / ray_dir[2]
intersection = near_world + t * ray_dir
```

### Double-Click Prevention
- PyVista `track_click_position` can fire multiple times per click
- Add 200ms debounce using `time.time()` comparison
```python
if time.time() - self._last_click_time < 0.2:
    return  # Debounce
self._last_click_time = time.time()
```

### Mode Switching Pattern
- Use signal `mode_changed` from InteractionManager
- Viewport listens and calls `track_click_position()` for creation modes
- Call `disable_picking()` when returning to IDLE

### Element Selection (Bounds-Based)
- `enable_point_picking(callback, picker='cell')` for IDLE mode selection
- VTK pickers may not return actor reference directly
- Use bounds-based element identification instead:
```python
for elem_id, actor in self._actors.items():
    bounds = actor.GetBounds()  # (xmin, xmax, ymin, ymax, zmin, zmax)
    margin = 500  # mm tolerance
    in_bounds = (bounds[0] - margin <= x <= bounds[1] + margin and
                 bounds[2] - margin <= y <= bounds[3] + margin and
                 bounds[4] - margin <= z <= bounds[5] + margin)
```

### Selection Highlighting
- **DON'T** remove and re-add mesh on selection (causes flicker, requires OCC)
- **DO** update actor color directly via VTK property:
```python
actor = self._actors[elem_id]
prop = actor.GetProperty()
r, g, b = parse_hex_color(color_hex)  # "#FFFF00" -> (1.0, 1.0, 0.0)
prop.SetColor(r, g, b)
```

---

## Properties Panel Design (2026-01-26)

### Tekla-Style Properties
Group properties into categories:
- **General**: Name, Type, ID
- **Section**: Profile
- **Material**: Material name
- **Geometry**: Length/Height, Start/End points, Rotation
- **Attributes**: Phase, Class

### Implementation
- Use `element.get_properties()` which returns a Dict
- `PropertiesPanel` widget with `QGroupBox` for each category
- Editable fields emit `property_changed` signal
- Call `element.set_property(name, value)` to update

---

*Last updated: 2026-01-26*
