"""
Properties panel widget for displaying element properties.

Shows selected element properties in a Tekla Structures-like format.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QScrollArea, QFrame, QGridLayout, QGroupBox,
    QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from loguru import logger


class PropertyRow(QWidget):
    """A single property row with label and value."""

    value_changed = Signal(str, str)  # property_name, new_value

    def __init__(self, name: str, value: str, editable: bool = False, parent=None):
        super().__init__(parent)
        self.property_name = name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Label (property name)
        self.label = QLabel(name + ":")
        self.label.setMinimumWidth(80)
        self.label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.label)

        # Value
        if editable:
            self.value_widget = QLineEdit(str(value))
            self.value_widget.setStyleSheet("""
                QLineEdit {
                    background: #3c3c3c;
                    border: 1px solid #555;
                    padding: 2px 4px;
                    color: white;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d4;
                }
            """)
            self.value_widget.editingFinished.connect(self._on_value_changed)
        else:
            self.value_widget = QLabel(str(value))
            self.value_widget.setStyleSheet("color: white; font-size: 11px;")
            self.value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.value_widget, 1)

    def _on_value_changed(self):
        if isinstance(self.value_widget, QLineEdit):
            self.value_changed.emit(self.property_name, self.value_widget.text())

    def set_value(self, value: str):
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(str(value))
        else:
            self.value_widget.setText(str(value))


class PropertiesPanel(QWidget):
    """
    Properties panel showing selected element properties.

    Displays properties grouped by category:
    - General (Name, Type, ID)
    - Section (Profile)
    - Material
    - Geometry (dimensions, positions)
    - Attributes (Phase, Class)
    """

    property_changed = Signal(str, str, str)  # element_id, property_name, new_value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_element_id: Optional[str] = None
        self._property_rows: Dict[str, PropertyRow] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup the panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QLabel("Properties")
        header.setStyleSheet("""
            background: #3c3c3c;
            color: white;
            font-weight: bold;
            padding: 8px;
            font-size: 12px;
        """)
        main_layout.addWidget(header)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #2b2b2b; border: none; }")

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(4)

        # Placeholder message
        self.placeholder = QLabel("Select an element\nto view properties")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #666; font-size: 12px; padding: 40px;")
        self.content_layout.addWidget(self.placeholder)

        self.content_layout.addStretch()

        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

    def clear(self):
        """Clear the properties panel."""
        self._current_element_id = None
        self._property_rows.clear()

        # Remove all widgets except placeholder
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show placeholder
        self.placeholder = QLabel("Select an element\nto view properties")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #666; font-size: 12px; padding: 40px;")
        self.content_layout.addWidget(self.placeholder)
        self.content_layout.addStretch()

    def show_element(self, element):
        """
        Display properties for an element.

        Args:
            element: StructuralElement to display
        """
        if element is None:
            self.clear()
            return

        self._current_element_id = str(element.id)
        self._property_rows.clear()

        # Clear existing content
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get properties from element
        props = element.get_properties()

        # Group properties by category
        general_props = ["Name", "Type", "ID"]
        section_props = ["Profile"]
        material_props = ["Material"]
        geometry_props = ["Length", "Height", "Start Point", "End Point", "Base Point", "Top Point", "Rotation"]
        attribute_props = ["Phase", "Class"]

        # Create groups
        self._add_property_group("General", props, general_props, editable_props=["Name"])
        self._add_property_group("Section", props, section_props)
        self._add_property_group("Material", props, material_props)
        self._add_property_group("Geometry", props, geometry_props)
        self._add_property_group("Attributes", props, attribute_props, editable_props=["Phase", "Class"])

        # Add any remaining properties
        shown_props = set(general_props + section_props + material_props + geometry_props + attribute_props)
        remaining = {k: v for k, v in props.items() if k not in shown_props}
        if remaining:
            self._add_property_group("Other", remaining, list(remaining.keys()))

        self.content_layout.addStretch()

    def _add_property_group(self, group_name: str, all_props: Dict[str, Any],
                           prop_names: List[str], editable_props: List[str] = None):
        """Add a group of properties."""
        editable_props = editable_props or []

        # Filter to properties that exist
        visible_props = [(name, all_props.get(name)) for name in prop_names if name in all_props and all_props.get(name) not in (None, "")]

        if not visible_props:
            return

        # Group box
        group = QGroupBox(group_name)
        group.setStyleSheet("""
            QGroupBox {
                color: #0078d4;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)

        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(4, 8, 4, 4)
        group_layout.setSpacing(2)

        for prop_name, prop_value in visible_props:
            editable = prop_name in editable_props
            row = PropertyRow(prop_name, str(prop_value) if prop_value is not None else "", editable)
            row.value_changed.connect(self._on_property_changed)
            self._property_rows[prop_name] = row
            group_layout.addWidget(row)

        self.content_layout.addWidget(group)

    def _on_property_changed(self, prop_name: str, new_value: str):
        """Handle property value change."""
        if self._current_element_id:
            self.property_changed.emit(self._current_element_id, prop_name, new_value)

    def show_multiple(self, elements: list):
        """
        Display properties for multiple selected elements.

        Args:
            elements: List of StructuralElement objects
        """
        if not elements:
            self.clear()
            return

        if len(elements) == 1:
            self.show_element(elements[0])
            return

        self._current_element_id = None
        self._property_rows.clear()

        # Clear existing content
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show multiple selection info
        header = QLabel(f"{len(elements)} elements selected")
        header.setStyleSheet("color: #0078d4; font-weight: bold; padding: 8px;")
        self.content_layout.addWidget(header)

        # Show common properties if all same type
        element_types = set(e.element_type.value for e in elements)
        if len(element_types) == 1:
            type_label = QLabel(f"Type: {list(element_types)[0].upper()}")
            type_label.setStyleSheet("color: white; padding: 4px 8px;")
            self.content_layout.addWidget(type_label)
        else:
            type_label = QLabel(f"Types: {', '.join(sorted(t.upper() for t in element_types))}")
            type_label.setStyleSheet("color: white; padding: 4px 8px;")
            self.content_layout.addWidget(type_label)

        # Count by type
        type_counts = {}
        for e in elements:
            t = e.element_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        for t, count in sorted(type_counts.items()):
            count_label = QLabel(f"  {t.capitalize()}: {count}")
            count_label.setStyleSheet("color: #888; padding: 2px 16px;")
            self.content_layout.addWidget(count_label)

        self.content_layout.addStretch()
