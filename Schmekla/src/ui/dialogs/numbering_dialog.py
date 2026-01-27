"""
Numbering settings dialog for Schmekla.

Provides Tekla-style numbering configuration with table-based UI
for configuring prefix, start number, and step per element type.
"""

import re
from typing import Optional, Dict, Any
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QGroupBox, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView,
    QMessageBox, QWidget, QCheckBox
)
from PySide6.QtCore import Qt

from src.core.numbering import NumberingManager, NumberingSeries, ComparisonConfig
from src.core.element import ElementType


# Dialog dimension constants
DIALOG_MIN_WIDTH = 600
DIALOG_MIN_HEIGHT = 500
PREVIEW_TABLE_MAX_HEIGHT = 200


class NumberingDialog(QDialog):
    """Dialog for configuring element numbering series.

    Provides a table-based UI for configuring:
    - Element type prefix (e.g., "B" for beams)
    - Start number for series
    - End number (optional)
    - Step value for incrementing

    Also includes preview of next numbers and controls for
    renumbering all elements or resetting to defaults.
    """

    def __init__(self, numbering_manager: NumberingManager, parent=None):
        """
        Initialize numbering dialog.

        Args:
            numbering_manager: NumberingManager instance to configure
            parent: Parent widget
        """
        super().__init__(parent)
        self.numbering_manager = numbering_manager

        # Store original config for reset
        self._default_config = self._get_default_config()

        self.setWindowTitle("Numbering Settings")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)
        self.setMinimumHeight(DIALOG_MIN_HEIGHT)

        self._setup_ui()
        self._populate_table()

    def _get_default_config(self) -> Dict[str, Dict]:
        """Get default numbering configuration."""
        return {
            ElementType.BEAM.value: {'prefix': 'B', 'start_number': 1, 'step': 1},
            ElementType.COLUMN.value: {'prefix': 'C', 'start_number': 1, 'step': 1},
            ElementType.PLATE.value: {'prefix': 'PL', 'start_number': 1, 'step': 1},
            ElementType.SLAB.value: {'prefix': 'S', 'start_number': 1, 'step': 1},
            ElementType.WALL.value: {'prefix': 'W', 'start_number': 1, 'step': 1},
            ElementType.FOOTING.value: {'prefix': 'F', 'start_number': 1, 'step': 1},
            ElementType.BRACE.value: {'prefix': 'BR', 'start_number': 1, 'step': 1},
            ElementType.PURLIN.value: {'prefix': 'P', 'start_number': 1, 'step': 1},
            ElementType.GIRT.value: {'prefix': 'G', 'start_number': 1, 'step': 1},
        }

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Comparison properties group (Tekla-style identical parts)
        comparison_group = QGroupBox("Identical Parts Comparison")
        comparison_layout = QVBoxLayout(comparison_group)

        # Description label
        desc_label = QLabel(
            "Parts with matching properties will receive the same part number.\n"
            "For example, 5 identical beams all get 'B1'."
        )
        desc_label.setWordWrap(True)
        comparison_layout.addWidget(desc_label)

        # Checkboxes for comparison properties
        checkbox_layout = QHBoxLayout()

        self.compare_profile_cb = QCheckBox("Profile")
        self.compare_profile_cb.setToolTip("Compare section profile (e.g., UB 305x165x40)")
        self.compare_profile_cb.setChecked(True)
        checkbox_layout.addWidget(self.compare_profile_cb)

        self.compare_material_cb = QCheckBox("Material")
        self.compare_material_cb.setToolTip("Compare material (e.g., S355)")
        self.compare_material_cb.setChecked(True)
        checkbox_layout.addWidget(self.compare_material_cb)

        self.compare_name_cb = QCheckBox("Name")
        self.compare_name_cb.setToolTip("Compare element name/mark")
        self.compare_name_cb.setChecked(False)
        checkbox_layout.addWidget(self.compare_name_cb)

        self.compare_geometry_cb = QCheckBox("Geometry")
        self.compare_geometry_cb.setToolTip("Compare geometry (length, height, dimensions)")
        self.compare_geometry_cb.setChecked(True)
        checkbox_layout.addWidget(self.compare_geometry_cb)

        self.compare_rotation_cb = QCheckBox("Rotation")
        self.compare_rotation_cb.setToolTip("Compare rotation angle")
        self.compare_rotation_cb.setChecked(True)
        checkbox_layout.addWidget(self.compare_rotation_cb)

        comparison_layout.addLayout(checkbox_layout)

        # Tolerance setting
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("Geometry Tolerance:")
        tolerance_layout.addWidget(tolerance_label)

        self.tolerance_spinbox = QDoubleSpinBox()
        self.tolerance_spinbox.setRange(0.1, 100.0)
        self.tolerance_spinbox.setValue(1.0)
        self.tolerance_spinbox.setSuffix(" mm")
        self.tolerance_spinbox.setDecimals(1)
        self.tolerance_spinbox.setToolTip("Parts within this tolerance are considered identical")
        tolerance_layout.addWidget(self.tolerance_spinbox)

        tolerance_layout.addStretch()
        comparison_layout.addLayout(tolerance_layout)

        layout.addWidget(comparison_group)

        # Series configuration group
        config_group = QGroupBox("Numbering Series Configuration")
        config_layout = QVBoxLayout(config_group)

        # Configuration table
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels([
            "Element Type", "Prefix", "Start Number", "End Number", "Step"
        ])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.config_table.setAlternatingRowColors(True)
        config_layout.addWidget(self.config_table)

        layout.addWidget(config_group)

        # Preview group
        preview_group = QGroupBox("Preview - Next Numbers")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels([
            "Element Type", "Current Count", "Next Number"
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMaximumHeight(PREVIEW_TABLE_MAX_HEIGHT)
        preview_layout.addWidget(self.preview_table)

        # Refresh preview button
        refresh_btn = QPushButton("Refresh Preview")
        refresh_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(refresh_btn)

        layout.addWidget(preview_group)

        # Action buttons group
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)

        self.renumber_btn = QPushButton("Renumber All")
        self.renumber_btn.setToolTip("Renumber all elements in the model using current settings")
        self.renumber_btn.clicked.connect(self._on_renumber_all)
        action_layout.addWidget(self.renumber_btn)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setToolTip("Reset all numbering series to default values")
        self.reset_btn.clicked.connect(self._on_reset_defaults)
        action_layout.addWidget(self.reset_btn)

        self.reset_counters_btn = QPushButton("Reset Counters")
        self.reset_counters_btn.setToolTip("Reset all counters to zero without changing configuration")
        self.reset_counters_btn.clicked.connect(self._on_reset_counters)
        action_layout.addWidget(self.reset_counters_btn)

        action_layout.addStretch()
        layout.addWidget(action_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._on_apply)
        layout.addWidget(button_box)

    def _load_comparison_config(self):
        """Load comparison config from numbering manager into UI."""
        config = self.numbering_manager.get_comparison_config()
        self.compare_profile_cb.setChecked(config.compare_profile)
        self.compare_material_cb.setChecked(config.compare_material)
        self.compare_name_cb.setChecked(config.compare_name)
        self.compare_geometry_cb.setChecked(config.compare_geometry)
        self.compare_rotation_cb.setChecked(config.compare_rotation)
        self.tolerance_spinbox.setValue(config.geometry_tolerance)

    def _apply_comparison_config(self):
        """Apply comparison config from UI to numbering manager."""
        config = ComparisonConfig(
            compare_profile=self.compare_profile_cb.isChecked(),
            compare_material=self.compare_material_cb.isChecked(),
            compare_name=self.compare_name_cb.isChecked(),
            compare_geometry=self.compare_geometry_cb.isChecked(),
            compare_rotation=self.compare_rotation_cb.isChecked(),
            geometry_tolerance=self.tolerance_spinbox.value(),
        )
        self.numbering_manager.set_comparison_config(config)
        logger.info("Comparison config applied")

    def _populate_table(self):
        """Populate configuration table with current settings."""
        # Load comparison config first
        self._load_comparison_config()

        current_config = self.numbering_manager.get_all_series_config()

        # Combine with defaults for any missing types
        all_types = list(ElementType)
        self.config_table.setRowCount(len(all_types))

        for row, elem_type in enumerate(all_types):
            type_name = elem_type.value

            # Get current config or default
            if type_name in current_config:
                config = current_config[type_name]
            else:
                config = self._default_config.get(type_name, {
                    'prefix': 'E', 'start_number': 1, 'step': 1
                })

            # Element Type (read-only)
            type_item = QTableWidgetItem(type_name.upper())
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            type_item.setData(Qt.UserRole, elem_type)
            self.config_table.setItem(row, 0, type_item)

            # Prefix (editable)
            prefix_item = QTableWidgetItem(config.get('prefix', 'E'))
            self.config_table.setItem(row, 1, prefix_item)

            # Start Number (editable)
            start_item = QTableWidgetItem(str(config.get('start_number', 1)))
            self.config_table.setItem(row, 2, start_item)

            # End Number (optional, editable)
            end_item = QTableWidgetItem("")  # Empty means no limit
            self.config_table.setItem(row, 3, end_item)

            # Step (editable)
            step_item = QTableWidgetItem(str(config.get('step', 1)))
            self.config_table.setItem(row, 4, step_item)

        self._update_preview()

    def _update_preview(self):
        """Update the preview table with next numbers."""
        current_config = self.numbering_manager.get_all_series_config()
        all_types = list(ElementType)

        self.preview_table.setRowCount(len(all_types))

        for row, elem_type in enumerate(all_types):
            type_name = elem_type.value

            # Element Type
            type_item = QTableWidgetItem(type_name.upper())
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.preview_table.setItem(row, 0, type_item)

            # Current Count
            if type_name in current_config:
                count = current_config[type_name].get('current_counter', 0)
                next_num = current_config[type_name].get('next_number', 'N/A')
            else:
                count = 0
                next_num = 'N/A'

            count_item = QTableWidgetItem(str(count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
            self.preview_table.setItem(row, 1, count_item)

            # Next Number
            next_item = QTableWidgetItem(next_num)
            next_item.setFlags(next_item.flags() & ~Qt.ItemIsEditable)
            self.preview_table.setItem(row, 2, next_item)

    def _get_table_config(self) -> Dict[str, Dict]:
        """Get configuration from table."""
        config = {}
        # Regex pattern for valid prefix: alphanumeric, hyphen, underscore only
        prefix_pattern = re.compile(r'^[A-Za-z0-9_-]+$')

        for row in range(self.config_table.rowCount()):
            type_item = self.config_table.item(row, 0)
            prefix_item = self.config_table.item(row, 1)
            start_item = self.config_table.item(row, 2)
            step_item = self.config_table.item(row, 4)

            if type_item and prefix_item and start_item:
                type_name = type_item.text().lower()
                prefix = prefix_item.text().strip() if prefix_item.text() else ''

                # Validate prefix: 1-20 characters, alphanumeric/hyphen/underscore only
                if not prefix or len(prefix) < 1 or len(prefix) > 20 or not prefix_pattern.match(prefix):
                    logger.warning(
                        f"Invalid prefix '{prefix}' for element type '{type_name}': "
                        "must be 1-20 characters, alphanumeric/hyphen/underscore only. Using 'E' as fallback."
                    )
                    prefix = 'E'

                try:
                    start_number = int(start_item.text())
                except ValueError:
                    start_number = 1

                # Read step value from column 4
                step = 1
                if step_item and step_item.text():
                    try:
                        step = int(step_item.text())
                        if step < 1:
                            step = 1
                    except ValueError:
                        step = 1

                config[type_name] = {
                    'prefix': prefix,
                    'start_number': start_number,
                    'step': step
                }

        return config

    def _apply_config(self):
        """Apply configuration from table and comparison settings to numbering manager."""
        # Apply series configuration
        config = self._get_table_config()
        self.numbering_manager.set_series_from_config(config)

        # Apply comparison configuration
        self._apply_comparison_config()

        self._update_preview()
        logger.info("Numbering configuration applied (series + comparison)")

    def _on_apply(self):
        """Handle Apply button click."""
        self._apply_config()

    def _on_accept(self):
        """Handle dialog acceptance."""
        self._apply_config()
        self.accept()

    def _on_renumber_all(self):
        """Handle Renumber All button click with preview."""
        # Get parent window to access model
        parent = self.parent()
        if not hasattr(parent, 'model'):
            QMessageBox.warning(
                self,
                "Error",
                "Could not access model for renumbering."
            )
            return

        model = parent.model
        elements = model.get_all_elements()

        if not elements:
            QMessageBox.information(
                self,
                "No Elements",
                "There are no elements in the model to renumber."
            )
            return

        # Apply current config first (to get correct comparison settings)
        self._apply_config()

        # Generate preview
        preview = self.numbering_manager.preview_renumber(elements)

        # Build preview summary
        # Count unique numbers to show identical parts detection
        number_counts = {}
        for part_number in preview.values():
            number_counts[part_number] = number_counts.get(part_number, 0) + 1

        # Count how many are identical (count > 1)
        identical_groups = sum(1 for count in number_counts.values() if count > 1)
        identical_parts = sum(count for count in number_counts.values() if count > 1)

        preview_text = (
            f"Preview of renumbering:\n\n"
            f"Total elements: {len(elements)}\n"
            f"Unique part numbers: {len(number_counts)}\n"
        )

        if identical_groups > 0:
            preview_text += (
                f"\nIdentical parts detected:\n"
                f"  - {identical_groups} groups of identical parts\n"
                f"  - {identical_parts} elements share numbers with others\n"
            )
        else:
            preview_text += "\nNo identical parts detected (all unique).\n"

        preview_text += "\nDo you want to apply this renumbering?"

        result = QMessageBox.question(
            self,
            "Confirm Renumber",
            preview_text,
            QMessageBox.Yes | QMessageBox.No
        )

        if result == QMessageBox.Yes:
            self._execute_renumber(model, elements, number_counts)

            self._update_preview()

    def _execute_renumber(self, model, elements, number_counts):
        """Execute renumbering with undo support.

        Args:
            model: The structural model
            elements: List of elements to renumber
            number_counts: Dictionary of part number counts for summary
        """
        from src.core.commands.numbering_commands import RenumberCommand

        # Create command and capture before state
        cmd = RenumberCommand(model, "Renumber All Elements")
        cmd.capture_before_state()

        # Reset counters and renumber with identical parts detection
        self.numbering_manager.reset()

        for element in elements:
            new_number = self.numbering_manager.get_number_for_element(element)
            element.part_number = new_number
            logger.debug(f"Renumbered {element.id} to {new_number}")

        # Capture after state and execute via model (pushes to undo stack)
        cmd.capture_after_state()
        model.execute_command(cmd)

        QMessageBox.information(
            self,
            "Renumbering Complete",
            f"Renumbered {len(elements)} elements.\n"
            f"Unique part numbers: {len(number_counts)}"
        )

    def _on_reset_defaults(self):
        """Handle Reset to Defaults button click."""
        result = QMessageBox.question(
            self,
            "Confirm Reset",
            "Reset all numbering series to default values?\n\n"
            "This will not change existing part numbers.",
            QMessageBox.Yes | QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # Reset to defaults
            for type_name, config in self._default_config.items():
                try:
                    elem_type = ElementType(type_name)
                    self.numbering_manager.configure_series(
                        elem_type,
                        prefix=config['prefix'],
                        start_number=config['start_number']
                    )
                except ValueError as e:
                    logger.warning(f"Invalid element type '{type_name}' in default config: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error resetting defaults for '{type_name}': {e}")

            # Repopulate table
            self._populate_table()
            logger.info("Numbering series reset to defaults")

    def _on_reset_counters(self):
        """Handle Reset Counters button click."""
        result = QMessageBox.question(
            self,
            "Confirm Reset Counters",
            "Reset all numbering counters to zero?\n\n"
            "This will affect new element numbers but not existing ones.",
            QMessageBox.Yes | QMessageBox.No
        )

        if result == QMessageBox.Yes:
            self.numbering_manager.reset()
            self._update_preview()
            logger.info("Numbering counters reset")
