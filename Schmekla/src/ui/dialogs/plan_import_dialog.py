"""
Plan Import Dialog for Schmekla.

Allows users to upload structural drawings and auto-generate models.
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QGroupBox, QDialogButtonBox,
    QFileDialog, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from src.core.model import StructuralModel


class AnalysisWorker(QThread):
    """Worker thread for plan analysis."""

    finished = Signal(dict)
    progress = Signal(str)

    def __init__(self, model: StructuralModel, file_path: str, plan_type: str):
        super().__init__()
        self.model = model
        self.file_path = file_path
        self.plan_type = plan_type

    def run(self):
        """Run analysis in background."""
        try:
            self.progress.emit("Analyzing plan with Claude...")

            from src.claude_integration.plan_analyzer import PlanAnalyzer
            analyzer = PlanAnalyzer(self.model)

            self.progress.emit("Detecting structural elements...")
            result = analyzer.build_model_from_plan(self.file_path, self.plan_type)

            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.finished.emit({
                "success": False,
                "error": str(e)
            })


class PlanImportDialog(QDialog):
    """
    Dialog for importing structural plans and auto-generating models.

    Supports PNG, JPG, PDF images of floor plans, elevations, grids.
    """

    def __init__(self, model: StructuralModel, parent=None):
        """
        Initialize plan import dialog.

        Args:
            model: Schmekla model to populate
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self.file_path: Optional[str] = None
        self.worker: Optional[AnalysisWorker] = None

        self.setWindowTitle("Import Structural Plan")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("Select Plan File")
        file_layout = QHBoxLayout(file_group)

        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select a plan image or PDF...")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addWidget(file_group)

        # Plan type selection
        type_group = QGroupBox("Plan Settings")
        type_layout = QFormLayout(type_group)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Auto-detect",
            "Floor Plan",
            "Elevation View",
            "Grid Layout",
            "Section View"
        ])
        type_layout.addRow("Plan Type:", self.type_combo)

        # Scale hint
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "1:100 (default)",
            "1:50",
            "1:200",
            "1:500"
        ])
        type_layout.addRow("Drawing Scale:", self.scale_combo)

        layout.addWidget(type_group)

        # Instructions
        instructions = QLabel(
            "<b>How it works:</b><br>"
            "1. Select a structural drawing (floor plan, grid layout, etc.)<br>"
            "2. Claude AI will analyze the drawing and detect:<br>"
            "   - Grid lines and spacings<br>"
            "   - Column positions<br>"
            "   - Beam layouts<br>"
            "   - Wall locations<br>"
            "3. Elements will be automatically created in your model<br><br>"
            "<i>Supported formats: PNG, JPG, PDF</i>"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #888; padding: 10px; background: #2d2d2d; border-radius: 5px;")
        layout.addWidget(instructions)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Results area
        self.results_group = QGroupBox("Analysis Results")
        self.results_group.setVisible(False)
        results_layout = QVBoxLayout(self.results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        results_layout.addWidget(self.results_text)

        layout.addWidget(self.results_group)

        # Buttons
        btn_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("Analyze && Build Model")
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #555;
            }
            QPushButton:hover:!disabled {
                background-color: #1084d8;
            }
        """)
        btn_layout.addWidget(self.analyze_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _browse_file(self):
        """Open file browser for plan selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Structural Plan",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.gif *.webp);;PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            self.file_path = file_path
            self.file_edit.setText(file_path)
            self.analyze_btn.setEnabled(True)
            self.status_label.setText("Ready to analyze")

    def _start_analysis(self):
        """Start plan analysis."""
        if not self.file_path:
            return

        # Get plan type
        type_map = {
            "Auto-detect": "auto",
            "Floor Plan": "floor",
            "Elevation View": "elevation",
            "Grid Layout": "grid",
            "Section View": "section"
        }
        plan_type = type_map.get(self.type_combo.currentText(), "auto")

        # Disable UI during analysis
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Analyzing plan with Claude AI...")

        # Start worker thread
        self.worker = AnalysisWorker(self.model, self.file_path, plan_type)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_analysis_complete)
        self.worker.start()

    def _on_progress(self, message: str):
        """Handle progress update."""
        self.status_label.setText(message)

    def _on_analysis_complete(self, result: dict):
        """Handle analysis completion."""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)

        if result.get("success"):
            elements_created = result.get("elements_created", 0)
            self.status_label.setText(f"Successfully created {elements_created} elements!")
            self.status_label.setStyleSheet("color: #5cb85c;")

            # Show results
            self.results_group.setVisible(True)

            results_text = []
            results_text.append(f"Description: {result.get('description', 'N/A')}")
            results_text.append(f"Elements created: {elements_created}")

            if result.get('created'):
                results_text.append("\nCreated elements:")
                for elem in result['created'][:10]:
                    results_text.append(f"  - {elem['command']}: {elem['element_id']}")
                if len(result['created']) > 10:
                    results_text.append(f"  ... and {len(result['created']) - 10} more")

            if result.get('errors'):
                results_text.append(f"\nErrors: {len(result['errors'])}")
                for err in result['errors'][:3]:
                    results_text.append(f"  - {err.get('error', 'Unknown error')}")

            self.results_text.setText("\n".join(results_text))

            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully created {elements_created} structural elements from the plan.\n\n"
                "The model has been updated. You can now:\n"
                "- View elements in 3D viewport\n"
                "- Edit element properties\n"
                "- Export to IFC for Tekla"
            )

        else:
            error = result.get("error", "Unknown error")
            self.status_label.setText(f"Analysis failed: {error}")
            self.status_label.setStyleSheet("color: #d9534f;")

            # Show error details
            self.results_group.setVisible(True)
            self.results_text.setText(f"Error: {error}\n\nRaw response:\n{result.get('raw_response', 'N/A')[:1000]}")

            QMessageBox.warning(
                self,
                "Analysis Failed",
                f"Could not analyze the plan:\n{error}\n\n"
                "Possible solutions:\n"
                "- Ensure the image is clear and readable\n"
                "- Try a different plan type setting\n"
                "- Make sure Claude CLI is installed and accessible"
            )
