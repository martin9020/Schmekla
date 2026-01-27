# Schmekla - Learned Knowledge Base

This file accumulates lessons learned across all projects. Claude reads this at session start.

---

## IFC Export (IfcOpenShell 0.8+)

### API Changes (discovered 2026-01-25)
- `product=` parameter changed to `products=[]` (list required)
- `application_version=` changed to `version=`
- Must call `owner.create_owner_history` BEFORE creating any entities
- Affected functions:
  - `aggregate.assign_object` -> use `products=[entity]`
  - `spatial.assign_container` -> use `products=[entity]`
  - `material.assign_material` -> use `products=[entity]`

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
  z = z_eaves + 4 * rise * t * (1 - t)  # t goes 0->1
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
+-- {job_number}_{client}/
    +-- PROJECT_CONTEXT.md    # Auto-generated summary
    +-- model.schmekla        # Schmekla native format
    +-- conditions/           # Original client files
    +-- exports/              # IFC and other outputs
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

## Alt+Drag Box Selection (discovered 2026-01-27)

### VTK Event Observers for Selection
- Use `interactor.AddObserver()` for key and mouse events
- Key events: "KeyPressEvent", "KeyReleaseEvent" for Alt detection
- Mouse events: "LeftButtonPressEvent", "LeftButtonReleaseEvent", "MouseMoveEvent"

### Implementation Pattern
```python
def _install_selection_interactor(self):
    interactor = self.plotter.iren.interactor
    interactor.AddObserver("KeyPressEvent", self._on_key_press)
    interactor.AddObserver("KeyReleaseEvent", self._on_key_release)
    interactor.AddObserver("LeftButtonPressEvent", self._on_left_button_press)
    interactor.AddObserver("LeftButtonReleaseEvent", self._on_left_button_release)
    interactor.AddObserver("MouseMoveEvent", self._on_mouse_move)

def _on_key_press(self, obj, event):
    key = obj.GetKeySym()
    if key in ("Alt_L", "Alt_R", "Alt"):
        self._alt_pressed = True
```

### Screen-to-World Coordinate Conversion
```python
# Project element center to screen coords
coord = vtkCoordinate()
coord.SetCoordinateSystemToWorld()
coord.SetValue(center[0], center[1], center[2])
screen_pos = coord.GetComputedDisplayValue(renderer)
```

### Box Selection Logic
- Track `_selection_start` (x, y) on LeftButtonPress when Alt held
- On LeftButtonRelease, find all elements whose screen-projected centers fall within rectangle
- Clear selection first, then add all selected elements with `add_to_selection=True`

---

## Tekla-Style Numbering System (discovered 2026-01-27)

### NumberingSeries Dataclass
```python
@dataclass
class NumberingSeries:
    prefix: str           # "B", "C", "PL", etc.
    start_number: int = 1
    current_counter: int = 0

    def get_next(self) -> str:
        self.current_counter += 1
        return f"{self.prefix}{self.start_number + self.current_counter - 1}"
```

### Position Numbering for Start/End Points
- Tekla assigns unique position numbers to geometric positions
- Elements sharing the same position get the same number
- Use tolerance-based point matching (default 10mm):
```python
def _point_to_key(self, point: Point3D) -> Tuple[float, float, float]:
    tol = self._position_tolerance
    return (
        round(point.x / tol) * tol,
        round(point.y / tol) * tol,
        round(point.z / tol) * tol
    )
```

### Series Configuration API
```python
# Configure beam numbering to start at B100
numbering.configure_series(ElementType.BEAM, prefix="B", start_number=100)

# Get all series config for UI display
config = numbering.get_all_series_config()
# Returns: {'beam': {'prefix': 'B', 'start_number': 100, 'current_counter': 5, 'next_number': 'B105'}}
```

### Identical Parts Numbering (discovered 2026-01-27)

Tekla-style identical parts detection: parts with matching signatures get the same number.
For example, 5 identical beams all get "B1".

