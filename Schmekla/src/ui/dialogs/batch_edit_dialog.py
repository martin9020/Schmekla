"""Batch edit dialog for changing properties of multiple elements."""
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QPushButton, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from loguru import logger

from src.core.element import StructuralElement
from src.core.profile import ProfileCatalog
from src.core.material import MaterialCatalog


class BatchEditDialog(QDialog):
    """Dialog for batch editing properties of multiple elements."""

    def __init__(self, elements: List[StructuralElement], parent=None):
        super().__init__(parent)
        self.elements = elements
        self.setWindowTitle(f"Batch Edit - {len(elements)} Elements")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Editing {len(self.elements)} selected elements")
        header.setStyleSheet("font-weight: bold; font-size: 12px; color: #0078d4;")
        layout.addWidget(header)

        # Profile group
        profile_group = QGroupBox("Profile")
        profile_layout = QHBoxLayout(profile_group)

        self.change_profile_cb = QCheckBox("Change Profile:")
        self.change_profile_cb.stateChanged.connect(self._on_profile_checkbox_changed)
        profile_layout.addWidget(self.change_profile_cb)

        self.profile_combo = QComboBox()
        self.profile_combo.setEnabled(False)
        self._populate_profiles()
        profile_layout.addWidget(self.profile_combo, 1)

        layout.addWidget(profile_group)

        # Material group
        material_group = QGroupBox("Material")
        material_layout = QHBoxLayout(material_group)

        self.change_material_cb = QCheckBox("Change Material:")
        self.change_material_cb.stateChanged.connect(self._on_material_checkbox_changed)
        material_layout.addWidget(self.change_material_cb)

        self.material_combo = QComboBox()
        self.material_combo.setEnabled(False)
        self._populate_materials()
        material_layout.addWidget(self.material_combo, 1)

        layout.addWidget(material_group)

        # Phase group
        phase_group = QGroupBox("Phase")
        phase_layout = QHBoxLayout(phase_group)

        self.change_phase_cb = QCheckBox("Change Phase:")
        self.change_phase_cb.stateChanged.connect(self._on_phase_checkbox_changed)
        phase_layout.addWidget(self.change_phase_cb)

        self.phase_combo = QComboBox()
        self.phase_combo.setEnabled(False)
        self.phase_combo.addItems(["1", "2", "3", "4", "5"])
        phase_layout.addWidget(self.phase_combo, 1)

        layout.addWidget(phase_group)

        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.summary_label)
        self._update_summary()

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #106ebe; }
            QPushButton:disabled { background: #555; }
        """)
        button_layout.addWidget(self.apply_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _populate_profiles(self):
        """Populate profile combo from catalog."""
        try:
            catalog = ProfileCatalog.get_instance()
            profiles = catalog.get_all_profiles()
            for profile in profiles:
                self.profile_combo.addItem(profile.name, profile)
        except Exception as e:
            logger.warning(f"Could not load profiles: {e}")
            self.profile_combo.addItem("UB 305x165x40")
            self.profile_combo.addItem("UB 406x178x54")
            self.profile_combo.addItem("UC 254x254x73")

    def _populate_materials(self):
        """Populate material combo from catalog."""
        try:
            catalog = MaterialCatalog.get_instance()
            materials = catalog.get_all_materials()
            for material in materials:
                self.material_combo.addItem(material.name, material)
        except Exception as e:
            logger.warning(f"Could not load materials: {e}")
            self.material_combo.addItem("S355")
            self.material_combo.addItem("S275")
            self.material_combo.addItem("C30/37")

    def _load_current_values(self):
        """Load current values from selected elements."""
        if not self.elements:
            return

        # Check if all elements have same profile
        profiles = set()
        materials = set()
        phases = set()

        for elem in self.elements:
            if hasattr(elem, '_profile') and elem._profile:
                profiles.add(elem._profile.name)
            if hasattr(elem, '_material') and elem._material:
                materials.add(elem._material.name)
            if hasattr(elem, 'phase'):
                phases.add(str(elem.phase))

        # Set combo to current value if all same
        if len(profiles) == 1:
            idx = self.profile_combo.findText(list(profiles)[0])
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

        if len(materials) == 1:
            idx = self.material_combo.findText(list(materials)[0])
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)

        if len(phases) == 1:
            idx = self.phase_combo.findText(list(phases)[0])
            if idx >= 0:
                self.phase_combo.setCurrentIndex(idx)

    def _on_profile_checkbox_changed(self, state):
        self.profile_combo.setEnabled(state == Qt.Checked)
        self._update_summary()

    def _on_material_checkbox_changed(self, state):
        self.material_combo.setEnabled(state == Qt.Checked)
        self._update_summary()

    def _on_phase_checkbox_changed(self, state):
        self.phase_combo.setEnabled(state == Qt.Checked)
        self._update_summary()

    def _update_summary(self):
        """Update the summary label."""
        changes = []
        if self.change_profile_cb.isChecked():
            changes.append(f"Profile -> {self.profile_combo.currentText()}")
        if self.change_material_cb.isChecked():
            changes.append(f"Material -> {self.material_combo.currentText()}")
        if self.change_phase_cb.isChecked():
            changes.append(f"Phase -> {self.phase_combo.currentText()}")

        if changes:
            self.summary_label.setText("Changes: " + ", ".join(changes))
            self.apply_btn.setEnabled(True)
        else:
            self.summary_label.setText("No changes selected")
            self.apply_btn.setEnabled(False)

    def _on_apply(self):
        """Apply the changes to all elements."""
        count = 0
        failures = []

        for elem in self.elements:
            try:
                if self.change_profile_cb.isChecked():
                    profile = self.profile_combo.currentData()
                    if profile:
                        elem.profile = profile
                    else:
                        elem.set_property("Profile", self.profile_combo.currentText())

                if self.change_material_cb.isChecked():
                    material = self.material_combo.currentData()
                    if material:
                        elem.material = material
                    else:
                        elem.set_property("Material", self.material_combo.currentText())

                if self.change_phase_cb.isChecked():
                    elem.set_property("Phase", self.phase_combo.currentText())

                count += 1
            except Exception as e:
                logger.warning(f"Could not update element {elem.id}: {e}")
                failures.append(str(elem.id)[:8])

        logger.info(f"Batch edit applied to {count}/{len(self.elements)} elements")

        if failures:
            QMessageBox.warning(
                self,
                "Batch Edit Completed With Errors",
                f"Updated {count}/{len(self.elements)} elements.\n"
                f"Failed: {len(failures)} elements"
            )
        else:
            QMessageBox.information(
                self,
                "Batch Edit Complete",
                f"Successfully updated all {count} elements."
            )

        self.accept()

    def get_changes(self) -> dict:
        """Get the changes to apply."""
        changes = {}
        if self.change_profile_cb.isChecked():
            changes['profile'] = self.profile_combo.currentText()
        if self.change_material_cb.isChecked():
            changes['material'] = self.material_combo.currentText()
        if self.change_phase_cb.isChecked():
            changes['phase'] = self.phase_combo.currentText()
        return changes
