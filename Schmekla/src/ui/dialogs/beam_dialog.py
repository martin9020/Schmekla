"""
Beam creation dialog for Schmekla.
"""

from typing import Optional
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QGroupBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

from src.core.beam import Beam
from src.core.profile import Profile, ProfileCatalog
from src.core.material import Material, MaterialCatalog
from src.geometry.point import Point3D


class BeamDialog(QDialog):
    """Dialog for creating or editing a beam."""

    def __init__(self, parent=None, beam: Optional[Beam] = None):
        """
        Initialize beam dialog.

        Args:
            parent: Parent widget
            beam: Existing beam to edit (None for new beam)
        """
        super().__init__(parent)
        self.beam = beam
        self.result_beam: Optional[Beam] = None

        self.setWindowTitle("Create Beam" if beam is None else "Edit Beam")
        self.setMinimumWidth(400)

        self._setup_ui()
        self._populate_combos()

        if beam:
            self._load_beam_data(beam)

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Start point group
        start_group = QGroupBox("Start Point")
        start_layout = QFormLayout(start_group)

        self.start_x = QDoubleSpinBox()
        self.start_x.setRange(-1e9, 1e9)
        self.start_x.setDecimals(1)
        self.start_x.setSuffix(" mm")
        start_layout.addRow("X:", self.start_x)

        self.start_y = QDoubleSpinBox()
        self.start_y.setRange(-1e9, 1e9)
        self.start_y.setDecimals(1)
        self.start_y.setSuffix(" mm")
        start_layout.addRow("Y:", self.start_y)

        self.start_z = QDoubleSpinBox()
        self.start_z.setRange(-1e9, 1e9)
        self.start_z.setDecimals(1)
        self.start_z.setSuffix(" mm")
        start_layout.addRow("Z:", self.start_z)

        layout.addWidget(start_group)

        # End point group
        end_group = QGroupBox("End Point")
        end_layout = QFormLayout(end_group)

        self.end_x = QDoubleSpinBox()
        self.end_x.setRange(-1e9, 1e9)
        self.end_x.setDecimals(1)
        self.end_x.setSuffix(" mm")
        self.end_x.setValue(6000)  # Default 6m
        end_layout.addRow("X:", self.end_x)

        self.end_y = QDoubleSpinBox()
        self.end_y.setRange(-1e9, 1e9)
        self.end_y.setDecimals(1)
        self.end_y.setSuffix(" mm")
        end_layout.addRow("Y:", self.end_y)

        self.end_z = QDoubleSpinBox()
        self.end_z.setRange(-1e9, 1e9)
        self.end_z.setDecimals(1)
        self.end_z.setSuffix(" mm")
        end_layout.addRow("Z:", self.end_z)

        layout.addWidget(end_group)

        # Properties group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout(props_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional beam name/mark")
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

        # Length display
        self.length_label = QLabel("Length: 0 mm")
        layout.addWidget(self.length_label)

        # Connect signals to update length
        for spin in [self.start_x, self.start_y, self.start_z,
                     self.end_x, self.end_y, self.end_z]:
            spin.valueChanged.connect(self._update_length)

        self._update_length()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_combos(self):
        """Populate profile and material combo boxes."""
        # Profiles
        catalog = ProfileCatalog.get_instance()
        profile_names = catalog.get_profile_names()
        self.profile_combo.addItems(sorted(profile_names))

        # Set default
        default_profile = "UB 305x165x40"
        idx = self.profile_combo.findText(default_profile)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)

        # Materials
        mat_catalog = MaterialCatalog.get_instance()
        material_names = mat_catalog.get_material_names()
        self.material_combo.addItems(sorted(material_names))

        # Set default
        default_material = "S355"
        idx = self.material_combo.findText(default_material)
        if idx >= 0:
            self.material_combo.setCurrentIndex(idx)

    def _load_beam_data(self, beam: Beam):
        """Load existing beam data into dialog."""
        self.start_x.setValue(beam.start_point.x)
        self.start_y.setValue(beam.start_point.y)
        self.start_z.setValue(beam.start_point.z)

        self.end_x.setValue(beam.end_point.x)
        self.end_y.setValue(beam.end_point.y)
        self.end_z.setValue(beam.end_point.z)

        self.name_edit.setText(beam.name)
        self.rotation_spin.setValue(beam.rotation)

        if beam.profile:
            idx = self.profile_combo.findText(beam.profile.name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

        if beam.material:
            idx = self.material_combo.findText(beam.material.name)
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)

    def _update_length(self):
        """Update length display."""
        start = Point3D(
            self.start_x.value(),
            self.start_y.value(),
            self.start_z.value()
        )
        end = Point3D(
            self.end_x.value(),
            self.end_y.value(),
            self.end_z.value()
        )
        length = start.distance_to(end)
        self.length_label.setText(f"Length: {length:.1f} mm")

    def _on_accept(self):
        """Handle dialog acceptance."""
        start = Point3D(
            self.start_x.value(),
            self.start_y.value(),
            self.start_z.value()
        )
        end = Point3D(
            self.end_x.value(),
            self.end_y.value(),
            self.end_z.value()
        )

        # Validate
        if start.distance_to(end) < 1:
            logger.warning("Beam length too short")
            return

        profile = Profile.from_name(self.profile_combo.currentText())
        material = Material.from_name(self.material_combo.currentText())

        self.result_beam = Beam(
            start_point=start,
            end_point=end,
            profile=profile,
            material=material,
            rotation=self.rotation_spin.value(),
            name=self.name_edit.text()
        )

        self.accept()

    def get_beam(self) -> Optional[Beam]:
        """Get the created/edited beam."""
        return self.result_beam
