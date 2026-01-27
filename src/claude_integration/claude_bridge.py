"""
Claude Code CLI Bridge for Schmekla.

Connects Schmekla to Claude Code CLI for AI-assisted modeling.
"""

import subprocess
import shutil
import json
import re
import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from src.core.model import StructuralModel
from src.core.element import ElementType


class ClaudeBridge:
    """
    Bridge between Schmekla and Claude Code CLI.

    Handles prompt building, CLI communication, and command execution.
    """

    def __init__(self, model: StructuralModel):
        """
        Initialize Claude bridge.

        Args:
            model: Schmekla model to operate on
        """
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 50

    def send_prompt(self, user_prompt: str) -> str:
        """
        Send prompt to Claude and return response.

        Args:
            user_prompt: User's natural language prompt

        Returns:
            Claude's response text
        """
        logger.info(f"Sending prompt to Claude: {user_prompt[:50]}...")

        # Build full prompt with context
        full_prompt = self._build_full_prompt(user_prompt)

        # Call Claude CLI
        response = self._call_claude_cli(full_prompt)

        # Parse and execute any commands
        commands = self._extract_commands(response)
        for cmd in commands:
            try:
                result = self._execute_command(cmd)
                logger.debug(f"Executed command: {cmd['command']} -> {result}")
            except Exception as e:
                logger.error(f"Failed to execute command: {e}")

        # Store in history
        self._add_to_history("user", user_prompt)
        self._add_to_history("assistant", response)

        return response

    def _extract_and_read_files(self, user_prompt: str) -> str:
        """
        Extract file/folder paths from user prompt and read their contents.

        Args:
            user_prompt: User's prompt that may contain file paths

        Returns:
            String containing file contents, or empty string
        """
        import re

        # Match Windows paths like C:\..., or relative paths
        path_pattern = r'([A-Za-z]:\\[^\s\'"<>|*?]+|\.{1,2}[\\/][^\s\'"<>|*?]+)'
        matches = re.findall(path_pattern, user_prompt)

        if not matches:
            return ""

        file_contents = []

        for path_str in matches:
            path = Path(path_str)
            try:
                if path.is_file():
                    # Read file
                    content = self._read_file_safely(path)
                    if content:
                        file_contents.append(f"### File: {path.name}\n```\n{content}\n```")
                elif path.is_dir():
                    # Read directory contents
                    dir_contents = self._read_directory(path)
                    if dir_contents:
                        file_contents.append(f"### Folder: {path.name}\n{dir_contents}")
            except Exception as e:
                logger.warning(f"Could not read {path}: {e}")
                file_contents.append(f"### {path}: Could not read - {e}")

        if file_contents:
            return "\n\n## Referenced Files/Folders:\n" + "\n\n".join(file_contents)
        return ""

    def _read_file_safely(self, path: Path, max_size: int = 50000) -> Optional[str]:
        """Read a file with size limits."""
        try:
            if path.stat().st_size > max_size:
                return f"[File too large: {path.stat().st_size} bytes, max {max_size}]"

            # Handle different file types
            suffix = path.suffix.lower()
            if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf'}:
                return f"[Binary file: {suffix} - use Plan Import for images]"

            return path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            return f"[Error reading: {e}]"

    def _read_directory(self, path: Path, max_files: int = 20) -> str:
        """Read contents of a directory."""
        contents = []
        files_read = 0

        for item in sorted(path.iterdir()):
            if files_read >= max_files:
                contents.append(f"\n... and {len(list(path.iterdir())) - max_files} more files")
                break

            if item.is_file():
                suffix = item.suffix.lower()
                if suffix in {'.txt', '.md', '.json', '.csv', '.xml', '.yaml', '.yml'}:
                    content = self._read_file_safely(item, max_size=20000)
                    contents.append(f"#### {item.name}\n```\n{content}\n```")
                    files_read += 1
                elif suffix in {'.png', '.jpg', '.jpeg', '.pdf', '.dwg', '.dxf'}:
                    contents.append(f"#### {item.name}\n[Image/Drawing file - use Plan Import feature]")
                    files_read += 1

        return "\n".join(contents) if contents else "[Empty or no readable files]"

    def _build_full_prompt(self, user_prompt: str) -> str:
        """Build full prompt with model context."""
        context = self._build_context()

        # Read any referenced files
        file_context = self._extract_and_read_files(user_prompt)

        system_prompt = f"""You are a structural engineering AI assistant integrated into Schmekla, a 3D structural modeling application.

Your role is to help users create and modify structural models by:
1. Understanding their requirements (from text descriptions, specifications, or file contents)
2. Generating commands to create structural elements (beams, columns, slabs, etc.)
3. Providing engineering guidance

## Current Model State:
{context}
{file_context}

## How to Create Elements:
Output commands in this JSON format - you can include multiple commands:
```schmekla-command
{{"command": "create_beam", "params": {{"start": [0,0,0], "end": [6000,0,0], "profile": "UB 305x165x40"}}}}
```

## Available Commands:

### Structural Elements:
- **create_column**: Vertical support
  - Params: base [x,y,z], height (mm), profile, material (optional), rotation (optional), name (optional)

- **create_beam**: Horizontal/inclined beam
  - Params: start [x,y,z], end [x,y,z], profile, material (optional), name (optional)

- **create_curved_beam**: Arc/curved beam
  - Params: start [x,y,z], end [x,y,z], rise (mm), profile, segments (optional), name (optional)

- **create_slab**: Floor/roof slab
  - Params: points [[x,y,z],...] OR origin + width + length, thickness (mm), slab_type ("floor"/"roof"), name (optional)

- **create_wall**: Wall element
  - Params: start [x,y,z], end [x,y,z], height (mm), thickness (mm), wall_type ("standard"/"shear"/"retaining"), name (optional)

- **create_footing**: Foundation
  - Params: center [x,y,z], width (mm), length (mm), depth (mm), footing_type ("pad"/"strip"/"mat"), name (optional)

- **create_plate**: Steel plate
  - Params: points [[x,y,z],...] OR origin + width + length, thickness (mm), name (optional)

### Assemblies:
- **create_portal_frame**: Complete portal frame
  - Params: width (mm), height (mm), profile_beam, profile_column, origin [x,y,z]

- **create_barrel_canopy**: Barrel vault canopy structure
  - Params: origin, width, length, eaves_height, apex_height, num_bays, column_profile, hoop_profile

### Modification:
- **modify_element**: Change element property
  - Params: element_id, property, value
- **delete_element**: Remove element
  - Params: element_id

## Units & Profiles:
- All dimensions in **millimeters (mm)**
- Profiles: "UB 305x165x40", "UB 406x178x54", "UC 203x203x46", "UC 254x254x73", "SHS 100x100x5", "RHS 200x100x6", "CHS 168.3x7.1", "PFC 200x90x30"
- Materials: "S355" (steel), "C30/37" (concrete)

## User Request:
{user_prompt}

Analyze the request and any provided files. If the user wants to create a structural model, output the appropriate schmekla-command blocks. Explain what you're creating.
"""
        return system_prompt

    def _build_context(self) -> str:
        """Build context string describing current model."""
        parts = []

        parts.append(f"Model: {self.model.name}")
        parts.append(f"Total elements: {self.model.element_count}")

        # Elements by type
        for elem_type in ElementType:
            elements = self.model.get_elements_by_type(elem_type)
            if elements:
                parts.append(f"\n{elem_type.value.title()}s ({len(elements)}):")
                for elem in elements[:5]:
                    desc = self._describe_element(elem)
                    parts.append(f"  - {elem.name or str(elem.id)[:8]}: {desc}")
                if len(elements) > 5:
                    parts.append(f"  ... and {len(elements) - 5} more")

        # Selected elements
        selected = self.model.get_selected_ids()
        if selected:
            parts.append(f"\nSelected: {len(selected)} elements")

        return "\n".join(parts)

    def _describe_element(self, elem) -> str:
        """Create short description of element."""
        props = elem.get_properties()
        if "Start Point" in props:
            return f"{elem.profile.name if elem.profile else 'unknown'}, {props.get('Length', 'unknown length')}"
        return elem.profile.name if elem.profile else "unknown"

    def _find_claude_cli(self) -> Optional[str]:
        """
        Find the Claude CLI executable.

        Returns:
            Path to claude executable, or None if not found
        """
        # First try shutil.which (respects PATH)
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path

        # On Windows, also try .cmd extension explicitly
        if sys.platform == "win32":
            claude_path = shutil.which("claude.cmd")
            if claude_path:
                return claude_path

        # Check common npm global install locations
        home = Path.home()
        common_paths = []

        if sys.platform == "win32":
            # Windows npm paths
            common_paths = [
                home / "AppData" / "Roaming" / "npm" / "claude.cmd",
                home / "AppData" / "Roaming" / "npm" / "claude",
                Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd",
                Path("C:/Program Files/nodejs/claude.cmd"),
            ]
        else:
            # macOS/Linux npm paths
            common_paths = [
                home / ".npm-global" / "bin" / "claude",
                Path("/usr/local/bin/claude"),
                Path("/usr/bin/claude"),
            ]

        for path in common_paths:
            if path.exists():
                return str(path)

        return None

    def _call_claude_cli(self, prompt: str) -> str:
        """
        Call Claude Code CLI and return response.

        Args:
            prompt: Full prompt to send

        Returns:
            Response text
        """
        # Find claude CLI
        claude_exe = self._find_claude_cli()
        if not claude_exe:
            logger.error("Claude CLI not found in PATH or common locations")
            return "Error: Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code"

        logger.debug(f"Using Claude CLI at: {claude_exe}")

        try:
            # Use --print flag with prompt via stdin for non-interactive mode
            # This avoids file permission issues and works with long prompts
            cmd = [claude_exe, "--print", "--output-format", "text"]

            logger.debug(f"Running Claude CLI in print mode")

            # Pass prompt via stdin to avoid command line length limits
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes for complex prompts
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.warning(f"Claude CLI returned non-zero: {result.stderr}")
                # Check for common error patterns
                if "permission" in result.stderr.lower():
                    return "Error: Claude CLI permission issue. Try running Schmekla from a terminal."

            response = result.stdout or result.stderr or "No response from Claude"
            return response

        except FileNotFoundError:
            logger.error("Claude CLI not found")
            return "Error: Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code"
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timed out")
            return "Error: Claude request timed out after 120 seconds"
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"Error: {e}"

    def _extract_commands(self, response: str) -> List[Dict]:
        """
        Extract schmekla-command blocks from response.

        Args:
            response: Claude's response text

        Returns:
            List of command dictionaries
        """
        commands = []
        pattern = r'```schmekla-command\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            try:
                cmd = json.loads(match.strip())
                if "command" in cmd:
                    commands.append(cmd)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse command JSON: {e}")

        logger.debug(f"Extracted {len(commands)} commands from response")
        return commands

    def _execute_command(self, command: Dict) -> Dict:
        """
        Execute a model command.

        Args:
            command: Command dictionary with 'command' and 'params'

        Returns:
            Result dictionary
        """
        cmd_name = command.get("command")
        params = command.get("params", {})

        logger.info(f"Executing command: {cmd_name}")

        if cmd_name == "create_beam":
            return self._cmd_create_beam(params)
        elif cmd_name == "create_curved_beam":
            return self._cmd_create_curved_beam(params)
        elif cmd_name == "create_hoop":
            return self._cmd_create_hoop(params)
        elif cmd_name == "create_column":
            return self._cmd_create_column(params)
        elif cmd_name == "create_plate":
            return self._cmd_create_plate(params)
        elif cmd_name == "create_slab":
            return self._cmd_create_slab(params)
        elif cmd_name == "create_wall":
            return self._cmd_create_wall(params)
        elif cmd_name == "create_footing":
            return self._cmd_create_footing(params)
        elif cmd_name == "create_portal_frame":
            return self._cmd_create_portal_frame(params)
        elif cmd_name == "create_barrel_canopy":
            return self._cmd_create_barrel_canopy(params)
        elif cmd_name == "delete_element":
            return self._cmd_delete_element(params)
        elif cmd_name == "modify_element":
            return self._cmd_modify_element(params)
        else:
            return {"success": False, "error": f"Unknown command: {cmd_name}"}

    def _cmd_create_beam(self, params: Dict) -> Dict:
        """Create beam command."""
        from src.core.beam import Beam
        from src.core.profile import Profile
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            start = Point3D(*params["start"])
            end = Point3D(*params["end"])
            profile = Profile.from_name(params.get("profile", "UB 305x165x40"))
            material = Material.from_name(params.get("material", "S355"))

            beam = Beam(start, end, profile, material)
            self.model.add_element(beam)

            return {"success": True, "element_id": str(beam.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_curved_beam(self, params: Dict) -> Dict:
        """Create curved beam/arc command."""
        from src.core.curved_beam import CurvedBeam
        from src.core.profile import Profile
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            start = Point3D(*params["start"])
            end = Point3D(*params["end"])
            rise = float(params["rise"])
            profile = Profile.from_name(params.get("profile", "CHS 168.3x7.1"))
            material = Material.from_name(params.get("material", "S355"))
            segments = int(params.get("segments", 12))
            name = params.get("name", "")

            curved_beam = CurvedBeam(start, end, rise, profile, material, name=name, segments=segments)
            self.model.add_element(curved_beam)

            return {"success": True, "element_id": str(curved_beam.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_hoop(self, params: Dict) -> Dict:
        """Create barrel vault hoop from grid positions."""
        from src.core.curved_beam import create_barrel_hoop
        from src.core.profile import Profile
        from src.geometry.point import Point3D

        try:
            grid_start = Point3D(*params["grid_start"])
            grid_end = Point3D(*params["grid_end"])
            eaves_height = float(params["eaves_height"])
            apex_height = float(params["apex_height"])
            profile = Profile.from_name(params.get("profile", "CHS 168.3x7.1"))
            name = params.get("name", "")

            hoop = create_barrel_hoop(grid_start, grid_end, eaves_height, apex_height, profile, name)
            self.model.add_element(hoop)

            return {"success": True, "element_id": str(hoop.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_barrel_canopy(self, params: Dict) -> Dict:
        """Create complete barrel vault canopy structure."""
        from src.core.curved_beam import create_barrel_hoop
        from src.core.column import Column
        from src.core.beam import Beam
        from src.core.footing import Footing
        from src.core.profile import Profile
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            ox, oy, oz = params.get("origin", [0, 0, 0])
            width = float(params.get("width", 10000))  # Across building
            length = float(params.get("length", 13000))  # Along building
            eaves_height = float(params.get("eaves_height", 4865))
            apex_height = float(params.get("apex_height", 6980))
            num_bays = int(params.get("num_bays", 4))  # Number of bays along length

            col_profile = Profile.from_name(params.get("column_profile", "CHS 168.3x7.1"))
            hoop_profile = Profile.from_name(params.get("hoop_profile", "CHS 168.3x7.1"))
            purlin_profile = Profile.from_name(params.get("purlin_profile", "SHS 100x100x5"))
            material = Material.default_steel()

            created_ids = []

            # Calculate bay spacing
            bay_spacing = length / num_bays

            # Create columns and hoops at each bay line
            for i in range(num_bays + 1):
                y_pos = oy + i * bay_spacing

                # Column at grid B (left side)
                col_b_base = Point3D(ox, y_pos, oz)
                col_b_top = Point3D(ox, y_pos, oz + eaves_height)
                col_b = Column(
                    start_point=col_b_base,
                    end_point=col_b_top,
                    profile=col_profile,
                    material=material,
                    name=f"Col-B{i+1}"
                )
                self.model.add_element(col_b)
                created_ids.append(str(col_b.id))

                # Column at grid C (right side)
                col_c_base = Point3D(ox + width, y_pos, oz)
                col_c_top = Point3D(ox + width, y_pos, oz + eaves_height)
                col_c = Column(
                    start_point=col_c_base,
                    end_point=col_c_top,
                    profile=col_profile,
                    material=material,
                    name=f"Col-C{i+1}"
                )
                self.model.add_element(col_c)
                created_ids.append(str(col_c.id))

                # Hoop from B to C at this bay line
                hoop = create_barrel_hoop(
                    Point3D(ox, y_pos, 0),
                    Point3D(ox + width, y_pos, 0),
                    eaves_height,
                    apex_height,
                    hoop_profile,
                    f"Hoop-{i+1}"
                )
                self.model.add_element(hoop)
                created_ids.append(str(hoop.id))

                # Footings under columns
                footing_b = Footing(Point3D(ox, y_pos, oz - 500), 1200, 1200, 500, name=f"Ftg-B{i+1}")
                self.model.add_element(footing_b)
                created_ids.append(str(footing_b.id))

                footing_c = Footing(Point3D(ox + width, y_pos, oz - 500), 1200, 1200, 500, name=f"Ftg-C{i+1}")
                self.model.add_element(footing_c)
                created_ids.append(str(footing_c.id))

            # Create purlins between hoops (at eaves and ridge)
            for i in range(num_bays):
                y1 = oy + i * bay_spacing
                y2 = oy + (i + 1) * bay_spacing

                # Eaves purlin at B
                purlin_b = Beam(
                    Point3D(ox, y1, eaves_height),
                    Point3D(ox, y2, eaves_height),
                    purlin_profile, material, name=f"Purlin-B{i+1}"
                )
                self.model.add_element(purlin_b)
                created_ids.append(str(purlin_b.id))

                # Eaves purlin at C
                purlin_c = Beam(
                    Point3D(ox + width, y1, eaves_height),
                    Point3D(ox + width, y2, eaves_height),
                    purlin_profile, material, name=f"Purlin-C{i+1}"
                )
                self.model.add_element(purlin_c)
                created_ids.append(str(purlin_c.id))

                # Ridge purlin
                ridge_purlin = Beam(
                    Point3D(ox + width/2, y1, apex_height),
                    Point3D(ox + width/2, y2, apex_height),
                    purlin_profile, material, name=f"Purlin-Ridge{i+1}"
                )
                self.model.add_element(ridge_purlin)
                created_ids.append(str(ridge_purlin.id))

            return {
                "success": True,
                "element_ids": created_ids,
                "summary": f"Created barrel canopy: {num_bays+1} frames, {(num_bays+1)*2} columns, {num_bays+1} hoops, {num_bays*3} purlins, {(num_bays+1)*2} footings"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_column(self, params: Dict) -> Dict:
        """Create column command."""
        from src.core.column import Column
        from src.core.profile import Profile
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            base = Point3D(*params["base"])
            height = float(params["height"])
            profile = Profile.from_name(params.get("profile", "UC 203x203x46"))
            material = Material.from_name(params.get("material", "S355"))
            rotation = float(params.get("rotation", 0))
            name = params.get("name", "")

            # Column requires start_point and end_point, not base and height
            end = Point3D(base.x, base.y, base.z + height)
            column = Column(
                start_point=base,
                end_point=end,
                profile=profile,
                material=material,
                rotation=rotation,
                name=name
            )
            self.model.add_element(column)

            return {"success": True, "element_id": str(column.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_plate(self, params: Dict) -> Dict:
        """Create plate command."""
        from src.core.plate import Plate
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            # Points can be list of [x,y,z] or use origin/width/length
            if "points" in params:
                points = [Point3D(*p) for p in params["points"]]
            else:
                # Create rectangular from origin
                ox, oy, oz = params.get("origin", [0, 0, 0])
                width = float(params.get("width", 300))
                length = float(params.get("length", 300))
                points = [
                    Point3D(ox, oy, oz),
                    Point3D(ox + width, oy, oz),
                    Point3D(ox + width, oy + length, oz),
                    Point3D(ox, oy + length, oz),
                ]

            thickness = float(params.get("thickness", 20))
            material = Material.from_name(params.get("material", "S355"))
            name = params.get("name", "")

            plate = Plate(points, thickness, material, name)
            self.model.add_element(plate)

            return {"success": True, "element_id": str(plate.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_slab(self, params: Dict) -> Dict:
        """Create slab command."""
        from src.core.slab import Slab
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            if "points" in params:
                points = [Point3D(*p) for p in params["points"]]
            else:
                ox, oy, oz = params.get("origin", [0, 0, 0])
                width = float(params.get("width", 6000))
                length = float(params.get("length", 6000))
                points = [
                    Point3D(ox, oy, oz),
                    Point3D(ox + width, oy, oz),
                    Point3D(ox + width, oy + length, oz),
                    Point3D(ox, oy + length, oz),
                ]

            thickness = float(params.get("thickness", 200))
            material = Material.from_name(params.get("material", "C30/37"))
            name = params.get("name", "")

            slab = Slab(points, thickness, material, name)
            slab.slab_type = params.get("slab_type", "floor")
            self.model.add_element(slab)

            return {"success": True, "element_id": str(slab.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_wall(self, params: Dict) -> Dict:
        """Create wall command."""
        from src.core.wall import Wall
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            start = Point3D(*params["start"])
            end = Point3D(*params["end"])
            height = float(params["height"])
            thickness = float(params.get("thickness", 200))
            material = Material.from_name(params.get("material", "C30/37"))
            name = params.get("name", "")

            wall = Wall(start, end, height, thickness, material, name)
            wall.wall_type = params.get("wall_type", "standard")
            self.model.add_element(wall)

            return {"success": True, "element_id": str(wall.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_footing(self, params: Dict) -> Dict:
        """Create footing command."""
        from src.core.footing import Footing
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            center = Point3D(*params["center"])
            width = float(params.get("width", 1500))
            length = float(params.get("length", 1500))
            depth = float(params.get("depth", 500))
            material = Material.from_name(params.get("material", "C30/37"))
            name = params.get("name", "")

            footing = Footing(center, width, length, depth, material, name)
            footing.footing_type = params.get("footing_type", "pad")
            self.model.add_element(footing)

            return {"success": True, "element_id": str(footing.id)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_create_portal_frame(self, params: Dict) -> Dict:
        """Create portal frame command."""
        from src.core.beam import Beam
        from src.core.column import Column
        from src.core.profile import Profile
        from src.core.material import Material
        from src.geometry.point import Point3D

        try:
            width = params.get("width", 12000)
            height = params.get("height", 6000)
            origin = params.get("origin", [0, 0, 0])
            beam_profile = Profile.from_name(params.get("profile_beam", "UB 406x178x54"))
            col_profile = Profile.from_name(params.get("profile_column", "UC 254x254x73"))
            material = Material.default_steel()

            ox, oy, oz = origin

            # Create columns using Column class
            col1_base = Point3D(ox, oy, oz)
            col2_base = Point3D(ox + width, oy, oz)
            col1_top = Point3D(ox, oy, oz + height)
            col2_top = Point3D(ox + width, oy, oz + height)

            col1 = Column(
                start_point=col1_base,
                end_point=col1_top,
                profile=col_profile,
                material=material,
                name="Col-1"
            )
            col2 = Column(
                start_point=col2_base,
                end_point=col2_top,
                profile=col_profile,
                material=material,
                name="Col-2"
            )

            # Create rafter beam at top
            rafter = Beam(col1_top, col2_top, beam_profile, material, name="Rafter")

            self.model.add_element(col1)
            self.model.add_element(col2)
            self.model.add_element(rafter)

            return {
                "success": True,
                "element_ids": [str(col1.id), str(col2.id), str(rafter.id)]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_delete_element(self, params: Dict) -> Dict:
        """Delete element command."""
        from uuid import UUID
        try:
            elem_id = UUID(params["element_id"])
            success = self.model.remove_element(elem_id)
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _cmd_modify_element(self, params: Dict) -> Dict:
        """Modify element command."""
        from uuid import UUID
        try:
            elem_id = UUID(params["element_id"])
            element = self.model.get_element(elem_id)
            if element:
                prop = params["property"]
                value = params["value"]
                success = element.set_property(prop, value)
                if success:
                    self.model.element_modified.emit(element)
                return {"success": success}
            return {"success": False, "error": "Element not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        # Trim history
        while len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
