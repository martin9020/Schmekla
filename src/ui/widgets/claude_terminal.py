"""
Claude Integration Widget for Schmekla.

Provides two modes:
1. External terminal launcher (opens Claude in Windows Terminal/cmd)
2. API-based chat (uses Anthropic SDK directly)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat


class ClaudeTerminal(QWidget):
    """
    Claude integration widget with external terminal launcher.

    Opens Claude CLI in a proper terminal window where it works fully.
    """

    model_changed = Signal()

    def __init__(self, working_dir: Optional[Path] = None, parent=None):
        super().__init__(parent)

        self.working_dir = working_dir or Path.cwd()
        self.claude_path: Optional[str] = None

        self._find_claude()
        self._setup_ui()

    def _find_claude(self):
        """Find Claude CLI executable."""
        self.claude_path = shutil.which("claude")
        if self.claude_path:
            return

        if sys.platform == "win32":
            self.claude_path = shutil.which("claude.cmd")
            if self.claude_path:
                return

            npm_path = Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
            if npm_path.exists():
                self.claude_path = str(npm_path)

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Info label
        info = QLabel(
            "<b>Claude Code CLI Integration</b><br><br>"
            "Click the button below to open Claude in a terminal window. "
            "Claude will have full access to read/write files in your project folder.<br><br>"
            f"<b>Project folder:</b> {self.working_dir}"
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background-color: #252526;
                padding: 12px;
                border-radius: 6px;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()

        self.open_btn = QPushButton("🚀 Open Claude in Terminal")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """)
        self.open_btn.clicked.connect(self.open_terminal)
        btn_layout.addWidget(self.open_btn)

        self.open_here_btn = QPushButton("📂 Open in Conditions Folder")
        self.open_here_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3d7a37;
            }
        """)
        self.open_here_btn.clicked.connect(self.open_terminal_conditions)
        btn_layout.addWidget(self.open_here_btn)

        layout.addLayout(btn_layout)

        # Tips
        tips = QLabel(
            "<b>Tips for using Claude:</b><br>"
            "• Say: <i>\"Read the Conditions folder and create a barrel vault model\"</i><br>"
            "• Say: <i>\"Create a portal frame 12m wide, 6m high\"</i><br>"
            "• Say: <i>\"Modify the beam profile to UB 406x178x54\"</i><br>"
            "• Type <b>/help</b> for Claude commands"
        )
        tips.setWordWrap(True)
        tips.setStyleSheet("""
            QLabel {
                background-color: #1e3a1e;
                padding: 12px;
                border-radius: 6px;
                color: #98c379;
                font-size: 12px;
            }
        """)
        layout.addWidget(tips)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        if not self.claude_path:
            self.open_btn.setEnabled(False)
            self.open_here_btn.setEnabled(False)
            self.status_label.setText(
                "⚠️ Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )
            self.status_label.setStyleSheet("color: #f44747;")

    def open_terminal(self, folder: Optional[Path] = None):
        """Open Claude in a new terminal window."""
        if not self.claude_path:
            QMessageBox.warning(
                self, "Claude Not Found",
                "Claude CLI is not installed.\n\n"
                "Install it with:\nnpm install -g @anthropic-ai/claude-code"
            )
            return

        work_dir = folder or self.working_dir

        try:
            if sys.platform == "win32":
                # Try Windows Terminal first, fall back to cmd
                try:
                    # Windows Terminal
                    subprocess.Popen(
                        ["wt", "-d", str(work_dir), "cmd", "/k", self.claude_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    self.status_label.setText(f"✓ Opened Claude in Windows Terminal at {work_dir.name}")
                except FileNotFoundError:
                    # Fall back to cmd.exe
                    subprocess.Popen(
                        f'start cmd /k "cd /d {work_dir} && {self.claude_path}"',
                        shell=True
                    )
                    self.status_label.setText(f"✓ Opened Claude in Command Prompt at {work_dir.name}")
            elif sys.platform == "darwin":
                # macOS
                script = f'cd "{work_dir}" && "{self.claude_path}"'
                subprocess.Popen([
                    "osascript", "-e",
                    f'tell app "Terminal" to do script "{script}"'
                ])
                self.status_label.setText(f"✓ Opened Claude in Terminal at {work_dir.name}")
            else:
                # Linux - try common terminals
                for terminal in ["gnome-terminal", "konsole", "xterm"]:
                    if shutil.which(terminal):
                        subprocess.Popen([
                            terminal, "--working-directory", str(work_dir),
                            "-e", self.claude_path
                        ])
                        self.status_label.setText(f"✓ Opened Claude in {terminal}")
                        break

            self.status_label.setStyleSheet("color: #4ec9b0;")

        except Exception as e:
            logger.error(f"Failed to open terminal: {e}")
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44747;")

    def open_terminal_conditions(self):
        """Open Claude in the Conditions folder."""
        conditions = self.working_dir / "Conditions"
        if conditions.exists():
            self.open_terminal(conditions)
        else:
            self.open_terminal(self.working_dir)

    def start_session(self):
        """For compatibility - just show the widget."""
        pass

    def restart_session(self):
        """For compatibility - open a new terminal."""
        self.open_terminal()

    def set_working_directory(self, path: Path):
        """Update working directory."""
        self.working_dir = path