#### ComparisonConfig Dataclass
```python
@dataclass
class ComparisonConfig:
    compare_profile: bool = True      # Compare section profile
    compare_material: bool = True     # Compare material
    compare_name: bool = False        # Compare element name
    compare_geometry: bool = True     # Compare geometry (length/dims)
    compare_rotation: bool = True     # Compare rotation angle
    geometry_tolerance: float = 1.0   # Tolerance in mm
```

#### PartSignature (Frozen Dataclass)
```python
@dataclass(frozen=True)
class PartSignature:
    """Immutable signature usable as dict key."""
    element_type: str
    profile_name: str = ""
    material_name: str = ""
    element_name: str = ""
    geometry_key: str = ""    # e.g., "L:6000" for 6m beam
    rotation_key: str = ""    # e.g., "R:45"
```

#### Element Signature Methods
Each element class implements geometry-specific signature calculation:
```python
# In StructuralElement (base class)
def calculate_signature(self, tolerance: float = 1.0) -> str:
    return self._calculate_geometry_key(tolerance)

def _calculate_geometry_key(self, tolerance: float) -> str:
    return ""  # Override in subclasses

def _get_rotation_key(self) -> str:
    return ""  # Override in subclasses

# In Beam
def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
    rounded_length = round(self.length / tolerance) * tolerance
    return f"L:{rounded_length:.0f}"

# In Column
def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
    rounded_height = round(self.height / tolerance) * tolerance
    return f"H:{rounded_height:.0f}"

# In Plate (dimensions sorted so orientation doesn't matter)
def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
    dims = sorted([rounded_width, rounded_length])
    return f"D:{dims[0]:.0f}x{dims[1]:.0f}x{rounded_thickness:.0f}"
```

#### Usage Pattern
```python
# Configure comparison (model.numbering or NumberingManager instance)
config = ComparisonConfig(
    compare_profile=True,
    compare_material=True,
    compare_geometry=True,
    geometry_tolerance=1.0
)
numbering.set_comparison_config(config)

# Get number for element (uses identical parts detection)
part_number = numbering.get_number_for_element(element)

# Preview renumbering without applying
preview = numbering.preview_renumber(elements)
# Returns: {"elem_id_1": "B1", "elem_id_2": "B1", "elem_id_3": "B2", ...}
```

#### Integration with Model
`model.add_element()` automatically uses `get_number_for_element()` which applies
identical parts detection based on the current ComparisonConfig.

---

## Grid Snapping Integration (2026-01-27)

### SnapManager Integration with InteractionManager
- `InteractionManager` holds reference to `SnapManager`
- `handle_click()` applies snapping before element creation
- Emits `snap_occurred` signal with (point, snap_type) for visual feedback

### Status Bar Snap Feedback
- Show active snaps in prompt: `"Pick start point [Snap: Grid, Endpoint]"`
- Show snap result after click: `"Beam created [Snapped to grid]. Pick start point"`

### Snap Toggle Methods
```python
def toggle_grid_snap(self) -> bool:
    if self.snap_manager:
        self.snap_manager.toggle_grid_snap()
        return self.snap_manager.grid_snap
    return False
```

---

## PyVista/VTK Viewport Interaction Overhaul (discovered 2026-01-27)

### CRITICAL: VTK Interactor Style Overrides Don't Work with PyVista

**Problem:** Custom `vtkInteractorStyleTrackballCamera` subclasses don't prevent default behavior because PyVista's Qt layer bypasses them.

**Root Cause:** In `pyvistaqt/rwi.py`, `QVTKRenderWindowInteractor.mouseMoveEvent()` unconditionally calls `self._Iren.MouseMoveEvent()` for EVERY mouse movement, regardless of what your custom interactor style does.

**Event Flow:**
```
Qt Widget receives mouse event
    → QVTKRenderWindowInteractor.mouseMoveEvent()  # PyVista's Qt layer
        → self._Iren.MouseMoveEvent()              # ALWAYS called
            → vtkInteractorStyle.OnMouseMove()     # Your override runs here
                → But parent class methods already processed rotation!
```

