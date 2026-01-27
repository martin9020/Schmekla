"""Snap manager for Schmekla - grid and point snapping.

Provides Tekla-like snapping functionality during element creation.
"""
from typing import Optional, List, Tuple, TYPE_CHECKING
from loguru import logger
from src.geometry.point import Point3D

if TYPE_CHECKING:
    from src.core.model import StructuralModel


class SnapManager:
    """Manages snapping to grid points, endpoints, etc."""

    def __init__(self, model: "StructuralModel"):
        self.model = model
        self.snap_tolerance = 500.0  # mm - snap radius
        self.snap_enabled = True
        self.grid_snap = True
        self.endpoint_snap = True
        self._cached_grid_points: Optional[List[Point3D]] = None

    def invalidate_cache(self):
        """Clear cached grid points when grids change."""
        self._cached_grid_points = None

    def get_grid_intersection_points(self) -> List[Point3D]:
        """Calculate all grid intersection points.

        Returns:
            List of Point3D at each grid intersection (X grid x Y grid)
        """
        if self._cached_grid_points is not None:
            return self._cached_grid_points

        points = []
        grids = getattr(self.model, '_grids', None)
        if not grids:
            return points

        x_positions = [g.get('position', 0) for g in grids.get('x_grids', [])]
        y_positions = [g.get('position', 0) for g in grids.get('y_grids', [])]

        for x in x_positions:
            for y in y_positions:
                points.append(Point3D(x, y, 0.0))

        self._cached_grid_points = points
        logger.debug(f"Cached {len(points)} grid intersection points")
        return points

    def find_nearest_snap(self, point: Point3D) -> Tuple[Optional[Point3D], str]:
        """Find nearest snap point within tolerance.

        Args:
            point: Input point to snap from

        Returns:
            Tuple of (snap_point, snap_type) or (None, "") if no snap found
            snap_type can be: "grid", "endpoint", "midpoint"
        """
        if not self.snap_enabled:
            return None, ""

        best_point = None
        best_dist = self.snap_tolerance
        snap_type = ""

        # Check grid intersections first (highest priority)
        if self.grid_snap:
            for grid_pt in self.get_grid_intersection_points():
                dist = point.distance_to(grid_pt)
                if dist < best_dist:
                    best_dist = dist
                    best_point = grid_pt
                    snap_type = "grid"

        # Check element endpoints
        if self.endpoint_snap:
            from src.core.beam import Beam
            from src.core.column import Column

            for elem in self.model.get_all_elements():
                endpoints = []

                if isinstance(elem, Beam):
                    endpoints = [elem.start_point, elem.end_point]
                elif isinstance(elem, Column):
                    if hasattr(elem, 'start_point') and hasattr(elem, 'end_point'):
                        endpoints = [elem.start_point, elem.end_point]
                    elif hasattr(elem, 'base_point'):
                        endpoints = [elem.base_point]

                for ep in endpoints:
                    dist = point.distance_to(ep)
                    if dist < best_dist:
                        best_dist = dist
                        best_point = ep
                        snap_type = "endpoint"

        return best_point, snap_type

    def set_snap_tolerance(self, tolerance: float):
        """Set snap tolerance in mm."""
        self.snap_tolerance = max(10.0, tolerance)  # Minimum 10mm

    def toggle_grid_snap(self, enabled: bool = None):
        """Toggle or set grid snapping."""
        if enabled is None:
            self.grid_snap = not self.grid_snap
        else:
            self.grid_snap = enabled
        logger.info(f"Grid snap: {'enabled' if self.grid_snap else 'disabled'}")

    def toggle_endpoint_snap(self, enabled: bool = None):
        """Toggle or set endpoint snapping."""
        if enabled is None:
            self.endpoint_snap = not self.endpoint_snap
        else:
            self.endpoint_snap = enabled
        logger.info(f"Endpoint snap: {'enabled' if self.endpoint_snap else 'disabled'}")
