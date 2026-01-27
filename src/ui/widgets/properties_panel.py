"""
Properties panel widget for displaying element properties.

Shows selected element properties in a Tekla Structures-like format.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QScrollArea, QFrame, QGridLayout, QGroupBox,
    QSpinBox, QDoubleSpinBox, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from loguru import logger

from src.core.element import PositionOnPlane, PositionAtDepth, EndPointOffsets


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


class OffsetSpinRow(QWidget):
    """Property row with spin box for offset values."""

    value_changed = Signal(str, float)  # property_name, new_value

    def __init__(self, name: str, value: float, parent=None):
        """
        Create an offset spin row.

        Args:
            name: Property name (e.g., "Dx", "Dy", "Dz")
            value: Initial value in mm
            parent: Parent widget
        """
        super().__init__(parent)
        self.property_name = name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Label (property name)
        self.label = QLabel(name + ":")
        self.label.setMinimumWidth(40)
        self.label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.label)

        # Spin box for offset value
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(-10000.0, 10000.0)
        self.spin_box.setSuffix(" mm")
        self.spin_box.setDecimals(1)
        self.spin_box.setValue(value)
        self.spin_box.setStyleSheet("""
            QDoubleSpinBox {
                background: #3c3c3c;
                border: 1px solid #555;
                padding: 2px 4px;
                color: white;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #0078d4;
            }
        """)
        self.spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spin_box, 1)

    def _on_value_changed(self, value: float):
        """Handle spin box value change."""
        self.value_changed.emit(self.property_name, value)

    def set_value(self, value: float):
        """Set the spin box value."""
        self.spin_box.blockSignals(True)
        self.spin_box.setValue(value)
        self.spin_box.blockSignals(False)


class PositionComboRow(QWidget):
    """Property row with combo box for position enums."""

    value_changed = Signal(str, str)  # property_name, new_value

    def __init__(self, name: str, current: str, options: list, parent=None):
        """
        Create a position combo row.

        Args:
            name: Property name (e.g., "On Plane", "At Depth")
            current: Current selected value
            options: List of option strings
            parent: Parent widget
        """
        super().__init__(parent)
        self.property_name = name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Label (property name)
        self.label = QLabel(name + ":")
        self.label.setMinimumWidth(60)
        self.label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.label)

        # Combo box for position options
        self.combo_box = QComboBox()
        self.combo_box.addItems(options)
        if current in options:
            self.combo_box.setCurrentText(current)
        self.combo_box.setStyleSheet("""
            QComboBox {
                background: #3c3c3c;
                border: 1px solid #555;
                padding: 2px 4px;
                color: white;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #aaa;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                color: white;
                selection-background-color: #0078d4;
            }
        """)
        self.combo_box.currentTextChanged.connect(self._on_value_changed)
        layout.addWidget(self.combo_box, 1)

    def _on_value_changed(self, value: str):
        """Handle combo box value change."""
        self.value_changed.emit(self.property_name, value)

    def set_value(self, value: str):
        """Set the combo box value."""
        self.combo_box.blockSignals(True)
        self.combo_box.setCurrentText(value)
        self.combo_box.blockSignals(False)


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
        self._current_element = None  # Reference to current element for direct manipulation
        self._current_elements: List = []  # List of elements for multi-select editing
        self._property_rows: Dict[str, PropertyRow] = {}
        self._offset_rows: Dict[str, OffsetSpinRow] = {}
        self._position_rows: Dict[str, PositionComboRow] = {}

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
        self._current_element = None
        self._current_elements = []
        self._property_rows.clear()
        self._offset_rows.clear()
        self._position_rows.clear()

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
        self._current_element = element  # Store reference for direct manipulation
        self._property_rows.clear()
        self._offset_rows.clear()
        self._position_rows.clear()

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

        # Add position group if element supports it
        self._add_position_group(element)

        # Add start/end offsets groups for linear elements
        start_offsets = getattr(element, 'start_offsets', None)
        end_offsets = getattr(element, 'end_offsets', None)

        if start_offsets is not None:
            self._add_offsets_group("Start Offsets", start_offsets, "Start")

        if end_offsets is not None:
            self._add_offsets_group("End Offsets", end_offsets, "End")

        # Add Swap Start/End button for linear elements
        self._add_swap_button(element)

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

    def _on_offset_changed(self, prop_name: str, new_value: float):
        """Handle offset value change from OffsetSpinRow."""
        if self._current_element_id:
            self.property_changed.emit(self._current_element_id, prop_name, str(new_value))

    def _on_position_changed(self, prop_name: str, new_value: str):
        """Handle position value change from PositionComboRow."""
        if self._current_element_id:
            self.property_changed.emit(self._current_element_id, prop_name, new_value)

    def _add_position_group(self, element) -> Optional[QGroupBox]:
        """
        Create Position group box with On Plane and At Depth combos.

        Args:
            element: The structural element

        Returns:
            QGroupBox widget or None if element doesn't support positions
        """
        # Check if element has position attributes
        on_plane = getattr(element, 'position_on_plane', None)
        at_depth = getattr(element, 'position_at_depth', None)

        # If element doesn't have these attributes, skip
        if on_plane is None and at_depth is None:
            return None

        group = QGroupBox("Position")
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

        # On Plane combo (LEFT, MIDDLE, RIGHT)
        on_plane_options = [e.value for e in PositionOnPlane]
        current_on_plane = on_plane.value if hasattr(on_plane, 'value') else str(on_plane) if on_plane else "MIDDLE"
        on_plane_row = PositionComboRow("On Plane", current_on_plane, on_plane_options)
        on_plane_row.value_changed.connect(self._on_position_changed)
        self._position_rows["On Plane"] = on_plane_row
        group_layout.addWidget(on_plane_row)

        # At Depth combo (FRONT, MIDDLE, BEHIND)
        at_depth_options = [e.value for e in PositionAtDepth]
        current_at_depth = at_depth.value if hasattr(at_depth, 'value') else str(at_depth) if at_depth else "MIDDLE"
        at_depth_row = PositionComboRow("At Depth", current_at_depth, at_depth_options)
        at_depth_row.value_changed.connect(self._on_position_changed)
        self._position_rows["At Depth"] = at_depth_row
        group_layout.addWidget(at_depth_row)

        self.content_layout.addWidget(group)
        return group

    def _add_offsets_group(self, title: str, offset_vector, prefix: str) -> Optional[QGroupBox]:
        """
        Create offsets group box with Dx, Dy, Dz spin boxes.

        Args:
            title: Group title (e.g., "Start Offsets" or "End Offsets")
            offset_vector: Vector3D with current offset values
            prefix: Prefix for property names (e.g., "Start" or "End")

        Returns:
            QGroupBox widget or None if offset_vector is None
        """
        if offset_vector is None:
            return None

        group = QGroupBox(title)
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

        # Get offset values
        dx = getattr(offset_vector, 'dx', 0.0)
        dy = getattr(offset_vector, 'dy', 0.0)
        dz = getattr(offset_vector, 'dz', 0.0)

        # Dx spin box
        dx_row = OffsetSpinRow("Dx", dx)
        dx_row.value_changed.connect(lambda name, val: self._on_offset_changed(f"{prefix}_Dx", val))
        self._offset_rows[f"{prefix}_Dx"] = dx_row
        group_layout.addWidget(dx_row)

        # Dy spin box
        dy_row = OffsetSpinRow("Dy", dy)
        dy_row.value_changed.connect(lambda name, val: self._on_offset_changed(f"{prefix}_Dy", val))
        self._offset_rows[f"{prefix}_Dy"] = dy_row
        group_layout.addWidget(dy_row)

        # Dz spin box
        dz_row = OffsetSpinRow("Dz", dz)
        dz_row.value_changed.connect(lambda name, val: self._on_offset_changed(f"{prefix}_Dz", val))
        self._offset_rows[f"{prefix}_Dz"] = dz_row
        group_layout.addWidget(dz_row)

        self.content_layout.addWidget(group)
        return group

    def _add_swap_button(self, element) -> Optional[QPushButton]:
        """
        Add Swap Start/End button for elements with start and end points.

        Args:
            element: The structural element

        Returns:
            QPushButton widget or None if element doesn't support swapping
        """
        # Check if element has start_point and end_point
        has_start = hasattr(element, 'start_point')
        has_end = hasattr(element, 'end_point')

        if not (has_start and has_end):
            return None

        swap_button = QPushButton("Swap Start/End")
        swap_button.setStyleSheet("""
            QPushButton {
                background: #3c3c3c;
                border: 1px solid #555;
                padding: 6px 12px;
                color: white;
                font-size: 11px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background: #2a2a2a;
            }
        """)
        swap_button.clicked.connect(lambda: self._on_swap_start_end(element))
        self.content_layout.addWidget(swap_button)
        return swap_button

    def _on_swap_start_end(self, element):
        """
        Handle Swap Start/End button click.

        Args:
            element: The structural element to swap
        """
        if element is None:
            return

        # Check if element has swap_start_end method
        if hasattr(element, 'swap_start_end') and callable(getattr(element, 'swap_start_end')):
            element.swap_start_end()
        else:
            # Manual swap for elements without dedicated method
            if hasattr(element, 'start_point') and hasattr(element, 'end_point'):
                temp = element.start_point
                element.start_point = element.end_point
                element.end_point = temp

                # Swap offsets if they exist
                if hasattr(element, 'start_offsets') and hasattr(element, 'end_offsets'):
                    temp_offsets = element.start_offsets
                    element.start_offsets = element.end_offsets
                    element.end_offsets = temp_offsets

                # Invalidate geometry
                if hasattr(element, 'invalidate') and callable(getattr(element, 'invalidate')):
                    element.invalidate()

        # Refresh the panel
        self.show_element(element)
        logger.debug(f"Swapped start/end for element {element.id}")

    def show_multiple(self, elements: list):
        """
        Display and allow editing of shared properties for multiple elements.

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
        self._current_elements = elements  # Store list for batch editing
        self._property_rows.clear()
        self._offset_rows.clear()
        self._position_rows.clear()

        # Clear existing content
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header
        header = QLabel(f"Multiple Selection ({len(elements)} elements)")
        header.setStyleSheet("color: #0078d4; font-weight: bold; font-size: 12px; padding: 8px;")
        self.content_layout.addWidget(header)

        # Show element type summary
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

        # Find shared properties
        shared_props = self._get_shared_properties(elements)

        # Create editable rows for shared properties
        self._add_shared_property_group("Shared Properties", shared_props, elements)

        self.content_layout.addStretch()

    def _get_shared_properties(self, elements: list) -> Dict[str, Any]:
        """Get properties shared across all elements (optimized)."""
        if not elements:
            return {}

        # Cache all properties to avoid repeated calls
        all_props = [elem.get_properties() for elem in elements]
        first_props = all_props[0]
        shared = {}

        for key, value in first_props.items():
            all_same = all(props.get(key) == value for props in all_props)
            shared[key] = value if all_same else "<varies>"

        return shared

    def _add_shared_property_group(self, title: str, props: Dict[str, Any], elements: list):
        """
        Add group for shared properties with batch editing support.

        Properties that can be edited across multiple elements:
        - Name, Phase, Class, Rotation

        Args:
            title: Group box title
            props: Dictionary of property names and values
            elements: List of elements for batch editing
        """
        editable_props = ["Name", "Phase", "Class", "Rotation"]

        group = QGroupBox(title)
        group.setStyleSheet(self._group_style())
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(4, 8, 4, 4)
        group_layout.setSpacing(2)

        for key, value in props.items():
            if key in editable_props:
                is_varies = (value == "<varies>")
                display_value = "" if is_varies else str(value)
                placeholder = "<varies>" if is_varies else ""

                row = PropertyRow(key, display_value, editable=True)
                # Set placeholder for varying values
                if hasattr(row, 'value_widget') and isinstance(row.value_widget, QLineEdit):
                    row.value_widget.setPlaceholderText(placeholder)
                # Connect to batch handler using lambda with default arguments to capture current values
                row.value_changed.connect(
                    lambda name, val, elems=elements: self._on_batch_property_changed(name, val, elems)
                )
                self._property_rows[key] = row
                group_layout.addWidget(row)
            else:
                # Non-editable - just show value
                display_value = str(value) if value is not None else ""
                row = PropertyRow(key, display_value, editable=False)
                group_layout.addWidget(row)

        self.content_layout.addWidget(group)

    def _on_batch_property_changed(self, name: str, value: str, elements: list):
        """
        Apply property change to all selected elements.

        Args:
            name: Property name to change
            value: New value to apply
            elements: List of elements to update
        """
        if not value:  # Don't apply empty values
            return

        count = 0
        for element in elements:
            if element.set_property(name, value):
                count += 1

        logger.info(f"Batch updated '{name}' to '{value}' for {count}/{len(elements)} elements")

    def _group_style(self) -> str:
        """Return the common style for group boxes."""
        return """
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
        """
