"""
Unit conversion utilities for Schmekla.

All internal calculations use millimeters (mm) for length.
This module handles conversion to/from display units.
"""

from enum import Enum
from typing import Union


class LengthUnit(Enum):
    """Supported length units."""
    MILLIMETER = "mm"
    METER = "m"
    INCH = "in"
    FOOT = "ft"


class AngleUnit(Enum):
    """Supported angle units."""
    DEGREE = "deg"
    RADIAN = "rad"


class ForceUnit(Enum):
    """Supported force units."""
    NEWTON = "N"
    KILONEWTON = "kN"
    POUND_FORCE = "lbf"
    KIP = "kip"


# Conversion factors to base units (mm for length, radians for angle, N for force)
LENGTH_TO_MM = {
    LengthUnit.MILLIMETER: 1.0,
    LengthUnit.METER: 1000.0,
    LengthUnit.INCH: 25.4,
    LengthUnit.FOOT: 304.8,
}

ANGLE_TO_RAD = {
    AngleUnit.DEGREE: 0.017453292519943295,  # pi/180
    AngleUnit.RADIAN: 1.0,
}

FORCE_TO_N = {
    ForceUnit.NEWTON: 1.0,
    ForceUnit.KILONEWTON: 1000.0,
    ForceUnit.POUND_FORCE: 4.4482216152605,
    ForceUnit.KIP: 4448.2216152605,
}


class UnitConverter:
    """
    Unit conversion utility.

    All internal values are stored in:
    - Length: millimeters (mm)
    - Angle: degrees (deg) for user-facing, radians internally for math
    - Force: Newtons (N)
    """

    def __init__(
        self,
        length_unit: Union[LengthUnit, str] = LengthUnit.MILLIMETER,
        angle_unit: Union[AngleUnit, str] = AngleUnit.DEGREE,
        force_unit: Union[ForceUnit, str] = ForceUnit.KILONEWTON,
    ):
        """
        Initialize unit converter with display units.

        Args:
            length_unit: Display unit for lengths
            angle_unit: Display unit for angles
            force_unit: Display unit for forces
        """
        self.length_unit = self._parse_length_unit(length_unit)
        self.angle_unit = self._parse_angle_unit(angle_unit)
        self.force_unit = self._parse_force_unit(force_unit)

    def _parse_length_unit(self, unit: Union[LengthUnit, str]) -> LengthUnit:
        """Parse length unit from string or enum."""
        if isinstance(unit, LengthUnit):
            return unit
        for lu in LengthUnit:
            if lu.value == unit:
                return lu
        raise ValueError(f"Unknown length unit: {unit}")

    def _parse_angle_unit(self, unit: Union[AngleUnit, str]) -> AngleUnit:
        """Parse angle unit from string or enum."""
        if isinstance(unit, AngleUnit):
            return unit
        for au in AngleUnit:
            if au.value == unit:
                return au
        raise ValueError(f"Unknown angle unit: {unit}")

    def _parse_force_unit(self, unit: Union[ForceUnit, str]) -> ForceUnit:
        """Parse force unit from string or enum."""
        if isinstance(unit, ForceUnit):
            return unit
        for fu in ForceUnit:
            if fu.value == unit:
                return fu
        raise ValueError(f"Unknown force unit: {unit}")

    # Length conversions
    def to_mm(self, value: float, from_unit: LengthUnit = None) -> float:
        """Convert length to millimeters."""
        if from_unit is None:
            from_unit = self.length_unit
        return value * LENGTH_TO_MM[from_unit]

    def from_mm(self, value_mm: float, to_unit: LengthUnit = None) -> float:
        """Convert millimeters to display unit."""
        if to_unit is None:
            to_unit = self.length_unit
        return value_mm / LENGTH_TO_MM[to_unit]

    # Angle conversions
    def to_radians(self, value: float, from_unit: AngleUnit = None) -> float:
        """Convert angle to radians."""
        if from_unit is None:
            from_unit = self.angle_unit
        return value * ANGLE_TO_RAD[from_unit]

    def from_radians(self, value_rad: float, to_unit: AngleUnit = None) -> float:
        """Convert radians to display unit."""
        if to_unit is None:
            to_unit = self.angle_unit
        return value_rad / ANGLE_TO_RAD[to_unit]

    def to_degrees(self, value: float, from_unit: AngleUnit = None) -> float:
        """Convert angle to degrees."""
        rad = self.to_radians(value, from_unit)
        return rad / ANGLE_TO_RAD[AngleUnit.DEGREE]

    # Force conversions
    def to_newtons(self, value: float, from_unit: ForceUnit = None) -> float:
        """Convert force to Newtons."""
        if from_unit is None:
            from_unit = self.force_unit
        return value * FORCE_TO_N[from_unit]

    def from_newtons(self, value_n: float, to_unit: ForceUnit = None) -> float:
        """Convert Newtons to display unit."""
        if to_unit is None:
            to_unit = self.force_unit
        return value_n / FORCE_TO_N[to_unit]

    # Format for display
    def format_length(self, value_mm: float, decimals: int = 1) -> str:
        """Format length value with unit suffix."""
        display_value = self.from_mm(value_mm)
        return f"{display_value:.{decimals}f} {self.length_unit.value}"

    def format_angle(self, value_deg: float, decimals: int = 1) -> str:
        """Format angle value with unit suffix."""
        if self.angle_unit == AngleUnit.RADIAN:
            value_rad = value_deg * ANGLE_TO_RAD[AngleUnit.DEGREE]
            return f"{value_rad:.{decimals}f} rad"
        return f"{value_deg:.{decimals}f}°"

    def format_force(self, value_n: float, decimals: int = 2) -> str:
        """Format force value with unit suffix."""
        display_value = self.from_newtons(value_n)
        return f"{display_value:.{decimals}f} {self.force_unit.value}"


# Global default converter
_default_converter = UnitConverter()


def set_default_units(
    length: str = "mm",
    angle: str = "deg",
    force: str = "kN"
):
    """Set default units for the application."""
    global _default_converter
    _default_converter = UnitConverter(length, angle, force)


def get_converter() -> UnitConverter:
    """Get the default unit converter."""
    return _default_converter
