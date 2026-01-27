"""
Claude Code CLI integration for Schmekla.

Provides natural language model creation and modification,
plus automatic model generation from plan images.
"""

from src.claude_integration.claude_bridge import ClaudeBridge
from src.claude_integration.plan_analyzer import PlanAnalyzer, analyze_and_build

__all__ = [
    "ClaudeBridge",
    "PlanAnalyzer",
    "analyze_and_build",
]
