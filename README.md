# Schmekla

**Structural Modeling Application with AI-Assisted Design**

Schmekla is a custom structural modeling application that creates 3D steel and concrete models, exports to IFC format for Tekla Structures compatibility, and features Claude Code CLI integration for natural language model creation and automatic model generation from plan drawings.

## Features

- **3D Structural Modeling**: Create beams, columns, plates, slabs, walls, footings, bolt groups, welds, and curved beams
- **Interactive Creation**: Two-point beams, one-click columns, four-point plates, two-step weld connections
- **Grids & Levels**: Parametric grid systems with quick-fill and level management
- **Snapping System**: Grid snap (F4), endpoint snap (F5), midpoint snap with visual indicators
- **Selection & Editing**: Single click, Ctrl+multi-select, box selection (window/crossing), batch editing
- **Tekla-Style Numbering**: Identical parts detection, series-based numbering with configurable prefixes
- **Drawings & Reports**: Drawing list (Ctrl+L), drawing editor, automatic dimensioning
- **Properties Panel**: Tekla-style grouped properties with position/offset editing
- **IFC Export**: Export models to IFC2X3/IFC4 format with profile and material mapping
- **AI-Assisted Design**: Natural language prompts to create and modify models via Claude CLI
- **Plan Import**: Upload structural drawings (PNG/JPG/PDF) and auto-generate models using Claude's vision
- **Copy & Move**: Two-point displacement operations on selected elements
- **Undo/Redo**: Full command-pattern undo history (100 steps)
- **UK Steel Sections**: 31 UK structural steel profiles, 7 standard materials

## Quick Start

### Prerequisites

- Python 3.12 or higher (3.11+ compatible)
- Windows 10/11 (primary target)
- Claude Code CLI installed (for AI features)

### Installation

**Option 1: One-Click Launcher (Recommended)**

Double-click `Schmekla.bat` — it creates the virtual environment, installs all 83 dependencies in 4 stages, and launches the application.

**Option 2: Manual Install**

```bash
cd Schmekla
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

### Deploying to Another PC

**IMPORTANT**: The `venv/` folder contains paths specific to your machine and is NOT portable.

1. **Copy these folders/files** (exclude `venv/`):
   ```
   Schmekla/
   ├── src/
   ├── resources/
   ├── deploy/
   ├── Conditions/
   ├── requirements.txt
   ├── pyproject.toml
   ├── Schmekla.bat
   └── ... (other files, but NOT venv/)
   ```

2. **On the target PC**, double-click `Schmekla.bat` or run:
   ```bash
   cd Schmekla
   deploy\install.bat
   ```

3. **For Claude CLI features**, also install:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

## Usage

### Creating Elements

#### Via Keyboard Shortcuts (Interactive)
- `B` - Create Beam (pick start point, then end point)
- `C` - Create Column (pick position, uses default height)
- `P` - Create Plate (pick 4 corner points)
- `G` - Create Grid (opens grid dialog with quick-fill)

#### Via Modeling Menu
- **Create Bolt Group** - Pick origin, auto-creates bolt array
- **Create Weld** - Select main part, then secondary part

#### Via Claude Terminal
Open with `` Ctrl+` `` and type natural language:

```
"Create a beam from 0,0,0 to 6000,0,0 using UB 305x165x40"
"Add a column at 0,0,0 with height 4000 using UC 203x203x46"
"Create a portal frame 12 meters wide and 6 meters high"
"Create a floor slab from 0,0,3500 with width 12000 and length 18000"
"Add a shear wall from 0,0,0 to 6000,0,0 height 3500 thickness 200"
"Create a pad footing at 0,0,0 size 1500x1500 depth 500"
```

### Importing from Plan Drawings

1. Go to **Claude > Import Plan...** (or `Ctrl+I`)
2. Select a plan image (PNG, JPG, PDF, GIF, WebP)
3. Choose the plan type (Floor Plan, Elevation, Grid Layout, Section View, or Auto-detect)
4. Set the drawing scale (1:50, 1:100, 1:200, 1:500)
5. Click **Analyze & Build Model**
6. Claude will detect grid lines, columns, beams, and walls automatically

### Snapping

- `F3` - Toggle all snaps on/off
- `F4` - Toggle grid snap (yellow indicator)
- `F5` - Toggle endpoint snap (cyan indicator)
- In viewport: `G` toggles grid snap, `E` toggles endpoint snap

### Selection & Editing

- **Single click** on element to select
- **Ctrl+click** to add/remove from selection
- **Left drag** for box selection:
  - Left-to-right = window selection (fully enclosed elements only)
  - Right-to-left = crossing selection (any intersecting elements)
- **Batch Edit**: Select multiple elements, then use Edit menu to change profile/material/phase simultaneously

### Copy & Move

- `Ctrl+Shift+C` - Enter copy mode (pick base point, then destination)
- `Ctrl+Shift+M` - Enter move mode (pick base point, then destination)

### Numbering (Tekla-Style)

Access via **Tools > Numbering Settings**:
- Configure comparison settings (profile, material, geometry, rotation)
- Set series prefixes per element type (B for beams, C for columns, PL for plates, etc.)
- Preview numbering before applying
- Renumber All with undo support

### Exporting to IFC for Tekla

1. **File > Export IFC...** (or `Ctrl+E`)
2. Configure settings:
   - IFC Schema: IFC2X3 (recommended for Tekla)
   - Author and Organization fields
   - Export options (profiles, materials, custom properties, split by storey)
3. Click **Export**

