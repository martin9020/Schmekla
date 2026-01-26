"""
IFC Export dialog for Schmekla.
"""

from typing import Optional
from pathlib import Path
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QDialogButtonBox, QPushButton,
    QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt


class ExportDialog(QDialog):
    """Dialog for IFC export settings."""

    def __init__(self, parent=None, default_name: str = "model"):
        """
        Initialize export dialog.

        Args:
            parent: Parent widget
            default_name: Default filename
        """
        super().__init__(parent)
        self.default_name = default_name
        self.export_path: Optional[str] = None
        self.export_settings: dict = {}

        self.setWindowTitle("Export to IFC")
        self.setMinimumWidth(450)

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # File selection group
        file_group = QGroupBox("Output File")
        file_layout = QHBoxLayout(file_group)

        self.path_edit = QLineEdit()
        default_path = str(Path.home() / f"{self.default_name}.ifc")
        self.path_edit.setText(default_path)
        file_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addWidget(file_group)

        # IFC Settings group
        settings_group = QGroupBox("IFC Settings")
        settings_layout = QFormLayout(settings_group)

        self.schema_combo = QComboBox()
        self.schema_combo.addItems(["IFC2X3", "IFC4"])
        self.schema_combo.setCurrentText("IFC2X3")  # Default for Tekla
        settings_layout.addRow("IFC Schema:", self.schema_combo)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Author name")
        settings_layout.addRow("Author:", self.author_edit)

        self.org_edit = QLineEdit()
        self.org_edit.setPlaceholderText("Organization")
        settings_layout.addRow("Organization:", self.org_edit)

        layout.addWidget(settings_group)

        # Export Options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)

        self.export_profiles_cb = QCheckBox("Export profile definitions")
        self.export_profiles_cb.setChecked(True)
        options_layout.addWidget(self.export_profiles_cb)

        self.export_materials_cb = QCheckBox("Export material properties")
        self.export_materials_cb.setChecked(True)
        options_layout.addWidget(self.export_materials_cb)

        self.export_properties_cb = QCheckBox("Export Schmekla custom properties")
        self.export_properties_cb.setChecked(True)
        options_layout.addWidget(self.export_properties_cb)

        self.split_by_storey_cb = QCheckBox("Split elements by storey")
        self.split_by_storey_cb.setChecked(False)
        options_layout.addWidget(self.split_by_storey_cb)

        layout.addWidget(options_group)

        # Info label
        info_label = QLabel(
            "Note: IFC2X3 is recommended for Tekla Structures compatibility.\n"
            "IFC4 provides more features but may have import issues."
        )
        info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText("Export")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _browse_file(self):
        """Open file browser for export path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export IFC File",
            self.path_edit.text(),
            "IFC Files (*.ifc)"
        )
        if file_path:
            self.path_edit.setText(file_path)

    def _on_accept(self):
        """Handle dialog acceptance."""
        path = self.path_edit.text().strip()
        if not path:
            return

        # Ensure .ifc extension
        if not path.lower().endswith('.ifc'):
            path += '.ifc'

        self.export_path = path
        self.export_settings = {
            "schema": self.schema_combo.currentText(),
            "author": self.author_edit.text(),
            "organization": self.org_edit.text(),
            "export_profiles": self.export_profiles_cb.isChecked(),
            "export_materials": self.export_materials_cb.isChecked(),
            "export_properties": self.export_properties_cb.isChecked(),
            "split_by_storey": self.split_by_storey_cb.isChecked(),
        }

        self.accept()

    def get_export_path(self) -> Optional[str]:
        """Get the export file path."""
        return self.export_path

    def get_settings(self) -> dict:
        """Get the export settings."""
        return self.export_settings