### Solution: Qt-Level Event Interception

Create a custom `QtInteractor` subclass that overrides Qt event methods:

```python
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt

class SelectionQtInteractor(QtInteractor):
    def __init__(self, viewport, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewport = viewport
        self._left_button_down = False
        self._drag_start = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle selection - DON'T call super()
            self._left_button_down = True
            self._drag_start = (event.position().x(), event.position().y())
            return  # VTK never sees this event!
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._left_button_down:
            # Draw selection box - DON'T call super()
            self._draw_selection_rect(event.position())
            return  # VTK never sees this event!
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Finish selection - DON'T call super()
            self._finish_selection(event.position())
            self._left_button_down = False
            return
        super().mouseReleaseEvent(event)
```

### Coordinate System Transformation (Qt ↔ VTK)

**Critical:** Qt and VTK use opposite Y-axis conventions!
- **Qt:** Y=0 at TOP of widget
- **VTK:** Y=0 at BOTTOM of widget

**Transformation:**
```python
widget_height = self.plotter.interactor.height()
vtk_y = widget_height - qt_y
```

**Apply in:**
- `finish_selection_box()` - When comparing selection box to element positions
- `_draw_selection_rect()` - When converting Qt coords to VTK display coords

### Faking Button Events for Rotation

To use Ctrl+Right or Ctrl+Middle for rotation (since left button is reserved for selection):

```python
def _fake_left_button_for_rotate(self, event, press=True):
    """Translate Ctrl+Right/Middle to VTK's left button for rotation."""
    iren = self._Iren
    x, y = int(event.position().x()), int(event.position().y())
    iren.SetEventInformation(x, self.height() - y - 1)  # Note Y flip!
    if press:
        iren.LeftButtonPressEvent()
    else:
        iren.LeftButtonReleaseEvent()
```

### Final Interaction Model

| Action | Function |
|--------|----------|
| Left click | Select element |
| Left drag | Box selection |
| Ctrl + Left click | Add/remove from selection |
| Right click | Context menu |
| Ctrl + Right drag | Rotate viewport |
| Ctrl + Middle drag | Rotate viewport |
| Middle drag | Pan |
| Scroll wheel | Zoom |

---

## VTK/PyVista Actor Reference Mismatch Bug (discovered 2026-01-27)

### The Problem

When using VTK's `vtkCellPicker` to pick elements in a PyVista viewport, comparing `picked_actor == stored_actor` **ALWAYS FAILS** even when clicking on the correct element.

**Root Cause:**
- PyVista's `add_mesh()` returns a PyVista actor wrapper
- VTK's picker returns the underlying VTK actor
- These are **different object references** even though they represent the same actor
- Direct comparison (`actor == picked_actor` or `actor is picked_actor`) fails
- The fallback distance-based matching then picks the **wrong element**

### The Fix: Compare Mappers Instead

Each mesh has a unique mapper object. Comparing mappers reliably identifies the correct element:

```python
from vtkmodules.vtkRenderingCore import vtkCellPicker

picker = vtkCellPicker()
picker.Pick(screen_x, screen_y, 0, renderer)
picked_actor = picker.GetActor()

if picked_actor is None:
    return  # Clicked empty space

# Get mapper from picked actor
picked_mapper = picked_actor.GetMapper()

# Find matching element by mapper comparison
for elem_id, actor in self._actors.items():
    if picked_mapper is not None and hasattr(actor, 'GetMapper'):
        actor_mapper = actor.GetMapper()
        if actor_mapper is not None and actor_mapper is picked_mapper:
            # FOUND IT - this is the correct element
            selected_element_id = elem_id
            break
```

### Key Points

1. **Use `is` not `==`** for mapper comparison (identity check is sufficient)
2. **Check for None** before comparing (picker may return None on empty space)
3. **Keep bounds-based fallback** as backup for edge cases
4. **Don't remove the picked_actor check** - still needed to detect empty space clicks

---

*Last updated: 2026-01-27*