### Importing to Tekla Structures

1. In Tekla: **File > Import > Insert reference model**
2. Select the exported `.ifc` file
3. To convert to native objects:
   - **Manage > Convert IFC objects**
   - Select objects and click **Convert**

## Supported Elements

| Element | Description | IFC Entity | Creation Mode |
|---------|-------------|------------|---------------|
| Beam | Horizontal/inclined linear member | IfcBeam | Two-point |
| Column | Vertical linear member | IfcColumn | One-point |
| Plate | Flat steel plate | IfcPlate | Four-point |
| Slab | Floor/roof slab | IfcSlab | Dialog |
| Wall | Vertical wall | IfcWall | Dialog |
| Footing | Foundation pad/strip | IfcFooting | Dialog |
| Bolt Group | Parametric bolt array | - | One-point |
| Weld | Logical connection | - | Two-selection |
| Curved Beam | Arc-based member (barrel roofs) | IfcBeam | Script |

## Available Profiles

### UK I-Sections
- UB 305x165x40, UB 406x178x54, etc.
- UC 203x203x46, UC 254x254x73, etc.

### Hollow Sections
- SHS 100x100x5, SHS 150x150x8
- RHS 200x100x6
- CHS 168.3x7.1

### Channels
- PFC 200x90x30

## Complete Keyboard Shortcuts

### File & Edit
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New model |
| `Ctrl+O` | Open model |
| `Ctrl+S` | Save model |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+E` | Export IFC |
| `Ctrl+Q` | Exit |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+A` | Select All |
| `Delete` | Delete selected |
| `Ctrl+Shift+C` | Copy mode |
| `Ctrl+Shift+M` | Move mode |
| `Esc` | Cancel current operation |

### Viewing
| Shortcut | Action |
|----------|--------|
| `F` | Zoom to Fit |
| `1` | Front View |
| `2` | Top View |
| `3` | Right View |
| `0` | Isometric View |

### Creation
| Shortcut | Action |
|----------|--------|
| `B` | Create Beam |
| `C` | Create Column |
| `P` | Create Plate |
| `G` | Create Grid |

### Tools & Snapping
| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Drawing List |
| `F3` | Toggle All Snaps |
| `F4` | Toggle Grid Snap |
| `F5` | Toggle Endpoint Snap |
| `M` | Toggle start/end markers |

### AI Integration
| Shortcut | Action |
|----------|--------|
| `Ctrl+I` | Import Plan |
| `Ctrl+Space` | Claude prompt |
| `` Ctrl+` `` | Toggle Claude terminal |

### Mouse Controls
| Action | Effect |
|--------|--------|
| Left click | Select / pick point |
| Left drag | Box selection (window/crossing) |
| Ctrl+click | Multi-select toggle |
| Ctrl+Right drag | Rotate viewport |
| Right drag | Zoom |
| Middle drag | Pan |
| Scroll wheel | Zoom |

## Menus

| Menu | Items |
|------|-------|
| **File** | New, Open, Save, Save As, Export IFC, Exit |
| **Edit** | Undo, Redo, Select All, Delete, Copy, Move |
| **View** | Zoom to Fit, Front, Top, Right, Isometric |
| **Modeling** | Beam, Column, Plate, Bolt Group, Weld, Grid |
| **Tools** | Numbering Settings, Drawing List, Snap Toggles |
| **Claude** | Import Plan, Open Prompt, Toggle Terminal |
| **Help** | About Schmekla |

## UI Panels

| Panel | Location | Purpose |
|-------|----------|---------|
| **Model Tree** | Left dock | Hierarchical element list with type/name columns |
| **Properties Panel** | Right dock | Tekla-style grouped properties, position/offset editing |
| **Claude Terminal** | Bottom dock | Claude CLI launcher with project folder integration |
| **Status Bar** | Bottom | Operation status, coordinates with snap type, element count, units (mm) |

## Workflow: From Drawing to Tekla

1. **Prepare your drawing**: Scan or export floor plan as PNG/JPG/PDF
2. **Import in Schmekla**: Claude > Import Plan (`Ctrl+I`)
3. **Review generated model**: Check elements in 3D viewport
4. **Make adjustments**: Add/modify elements, set profiles and materials
5. **Configure numbering**: Tools > Numbering Settings for part marks
6. **Export to IFC**: File > Export IFC (`Ctrl+E`)
7. **Import to Tekla**: Insert as reference model, then convert

## Limitations

- **Connection export**: Bolt groups and welds are modeled but not yet exported to IFC (add connections in Tekla)
- **Reinforcement**: Rebar must be added in Tekla
- **Complex geometry**: Some curved/complex shapes may need simplification
- **OCC fallback**: If CadQuery/OCP solid generation fails, elements render as simplified geometry

## Technology Stack

- **Python 3.12+**: Core language
- **PySide6 (Qt 6)**: Desktop UI framework
- **PyVista + VTK**: 3D visualization and interaction
- **CadQuery + OCP**: Parametric solid geometry (OpenCascade)
- **IfcOpenShell 0.8+**: IFC file generation
- **PyMuPDF**: PDF processing for plan import
- **Claude Code CLI**: AI integration

## Development

See [CLAUDE.md](CLAUDE.md) for development guidelines, agent ecosystem, and architecture details.

### Running Tests

```bash
pytest
pytest --cov=src  # with coverage
```

## License

Proprietary - Internal use only

## Acknowledgments

- IfcOpenShell for IFC support
- PyVista for 3D visualization
- Anthropic for Claude AI
