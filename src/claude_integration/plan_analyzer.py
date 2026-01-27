"""
Plan Analyzer for Schmekla.

Analyzes uploaded structural drawings/plans and generates model commands.
Uses Claude's vision capabilities to understand plans.
"""

import base64
import subprocess
import shutil
import json
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from src.core.model import StructuralModel


class PlanAnalyzer:
    """
    Analyzes structural drawings and generates model elements.

    Supports:
    - Floor plans (PNG, JPG, PDF)
    - Structural layouts
    - Grid layouts
    - Elevation drawings
    """

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'}

    def __init__(self, model: StructuralModel):
        """
        Initialize plan analyzer.

        Args:
            model: Schmekla model to populate
        """
        self.model = model
        self.last_analysis: Optional[Dict] = None

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

    def analyze_plan(self, file_path: str, plan_type: str = "auto") -> Dict[str, Any]:
        """
        Analyze a plan file and return structural information.

        Args:
            file_path: Path to plan image/PDF
            plan_type: Type of plan ("floor", "elevation", "grid", "auto")

        Returns:
            Analysis results with detected elements
        """
        path = Path(file_path)

        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return {"success": False, "error": f"Unsupported format: {path.suffix}"}

        logger.info(f"Analyzing plan: {file_path}")

        # Build analysis prompt
        prompt = self._build_analysis_prompt(path, plan_type)

        # Call Claude CLI with the image
        response = self._call_claude_with_image(path, prompt)

        # Parse response for structural data
        analysis = self._parse_analysis(response)
        self.last_analysis = analysis

        return analysis

    def build_model_from_plan(self, file_path: str, plan_type: str = "auto") -> Dict[str, Any]:
        """
        Analyze plan and automatically build model elements.

        Args:
            file_path: Path to plan image/PDF
            plan_type: Type of plan

        Returns:
            Result with created elements
        """
        # First analyze
        analysis = self.analyze_plan(file_path, plan_type)

        if not analysis.get("success", False):
            return analysis

        # Execute detected commands
        from src.claude_integration.claude_bridge import ClaudeBridge
        bridge = ClaudeBridge(self.model)

        created_elements = []
        errors = []

        commands = analysis.get("commands", [])
        for cmd in commands:
            try:
                result = bridge._execute_command(cmd)
                if result.get("success"):
                    elem_id = result.get("element_id") or result.get("element_ids", [])
                    created_elements.append({
                        "command": cmd.get("command"),
                        "element_id": elem_id
                    })
                else:
                    errors.append({
                        "command": cmd,
                        "error": result.get("error")
                    })
            except Exception as e:
                errors.append({
                    "command": cmd,
                    "error": str(e)
                })

        return {
            "success": True,
            "elements_created": len(created_elements),
            "created": created_elements,
            "errors": errors,
            "description": analysis.get("description", "")
        }

    def _build_analysis_prompt(self, path: Path, plan_type: str) -> str:
        """Build prompt for plan analysis."""

        type_context = {
            "floor": "This is a floor plan showing the layout of structural elements from above.",
            "elevation": "This is an elevation view showing the height and vertical arrangement of elements.",
            "grid": "This is a structural grid layout showing column positions and grid lines.",
            "section": "This is a section view cutting through the structure.",
            "auto": "Analyze this structural drawing and determine what type of view it is."
        }

        context = type_context.get(plan_type, type_context["auto"])

        prompt = f"""You are a structural engineer analyzing a drawing for the Schmekla structural modeling software.

{context}

Please analyze this drawing and:

1. IDENTIFY the structural elements visible:
   - Beams (horizontal straight members between columns/supports)
   - Curved beams/Hoops (arc-shaped members for barrel vault roofs)
   - Columns (vertical support members)
   - Purlins (secondary beams running perpendicular to main frames)
   - Walls (if shown as thick lines or hatched)
   - Slabs/floors (if boundaries are shown)
   - Grid lines (labeled axes like A, B, C or 1, 2, 3)
   - Footings/Foundations

2. IDENTIFY the structure type:
   - Standard building frame (flat roof)
   - Barrel vault canopy (curved/arched roof)
   - Portal frame
   - Other

3. EXTRACT dimensions and positions:
   - Grid spacings in millimeters (assume meters in drawing, multiply by 1000)
   - Overall structure dimensions (width x length)
   - Heights: ground level, eaves height, apex/ridge height
   - Element sizes if indicated

4. OUTPUT commands in this JSON format for creating the model:

For BARREL VAULT CANOPIES (curved roof structures), use create_barrel_canopy:
```schmekla-commands
{{
    "description": "Barrel vault canopy - 10m x 13m with 4 bays",
    "structure_type": "barrel_canopy",
    "commands": [
        {{
            "command": "create_barrel_canopy",
            "params": {{
                "origin": [0, 0, 0],
                "width": 10000,
                "length": 13000,
                "eaves_height": 4865,
                "apex_height": 6980,
                "num_bays": 4,
                "column_profile": "CHS 168.3x7.1",
                "hoop_profile": "CHS 168.3x7.1"
            }}
        }}
    ]
}}
```

For STANDARD STRUCTURES, use individual commands:
```schmekla-commands
{{
    "description": "Brief description of what was detected",
    "structure_type": "standard_frame",
    "grid": {{
        "x_grids": [{{"name": "A", "position": 0}}, {{"name": "B", "position": 6000}}],
        "y_grids": [{{"name": "1", "position": 0}}, {{"name": "2", "position": 6000}}]
    }},
    "commands": [
        {{"command": "create_column", "params": {{"base": [0, 0, 0], "height": 3500, "profile": "UC 203x203x46"}}}},
        {{"command": "create_beam", "params": {{"start": [0, 0, 3500], "end": [6000, 0, 3500], "profile": "UB 305x165x40"}}}}
    ]
}}
```

For INDIVIDUAL CURVED BEAMS (hoops), use:
{{"command": "create_hoop", "params": {{"grid_start": [0, 6000, 0], "grid_end": [10000, 6000, 0], "eaves_height": 4865, "apex_height": 6980, "profile": "CHS 168.3x7.1", "name": "Hoop-1"}}}}

AVAILABLE COMMANDS:
- create_column: Vertical support. params: base [x,y,z], height, profile
- create_beam: Straight beam. params: start [x,y,z], end [x,y,z], profile
- create_curved_beam: Arc beam. params: start [x,y,z], end [x,y,z], rise, profile
- create_hoop: Barrel vault hoop. params: grid_start [x,y,z], grid_end [x,y,z], eaves_height, apex_height, profile
- create_barrel_canopy: Complete canopy. params: origin, width, length, eaves_height, apex_height, num_bays, column_profile, hoop_profile
- create_footing: Foundation. params: center [x,y,z], width, length, depth

IMPORTANT NOTES:
- All dimensions must be in millimeters (mm)
- If drawing shows meters, multiply by 1000
- For barrel vaults, "width" is across the building (span of hoops), "length" is along the building
- Typical CHS profiles for canopies: CHS 168.3x7.1, CHS 139.7x5
- Look for curved elements indicating barrel/arch roofs
- Heights like "+4865" or "+6980" on drawings are in mm from ground (+0)
- Count the number of frame lines to determine num_bays

Please analyze the attached drawing and provide the schmekla-commands JSON block.
"""
        return prompt

    def _call_claude_with_image(self, image_path: Path, prompt: str) -> str:
        """
        Call Claude CLI with an image for vision analysis.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt

        Returns:
            Claude's response text
        """
        # Find claude CLI
        claude_exe = self._find_claude_cli()
        if not claude_exe:
            logger.error("Claude CLI not found in PATH or common locations")
            return "Error: Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code"

        logger.debug(f"Using Claude CLI at: {claude_exe}")

        try:
            # Use --print mode with image attachment
            # Pass prompt via stdin to avoid file permission issues
            cmd = [
                claude_exe,
                "--print",
                "--image", str(image_path),
                "--output-format", "text"
            ]

            logger.debug(f"Running Claude CLI with image: {image_path}")

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes for image analysis
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.warning(f"Claude CLI warning: {result.stderr}")

            return result.stdout or result.stderr or "No response from Claude"

        except FileNotFoundError:
            logger.error("Claude CLI not found")
            return "Error: Claude Code CLI not found. Please ensure 'claude' is in your PATH."
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timed out during image analysis")
            return "Error: Analysis timed out after 180 seconds"
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"Error: {e}"

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's analysis response.

        Args:
            response: Claude's response text

        Returns:
            Parsed analysis with commands
        """
        result = {
            "success": False,
            "raw_response": response,
            "description": "",
            "grid": None,
            "commands": []
        }

        # Look for schmekla-commands JSON block
        pattern = r'```schmekla-commands\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        if not matches:
            # Try generic JSON block
            pattern = r'```json\s*(.*?)\s*```'
            matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            try:
                data = json.loads(matches[0].strip())
                result["success"] = True
                result["description"] = data.get("description", "")
                result["grid"] = data.get("grid")
                result["commands"] = data.get("commands", [])

                logger.info(f"Parsed {len(result['commands'])} commands from analysis")

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from response: {e}")
                result["error"] = f"Failed to parse response: {e}"
        else:
            # No structured commands found, but analysis might still be useful
            result["description"] = response[:500]  # First 500 chars as description
            result["error"] = "No structured commands found in response"

        return result

    def get_analysis_summary(self) -> str:
        """Get summary of last analysis."""
        if not self.last_analysis:
            return "No analysis performed yet."

        analysis = self.last_analysis
        lines = [
            f"Description: {analysis.get('description', 'N/A')}",
            f"Commands detected: {len(analysis.get('commands', []))}",
        ]

        if analysis.get('grid'):
            grid = analysis['grid']
            lines.append(f"X Grids: {len(grid.get('x_grids', []))}")
            lines.append(f"Y Grids: {len(grid.get('y_grids', []))}")

        # Summarize commands by type
        cmd_counts = {}
        for cmd in analysis.get('commands', []):
            cmd_type = cmd.get('command', 'unknown')
            cmd_counts[cmd_type] = cmd_counts.get(cmd_type, 0) + 1

        for cmd_type, count in cmd_counts.items():
            lines.append(f"  - {cmd_type}: {count}")

        return "\n".join(lines)


def analyze_and_build(model: StructuralModel, file_path: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a plan and build the model.

    Args:
        model: Schmekla structural model
        file_path: Path to plan file

    Returns:
        Result dictionary
    """
    analyzer = PlanAnalyzer(model)
    return analyzer.build_model_from_plan(file_path)
