# Schmekla

**Structural Modeling Application with AI-Assisted Design**

Schmekla is a custom structural modeling application that creates 3D steel and concrete models, exports to IFC format for Tekla Structures compatibility, and features Claude Code CLI integration for natural language model creation and automatic model generation from plan drawings.

## Features

- **3D Structural Modeling**: Create beams, columns, plates, slabs, walls, and footings
- **IFC Export**: Export models to IFC2X3 format for Tekla import
- **AI-Assisted Design**: Use natural language prompts to create and modify models
- **Plan Import**: Upload structural drawings and auto-generate models using Claude's vision
- **Parametric Components**: Pre-built portal frames, bracing systems, and floor layouts
- **UK Steel Sections**: Full catalog of UK structural steel profiles

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows 10/11 (primary target)
- Claude Code CLI installed (for AI features)

### Installation

**Option 1: Automatic Install (Windows)**

```bash
# Navigate to Schmekla folder
cd Schmekla

# Run the install script
deploy\install.bat
```

This creates a virtual environment, installs dependencies, and creates `run_schmekla.bat`.

**Option 2: Manual Install**

```bash
# Clone or download the repository
cd Schmekla

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main
```

### Deploying to Another PC

⚠️ **IMPORTANT**: The `venv/` folder contains paths specific to your machine and is NOT portable.

To deploy Schmekla to another computer:

1. **Copy these folders/files** (exclude `venv/`):
   ```
   Schmekla/
   ├── src/
   ├── resources/
   ├── deploy/
   ├── requirements.txt
   ├── pyproject.toml
   └── ... (other files, but NOT venv/)
   ```

2. **On the target PC**, run:
   ```bash
   cd Schmekla
   deploy\install.bat
   ```
   Or manually create a new venv and install dependencies.

3. **For Claude CLI features**, also install:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

## Usage

### Creating Elements Manually

1. **Via UI Dialogs**: Use the toolbar buttons or Modeling menu
   - `B` - Create Beam
   - `C` - Create Column
   - `P` - Create Plate
   - `G` - Create Grid

2. **Via Claude Terminal**: Open with `Ctrl+`` and type commands

### Importing from Plan Drawings (NEW)

The most powerful feature - auto-generate models from your drawings:

1. Go to **Claude > Import Plan...** (or `Ctrl+I`)
2. Select a plan image (PNG, JPG, or PDF)
3. Choose the plan type (Floor Plan, Elevation, Grid Layout, etc.)
4. Click **Analyze & Build Model**
5. Claude will:
   - Detect grid lines and spacings
   - Identify column positions at grid intersections
   - Recognize beam layouts
   - Create all elements automatically

### Claude Natural Language Commands

Open the Claude terminal (`Ctrl+``) and type:

```
"Create a beam from 0,0,0 to 6000,0,0 using UB 305x165x40"
"Add a column at 0,0,0 with height 4000 using UC 203x203x46"
"Create a portal frame 12 meters wide and 6 meters high"
"Create a floor slab from 0,0,3500 with width 12000 and length 18000"
"Add a shear wall from 0,0,0 to 6000,0,0 height 3500 thickness 200"
"Create a pad footing at 0,0,0 size 1500x1500 depth 500"
```

### Exporting to IFC for Tekla

1. File > Export IFC... (or `Ctrl+E`)
2. Configure settings:
   - IFC Schema: IFC2X3 (recommended for Tekla)
   - Export options
3. Click **Export**

### Importing to Tekla Structures

1. In Tekla: **File > Import > Insert reference model**
2. Select the exported `.ifc` file
3. To convert to native objects:
   - **Manage > Convert IFC objects**
   - Select objects and click **Convert**

## Project Structure

```
Schmekla/
├── src/
│   ├── core/               # Data models
│   │   ├── beam.py         # Beam element
│   │   ├── column.py       # Column element
│   │   ├── plate.py        # Plate element
│   │   ├── slab.py         # Slab element
│   │   ├── wall.py         # Wall element
│   │   ├── footing.py      # Footing element
│   │   ├── profile.py      # Section profiles
│   │   └── material.py     # Materials
│   ├── geometry/           # 3D geometry operations
│   ├── ui/                 # PySide6 user interface
│   │   ├── main_window.py  # Main application window
│   │   ├── viewport.py     # 3D PyVista viewport
│   │   └── dialogs/        # Creation dialogs
│   ├── ifc/                # IFC export engine
│   │   ├── exporter.py     # Main exporter
│   │   ├── ifc_beam.py     # Beam IFC mapping
│   │   ├── ifc_column.py   # Column IFC mapping
│   │   └── ...             # Other element mappers
│   └── claude_integration/ # AI integration
│       ├── claude_bridge.py    # Claude CLI bridge
│       └── plan_analyzer.py    # Plan image analysis
├── resources/
│   ├── profiles/           # Steel section catalogs (JSON)
│   └── materials/          # Material databases (JSON)
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## Supported Elements

| Element | Description | IFC Entity | Tekla Conversion |
|---------|-------------|------------|------------------|
| Beam | Horizontal/inclined linear member | IfcBeam | Native Beam |
| Column | Vertical linear member | IfcColumn | Native Column |
| Plate | Flat steel plate | IfcPlate | Native Plate |
| Slab | Floor/roof slab | IfcSlab | Native Slab |
| Wall | Vertical wall | IfcWall | Native Wall |
| Footing | Foundation pad/strip | IfcFooting | Native Footing |

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

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New model |
| `Ctrl+O` | Open model |
| `Ctrl+S` | Save model |
| `Ctrl+E` | Export IFC |
| `Ctrl+I` | Import Plan |
| `Ctrl+Space` | Claude prompt |
| `Ctrl+`` | Toggle Claude terminal |
| `B` | Create beam |
| `C` | Create column |
| `P` | Create plate |
| `G` | Create grid |
| `F` | Zoom to fit |
| `1` | Front view |
| `2` | Top view |
| `3` | Right view |
| `0` | Isometric view |

## Workflow: From Drawing to Tekla

1. **Prepare your drawing**: Scan or export floor plan as PNG/JPG
2. **Import in Schmekla**: Claude > Import Plan
3. **Review generated model**: Check elements in 3D viewport
4. **Make adjustments**: Add/modify elements as needed
5. **Export to IFC**: File > Export IFC
6. **Import to Tekla**: Insert as reference model, then convert

## Limitations

- **Connections**: Bolts, welds, and connections cannot be exported (add in Tekla)
- **Reinforcement**: Rebar must be added in Tekla
- **Drawings**: Drawing generation is handled by Tekla
- **Complex geometry**: Some curved/complex shapes may need simplification

## Technology Stack

- **Python 3.11+**: Core language
- **PySide6**: Qt-based desktop UI
- **PyVista + VTK**: 3D visualization
- **IfcOpenShell**: IFC file generation
- **Claude Code CLI**: AI integration

## Development

See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Running Tests

```bash
pytest
pytest --cov=src  # with coverage
```

### Building Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed src/main.py --name Schmekla
```

## License

Proprietary - Internal use only

## Acknowledgments

- IfcOpenShell for IFC support
- PyVista for 3D visualization
- Anthropic for Claude AI
