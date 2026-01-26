"""
Column creation dialog for Schmekla.
"""

from typing import Optional
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QGroupBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

from src.core.column import Column
from src.core.profile import Profile, ProfileCatalog
from src.core.material import Material, MaterialCatalog
from src.geometry.point import Point3D


class ColumnDialog(QDialog):
    """Dialog for creating or editing a column."""

    def __init__(self, parent=None, column: Optional[Column] = None):
        """
        Initialize column dialog.

        Args:
            parent: Parent widget
            column: Existing column to edit (None for new column)
        """
        super().__init__(parent)
        self.column = column
        self.result_column: Optional[Column] = None

        self.setWindowTitle("Create Column" if column is None else "Edit Column")
        self.setMinimumWidth(400)

        self._setup_ui()
        self._populate_combos()

        if column:
            self._load_column_data(column)

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Base point group
        base_group = QGroupBox("Base Point")
        base_layout = QFormLayout(base_group)

        self.base_x = QDoubleSpinBox()
        self.base_x.setRange(-1e9, 1e9)
        self.base_x.setDecimals(1)
        self.base_x.setSuffix(" mm")
        base_layout.addRow("X:", self.base_x)

        self.base_y = QDoubleSpinBox()
        self.base_y.setRange(-1e9, 1e9)
        self.base_y.setDecimals(1)
        self.base_y.setSuffix(" mm")
        base_layout.addRow("Y:", self.base_y)

        self.base_z = QDoubleSpinBox()
        self.base_z.setRange(-1e9, 1e9)
        self.base_z.setDecimals(1)
        self.base_z.setSuffix(" mm")
        base_layout.addRow("Z:", self.base_z)

        layout.addWidget(base_group)

        # Dimensions group
        dims_group = QGroupBox("Dimensions")
        dims_layout = QFormLayout(dims_group)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 1e6)
        self.height_spin.setDecimals(1)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setValue(3000)  # Default 3m
        dims_layout.addRow("Height:", self.height_spin)

        layout.addWidget(dims_group)

        # Properties group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout(props_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional column name/mark")
        props_layout.addRow("Name:", self.name_edit)

        self.profile_combo = QComboBox()
        props_layout.addRow("Profile:", self.profile_combo)

        self.material_combo = QComboBox()
        props_layout.addRow("Material:", self.material_combo)

        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSuffix(" deg")
        props_layout.addRow("Rotation:", self.rotation_spin)

        layout.addWidget(props_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_combos(self):
        """Populate profile and material combo boxes."""
        # Profiles - prefer UC for columns
        catalog = ProfileCatalog.get_instance()
        profile_names = catalog.get_profile_names()
        self.profile_combo.addItems(sorted(profile_names))

        # Set default (UC for columns)
        default_profile = "UC 203x203x46"
        idx = self.profile_combo.findText(default_profile)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)

        # Materials
        mat_catalog = MaterialCatalog.get_instance()
        material_names = mat_catalog.get_material_names()
        self.material_combo.addItems(sorted(material_names))

        default_material = "S355"
        idx = self.material_combo.findText(default_material)
        if idx >= 0:
            self.material_combo.setCurrentIndex(idx)

    def _load_column_data(self, column: Column):
        """Load existing column data into dialog."""
        self.base_x.setValue(column.base_point.x)
        self.base_y.setValue(column.base_point.y)
        self.base_z.setValue(column.base_point.z)

        self.height_spin.setValue(column.height)
        self.name_edit.setText(column.name)
        self.rotation_spin.setValue(column.rotation)

        if column.profile:
            idx = self.profile_combo.findText(column.profile.name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

        if column.material:
            idx = self.material_combo.findText(column.material.name)
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)

    def _on_accept(self):
        """Handle dialog acceptance."""
        base = Point3D(
            self.base_x.value(),
            self.base_y.value(),
            self.base_z.value()
        )

        height = self.height_spin.value()

        # Validate
        if height < 1:
            logger.warning("Column height too short")
            return

        profile = Profile.from_name(self.profile_combo.currentText())
        material = Material.from_name(self.material_combo.currentText())

        self.result_column = Column(
            base_point=base,
            height=height,
            profile=profile,
            material=material,
            rotation=self.rotation_spin.value(),
            name=self.name_edit.text()
        )

        self.accept()

    def get_column(self) -> Optional[Column]:
        """Get the created/edited column."""
        return self.result_column
