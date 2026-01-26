"""
Grid creation dialog for Schmekla.
"""

from typing import Optional, List
from loguru import logger

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
    QGroupBox, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt


class GridDialog(QDialog):
    """Dialog for creating structural grids."""

    def __init__(self, parent=None):
        """
        Initialize grid dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.result_grids = None

        self.setWindowTitle("Create Grid")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # X Grids group
        x_group = QGroupBox("X Direction Grids (Vertical Lines)")
        x_layout = QVBoxLayout(x_group)

        # X grid table
        self.x_table = QTableWidget(5, 2)
        self.x_table.setHorizontalHeaderLabels(["Name", "Position (mm)"])
        self.x_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._populate_default_grids(self.x_table, ["A", "B", "C", "D", "E"], 6000)
        x_layout.addWidget(self.x_table)

        # X grid buttons
        x_btn_layout = QHBoxLayout()
        add_x_btn = QPushButton("Add Row")
        add_x_btn.clicked.connect(lambda: self._add_row(self.x_table))
        x_btn_layout.addWidget(add_x_btn)
        remove_x_btn = QPushButton("Remove Row")
        remove_x_btn.clicked.connect(lambda: self._remove_row(self.x_table))
        x_btn_layout.addWidget(remove_x_btn)
        x_btn_layout.addStretch()
        x_layout.addLayout(x_btn_layout)

        layout.addWidget(x_group)

        # Y Grids group
        y_group = QGroupBox("Y Direction Grids (Horizontal Lines)")
        y_layout = QVBoxLayout(y_group)

        # Y grid table
        self.y_table = QTableWidget(4, 2)
        self.y_table.setHorizontalHeaderLabels(["Name", "Position (mm)"])
        self.y_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._populate_default_grids(self.y_table, ["1", "2", "3", "4"], 6000)
        y_layout.addWidget(self.y_table)

        # Y grid buttons
        y_btn_layout = QHBoxLayout()
        add_y_btn = QPushButton("Add Row")
        add_y_btn.clicked.connect(lambda: self._add_row(self.y_table))
        y_btn_layout.addWidget(add_y_btn)
        remove_y_btn = QPushButton("Remove Row")
        remove_y_btn.clicked.connect(lambda: self._remove_row(self.y_table))
        y_btn_layout.addWidget(remove_y_btn)
        y_btn_layout.addStretch()
        y_layout.addLayout(y_btn_layout)

        layout.addWidget(y_group)

        # Quick fill section
        quick_group = QGroupBox("Quick Fill")
        quick_layout = QFormLayout(quick_group)

        self.x_count = QSpinBox()
        self.x_count.setRange(2, 50)
        self.x_count.setValue(5)
        quick_layout.addRow("X Grid Count:", self.x_count)

        self.x_spacing = QDoubleSpinBox()
        self.x_spacing.setRange(100, 100000)
        self.x_spacing.setValue(6000)
        self.x_spacing.setSuffix(" mm")
        quick_layout.addRow("X Spacing:", self.x_spacing)

        self.y_count = QSpinBox()
        self.y_count.setRange(2, 50)
        self.y_count.setValue(4)
        quick_layout.addRow("Y Grid Count:", self.y_count)

        self.y_spacing = QDoubleSpinBox()
        self.y_spacing.setRange(100, 100000)
        self.y_spacing.setValue(6000)
        self.y_spacing.setSuffix(" mm")
        quick_layout.addRow("Y Spacing:", self.y_spacing)

        quick_fill_btn = QPushButton("Generate Grids")
        quick_fill_btn.clicked.connect(self._quick_fill)
        quick_layout.addRow(quick_fill_btn)

        layout.addWidget(quick_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_default_grids(self, table: QTableWidget, names: List[str], spacing: float):
        """Populate table with default grid values."""
        table.setRowCount(len(names))
        for i, name in enumerate(names):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(str(i * spacing)))

    def _add_row(self, table: QTableWidget):
        """Add row to table."""
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(""))
        table.setItem(row, 1, QTableWidgetItem("0"))

    def _remove_row(self, table: QTableWidget):
        """Remove selected row from table."""
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    def _quick_fill(self):
        """Generate grids based on quick fill values."""
        # Generate X grids (A, B, C, ...)
        x_count = self.x_count.value()
        x_spacing = self.x_spacing.value()

        self.x_table.setRowCount(x_count)
        for i in range(x_count):
            name = chr(ord('A') + i) if i < 26 else f"A{i - 25}"
            self.x_table.setItem(i, 0, QTableWidgetItem(name))
            self.x_table.setItem(i, 1, QTableWidgetItem(str(i * x_spacing)))

        # Generate Y grids (1, 2, 3, ...)
        y_count = self.y_count.value()
        y_spacing = self.y_spacing.value()

        self.y_table.setRowCount(y_count)
        for i in range(y_count):
            name = str(i + 1)
            self.y_table.setItem(i, 0, QTableWidgetItem(name))
            self.y_table.setItem(i, 1, QTableWidgetItem(str(i * y_spacing)))

    def _on_accept(self):
        """Handle dialog acceptance."""
        x_grids = []
        for i in range(self.x_table.rowCount()):
            name_item = self.x_table.item(i, 0)
            pos_item = self.x_table.item(i, 1)
            if name_item and pos_item:
                name = name_item.text()
                try:
                    position = float(pos_item.text())
                    x_grids.append({"name": name, "position": position, "direction": "X"})
                except ValueError:
                    pass

        y_grids = []
        for i in range(self.y_table.rowCount()):
            name_item = self.y_table.item(i, 0)
            pos_item = self.y_table.item(i, 1)
            if name_item and pos_item:
                name = name_item.text()
                try:
                    position = float(pos_item.text())
                    y_grids.append({"name": name, "position": position, "direction": "Y"})
                except ValueError:
                    pass

        self.result_grids = {"x_grids": x_grids, "y_grids": y_grids}
        self.accept()

    def get_grids(self):
        """Get the created grids."""
        return self.result_grids
