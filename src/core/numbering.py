"""Element numbering manager for Schmekla.

Provides Tekla-style automatic part numbering (B1, B2, C1, C2, etc.)
with configurable series and position numbering for start/end points.

Supports identical parts detection - parts with matching signatures
(profile + material + geometry within tolerance) receive the same number.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING
from loguru import logger
from src.core.element import ElementType

if TYPE_CHECKING:
    from src.core.element import StructuralElement
    from src.geometry.point import Point3D


@dataclass
class NumberingSeries:
    """Configuration for a numbering series.

    Tekla-style numbering series that can be configured per element type.
    """
    prefix: str
    start_number: int = 1
    current_counter: int = 0

    def get_next(self) -> str:
        """Get next number in series."""
        self.current_counter += 1
        return f"{self.prefix}{self.start_number + self.current_counter - 1}"

    def reset(self):
        """Reset counter to beginning."""
        self.current_counter = 0

    def peek_next(self) -> str:
        """Preview next number without incrementing."""
        return f"{self.prefix}{self.start_number + self.current_counter}"


@dataclass
class PositionNumber:
    """Position number for element start/end points (Tekla-style).

    In Tekla, elements can have position numbers that identify their
    start and end points in the model for connection purposes.
    """
    element_id: str
    start_position: int = 0
    end_position: int = 0

    def __str__(self) -> str:
        return f"{self.start_position}-{self.end_position}"


@dataclass
class ComparisonConfig:
    """Configuration for part signature comparison (Tekla-style).

    Controls which properties are compared when determining if two parts
    are identical and should receive the same part number.
    """
    compare_profile: bool = True      # Compare section profile (e.g., UB 305x165x40)
    compare_material: bool = True     # Compare material (e.g., S355)
    compare_name: bool = False        # Compare element name/mark
    compare_geometry: bool = True     # Compare geometry (length/dimensions)
    compare_rotation: bool = True     # Compare rotation angle
    geometry_tolerance: float = 1.0   # Tolerance for geometry comparison (mm)

    def to_dict(self) -> Dict:
        """Serialize to dictionary for persistence."""
        return {
            'compare_profile': self.compare_profile,
            'compare_material': self.compare_material,
            'compare_name': self.compare_name,
            'compare_geometry': self.compare_geometry,
            'compare_rotation': self.compare_rotation,
            'geometry_tolerance': self.geometry_tolerance,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ComparisonConfig":
        """Create from dictionary."""
        return cls(
            compare_profile=data.get('compare_profile', True),
            compare_material=data.get('compare_material', True),
            compare_name=data.get('compare_name', False),
            compare_geometry=data.get('compare_geometry', True),
            compare_rotation=data.get('compare_rotation', True),
            geometry_tolerance=data.get('geometry_tolerance', 1.0),
        )


@dataclass(frozen=True)
class PartSignature:
    """Immutable signature representing part identity for numbering.

    Two parts with the same signature are considered identical and
    receive the same part number (Tekla-style identical parts).

    This is a frozen dataclass so it can be used as a dictionary key.
    """
    element_type: str           # "beam", "column", "plate", etc.
    profile_name: str = ""      # Profile name (empty if not comparing)
    material_name: str = ""     # Material name (empty if not comparing)
    element_name: str = ""      # Element name (empty if not comparing)
    geometry_key: str = ""      # Geometry key (e.g., "L:6000" for beam length)
    rotation_key: str = ""      # Rotation key (e.g., "R:45")

    def __str__(self) -> str:
        parts = [self.element_type]
        if self.profile_name:
            parts.append(self.profile_name)
        if self.material_name:
            parts.append(self.material_name)
        if self.element_name:
            parts.append(f"N:{self.element_name}")
        if self.geometry_key:
            parts.append(self.geometry_key)
        if self.rotation_key:
            parts.append(self.rotation_key)
        return "|".join(parts)


class NumberingManager:
    """Manages automatic part numbering like Tekla Structures.

    Features:
    - Configurable prefix per element type
    - Configurable start number per series
    - Position numbering for start/end points
    - Series management (add, modify, reset)
    """

    # Default element type prefix mapping
    DEFAULT_PREFIXES = {
        ElementType.BEAM: "B",
        ElementType.COLUMN: "C",
        ElementType.PLATE: "PL",
        ElementType.SLAB: "S",
        ElementType.WALL: "W",
        ElementType.FOOTING: "F",
        ElementType.BRACE: "BR",
        ElementType.PURLIN: "P",
        ElementType.GIRT: "G",
    }

    def __init__(self):
        # Series configuration per element type
        self._series: Dict[ElementType, NumberingSeries] = {}

        # Position numbering tracking
        self._position_counter: int = 0
        self._position_numbers: Dict[str, PositionNumber] = {}  # element_id -> PositionNumber

        # Point position tracking for unique positions
        self._point_positions: Dict[Tuple[float, float, float], int] = {}
        self._position_tolerance: float = 10.0  # mm tolerance for point matching

        # Tekla-style identical parts numbering
        self._comparison_config: ComparisonConfig = ComparisonConfig()
        self._signature_cache: Dict[PartSignature, str] = {}  # signature -> part_number
        self._part_counts: Dict[PartSignature, int] = {}      # signature -> count of parts

        # Initialize default series
        self._initialize_default_series()

        logger.debug("NumberingManager initialized")

    def _initialize_default_series(self):
        """Initialize default numbering series for all element types."""
        for elem_type, prefix in self.DEFAULT_PREFIXES.items():
            self._series[elem_type] = NumberingSeries(
                prefix=prefix,
                start_number=1,
                current_counter=0
            )

    def configure_series(self, element_type: ElementType, prefix: str,
                        start_number: int = 1) -> NumberingSeries:
        """Configure numbering series for an element type.

        Args:
            element_type: Type of structural element
            prefix: String prefix (e.g., "B", "BEAM", "STR-B")
            start_number: Starting number for the series

        Returns:
            The configured NumberingSeries
        """
        series = NumberingSeries(
            prefix=prefix,
            start_number=start_number,
            current_counter=0
        )
        self._series[element_type] = series
        logger.info(f"Configured series for {element_type.value}: {prefix}{start_number}+")
        return series

    def get_series(self, element_type: ElementType) -> NumberingSeries:
        """Get numbering series for element type.

        Args:
            element_type: Type of structural element

        Returns:
            NumberingSeries for that type
        """
        if element_type not in self._series:
            # Create default series if not configured
            prefix = self.DEFAULT_PREFIXES.get(element_type, "E")
            self._series[element_type] = NumberingSeries(prefix=prefix)
        return self._series[element_type]

    def get_next_number(self, element_type: ElementType) -> str:
        """Get next part number for element type.

        Args:
            element_type: Type of structural element

        Returns:
            Part number string like "B1", "C2", etc.
        """
        series = self.get_series(element_type)
        return series.get_next()

    def get_number_for_element(self, element: "StructuralElement") -> str:
        """Get part number for element using identical parts detection.

        Tekla-style numbering: elements with matching signatures (same profile,
        material, geometry within tolerance) receive the same part number.
        For example, 5 identical beams all get "B1".

        Args:
            element: The structural element to number

        Returns:
            Part number string (may be same as existing part if identical)
        """
        # Calculate element signature based on comparison config
        signature = self._calculate_signature(element)

        # Check if we've seen this signature before
        if signature in self._signature_cache:
            part_number = self._signature_cache[signature]
            self._part_counts[signature] = self._part_counts.get(signature, 0) + 1
            logger.debug(f"Identical part found: {element.id} -> {part_number} "
                        f"(count: {self._part_counts[signature]})")
            return part_number

        # New signature - get next number in series
        part_number = self.get_next_number(element.element_type)
        self._signature_cache[signature] = part_number
        self._part_counts[signature] = 1

        logger.debug(f"New part signature: {element.id} -> {part_number} "
                    f"(signature: {signature})")
        return part_number

    def _calculate_signature(self, element: "StructuralElement") -> PartSignature:
        """Calculate signature for element based on comparison config.

        Delegates to element.calculate_signature() which handles all the
        comparison logic based on the configuration.

        Args:
            element: Element to calculate signature for

        Returns:
            PartSignature that can be used as dictionary key
        """
        return element.calculate_signature(self._comparison_config)

    def set_comparison_config(self, config: ComparisonConfig):
        """Set comparison configuration for identical parts detection.

        Note: Changing config after numbering has started may cause
        inconsistent numbering. Consider calling reset() first.

        Args:
            config: New comparison configuration
        """
        self._comparison_config = config
        logger.info(f"Comparison config updated: profile={config.compare_profile}, "
                   f"material={config.compare_material}, geometry={config.compare_geometry}, "
                   f"tolerance={config.geometry_tolerance}mm")

    def get_comparison_config(self) -> ComparisonConfig:
        """Get current comparison configuration.

        Returns:
            Current ComparisonConfig
        """
        return self._comparison_config

    def get_identical_parts_count(self, signature: PartSignature) -> int:
        """Get count of parts with the same signature.

        Args:
            signature: Part signature to look up

        Returns:
            Number of parts with this signature
        """
        return self._part_counts.get(signature, 0)

    def get_all_signatures(self) -> Dict[PartSignature, str]:
        """Get all registered signatures and their part numbers.

        Returns:
            Dict mapping signatures to part numbers
        """
        return self._signature_cache.copy()

    def get_identical_parts_summary(self) -> List[Dict]:
        """Get summary of all identical parts groups for reporting.

        Returns a list of dictionaries, each containing:
        - part_number: The assigned part number (e.g., "B1")
        - signature: String representation of the signature
        - count: Number of parts with this signature
        - element_type: Type of element (beam, column, etc.)
        - profile: Profile name (if applicable)
        - material: Material name (if applicable)

        Returns:
            List of dicts with identical parts group information
        """
        summary = []
        for signature, part_number in self._signature_cache.items():
            count = self._part_counts.get(signature, 0)
            summary.append({
                'part_number': part_number,
                'signature': str(signature),
                'count': count,
                'element_type': signature.element_type,
                'profile': signature.profile_name or "N/A",
                'material': signature.material_name or "N/A",
                'geometry_key': signature.geometry_key or "N/A",
                'rotation_key': signature.rotation_key or "N/A",
            })

        # Sort by part number for consistent ordering
        summary.sort(key=lambda x: x['part_number'])
        return summary

    def preview_renumber(self, elements: List["StructuralElement"]) -> Dict[str, str]:
        """Preview what numbers elements would receive without actually assigning.

        Useful for showing user what renumbering will do before executing.

        Args:
            elements: List of elements to preview

        Returns:
            Dict mapping element ID (str) to proposed part number
        """
        # Save current state
        old_cache = self._signature_cache.copy()
        old_counts = self._part_counts.copy()
        old_counters = {et: s.current_counter for et, s in self._series.items()}

        # Reset for preview
        self._signature_cache.clear()
        self._part_counts.clear()
        for series in self._series.values():
            series.reset()

        # Calculate preview numbers
        preview = {}
        for element in elements:
            proposed_number = self.get_number_for_element(element)
            preview[str(element.id)] = proposed_number

        # Restore state
        self._signature_cache = old_cache
        self._part_counts = old_counts
        for et, counter in old_counters.items():
            self._series[et].current_counter = counter

        return preview

    def get_position_number(self, element: "StructuralElement",
                           start_point: "Point3D" = None,
                           end_point: "Point3D" = None) -> PositionNumber:
        """Get or create position numbers for element start/end points.

        Tekla-style position numbering assigns unique numbers to geometric
        positions. Elements sharing the same position get the same number.

        Args:
            element: The structural element
            start_point: Start point (optional, derived from element if not provided)
            end_point: End point (optional, derived from element if not provided)

        Returns:
            PositionNumber with start and end position numbers
        """
        from src.core.beam import Beam
        from src.core.column import Column

        elem_id = str(element.id)

        # Check if already assigned
        if elem_id in self._position_numbers:
            return self._position_numbers[elem_id]

        # Get points from element if not provided
        if start_point is None or end_point is None:
            if isinstance(element, Beam):
                start_point = start_point or element.start_point
                end_point = end_point or element.end_point
            elif isinstance(element, Column):
                start_point = start_point or element.base_point
                # For columns, end point is top of column
                if hasattr(element, 'top_point'):
                    end_point = end_point or element.top_point
                else:
                    from src.geometry.point import Point3D
                    end_point = end_point or Point3D(
                        element.base_point.x,
                        element.base_point.y,
                        element.base_point.z + element.height
                    )
            else:
                # For other elements, use origin as default
                from src.geometry.point import Point3D
                start_point = start_point or Point3D.origin()
                end_point = end_point or Point3D.origin()

        # Get position numbers for start and end points
        start_pos = self._get_point_position(start_point)
        end_pos = self._get_point_position(end_point)

        # Create position number record
        pos_num = PositionNumber(
            element_id=elem_id,
            start_position=start_pos,
            end_position=end_pos
        )
        self._position_numbers[elem_id] = pos_num

        logger.debug(f"Position number for {elem_id}: {pos_num}")
        return pos_num

    def _get_point_position(self, point: "Point3D") -> int:
        """Get or assign position number for a 3D point.

        Points within tolerance of each other share the same position number.

        Args:
            point: 3D point to get position for

        Returns:
            Position number (integer)
        """
        # Round point to tolerance grid
        key = self._point_to_key(point)

        if key not in self._point_positions:
            self._position_counter += 1
            self._point_positions[key] = self._position_counter

        return self._point_positions[key]

    def _point_to_key(self, point: "Point3D") -> Tuple[float, float, float]:
        """Convert point to hashable key with tolerance rounding.

        Args:
            point: 3D point

        Returns:
            Tuple of rounded coordinates
        """
        tol = self._position_tolerance
        return (
            round(point.x / tol) * tol,
            round(point.y / tol) * tol,
            round(point.z / tol) * tol
        )

    def set_position_tolerance(self, tolerance: float):
        """Set tolerance for position point matching.

        Args:
            tolerance: Distance in mm within which points are considered same
        """
        self._position_tolerance = max(1.0, tolerance)
        logger.info(f"Position tolerance set to {self._position_tolerance}mm")

    def reset(self):
        """Reset all counters, position tracking, and signature caches."""
        for series in self._series.values():
            series.reset()
        self._position_counter = 0
        self._position_numbers.clear()
        self._point_positions.clear()
        # Clear identical parts caches
        self._signature_cache.clear()
        self._part_counts.clear()
        logger.info("Numbering manager reset (including signature caches)")

    def reset_series(self, element_type: ElementType):
        """Reset counter for specific element type.

        Args:
            element_type: Type of element to reset
        """
        if element_type in self._series:
            self._series[element_type].reset()
            logger.info(f"Reset series for {element_type.value}")

    def get_current_count(self, element_type: ElementType) -> int:
        """Get current count for an element type.

        Args:
            element_type: Type of structural element

        Returns:
            Current counter value
        """
        series = self.get_series(element_type)
        return series.current_counter

    def get_all_series_config(self) -> Dict[str, Dict]:
        """Get configuration of all series for UI display.

        Returns:
            Dict mapping element type names to their series config
        """
        config = {}
        for elem_type, series in self._series.items():
            config[elem_type.value] = {
                'prefix': series.prefix,
                'start_number': series.start_number,
                'current_counter': series.current_counter,
                'next_number': series.peek_next()
            }
        return config

    def set_series_from_config(self, config: Dict[str, Dict]):
        """Set series configuration from dict (for UI/persistence).

        Args:
            config: Dict mapping element type names to their config
        """
        for type_name, series_config in config.items():
            try:
                elem_type = ElementType(type_name)
                self.configure_series(
                    elem_type,
                    prefix=series_config.get('prefix', 'E'),
                    start_number=series_config.get('start_number', 1)
                )
            except ValueError:
                logger.warning(f"Unknown element type: {type_name}")
