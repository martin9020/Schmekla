"""
Plate creation dialog for Schmekla.
"""

from typing import Optional, List
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QGroupBox, QDialogButtonBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt

from src.core.plate import Plate
from src.core.material import Material, MaterialCatalog
from src.geometry.point import Point3D


class PlateDialog(QDialog):
    """Dialog for creating or editing a plate."""

    def __init__(self, parent=None, plate: Optional[Plate] = None):
        """
        Initialize plate dialog.

        Args:
            parent: Parent widget
            plate: Existing plate to edit (None for new plate)
        """
        super().__init__(parent)
        self.plate = plate
        self.result_plate: Optional[Plate] = None

        self.setWindowTitle("Create Plate" if plate is None else "Edit Plate")
        self.setMinimumWidth(450)

        self._setup_ui()
        self._populate_combos()

        if plate:
            self._load_plate_data(plate)

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Origin point group
        origin_group = QGroupBox("Origin Point")
        origin_layout = QFormLayout(origin_group)

        self.origin_x = QDoubleSpinBox()
        self.origin_x.setRange(-1e9, 1e9)
        self.origin_x.setDecimals(1)
        self.origin_x.setSuffix(" mm")
        origin_layout.addRow("X:", self.origin_x)

        self.origin_y = QDoubleSpinBox()
        self.origin_y.setRange(-1e9, 1e9)
        self.origin_y.setDecimals(1)
        self.origin_y.setSuffix(" mm")
        origin_layout.addRow("Y:", self.origin_y)

        self.origin_z = QDoubleSpinBox()
        self.origin_z.setRange(-1e9, 1e9)
        self.origin_z.setDecimals(1)
        self.origin_z.setSuffix(" mm")
        origin_layout.addRow("Z:", self.origin_z)

        layout.addWidget(origin_group)

        # Dimensions group
        dims_group = QGroupBox("Dimensions")
        dims_layout = QFormLayout(dims_group)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1e6)
        self.width_spin.setDecimals(1)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setValue(300)  # Default 300mm
        dims_layout.addRow("Width (X):", self.width_spin)

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(1, 1e6)
        self.length_spin.setDecimals(1)
        self.length_spin.setSuffix(" mm")
        self.length_spin.setValue(300)  # Default 300mm
        dims_layout.addRow("Length (Y):", self.length_spin)

        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(1, 1000)
        self.thickness_spin.setDecimals(1)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setValue(20)  # Default 20mm
        dims_layout.addRow("Thickness:", self.thickness_spin)

        layout.addWidget(dims_group)

        # Properties group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout(props_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional plate name/mark")
        props_layout.addRow("Name:", self.name_edit)

        self.material_combo = QComboBox()
        props_layout.addRow("Material:", self.material_combo)

        layout.addWidget(props_group)

        # Area display
        self.area_label = QLabel("Area: 0 mm2")
        layout.addWidget(self.area_label)

        # Connect signals
        self.width_spin.valueChanged.connect(self._update_area)
        self.length_spin.valueChanged.connect(self._update_area)
        self._update_area()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_combos(self):
        """Populate material combo box."""
        mat_catalog = MaterialCatalog.get_instance()
        material_names = mat_catalog.get_material_names()
        self.material_combo.addItems(sorted(material_names))

        default_material = "S355"
        idx = self.material_combo.findText(default_material)
        if idx >= 0:
            self.material_combo.setCurrentIndex(idx)

    def _load_plate_data(self, plate: Plate):
        """Load existing plate data into dialog."""
        if plate.points:
            # Get bounding box
            min_x = min(p.x for p in plate.points)
            max_x = max(p.x for p in plate.points)
            min_y = min(p.y for p in plate.points)
            max_y = max(p.y for p in plate.points)

            self.origin_x.setValue(min_x)
            self.origin_y.setValue(min_y)
            self.origin_z.setValue(plate.points[0].z)

            self.width_spin.setValue(max_x - min_x)
            self.length_spin.setValue(max_y - min_y)

        self.thickness_spin.setValue(plate.thickness)
        self.name_edit.setText(plate.name)

        if plate.material:
            idx = self.material_combo.findText(plate.material.name)
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)

    def _update_area(self):
        """Update area display."""
        area = self.width_spin.value() * self.length_spin.value()
        self.area_label.setText(f"Area: {area:.1f} mm2")

    def _on_accept(self):
        """Handle dialog acceptance."""
        origin = Point3D(
            self.origin_x.value(),
            self.origin_y.value(),
            self.origin_z.value()
        )

        width = self.width_spin.value()
        length = self.length_spin.value()
        thickness = self.thickness_spin.value()

        # Validate
        if width < 1 or length < 1:
            logger.warning("Plate dimensions too small")
            return

        material = Material.from_name(self.material_combo.currentText())

        self.result_plate = Plate.create_rectangular(
            origin=origin,
            width=width,
            length=length,
            thickness=thickness,
            material=material,
            name=self.name_edit.text()
        )

        self.accept()

    def get_plate(self) -> Optional[Plate]:
        """Get the created/edited plate."""
        return self.result_plate
