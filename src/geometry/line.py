"""
3D Line class for Schmekla.

Represents a line segment or infinite line in 3D space.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D


class Line3D:
    """
    3D line defined by start and end points.

    Can represent both finite line segments and infinite lines.
    """

    def __init__(self, start: Point3D, end: Point3D):
        """
        Create a 3D line.

        Args:
            start: Start point
            end: End point
        """
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f"Line3D({self.start} -> {self.end})"

    @property
    def length(self) -> float:
        """Line segment length."""
        return self.start.distance_to(self.end)

    @property
    def direction(self) -> Vector3D:
        """Unit direction vector from start to end."""
        return (self.end - self.start).normalize()

    @property
    def vector(self) -> Vector3D:
        """Vector from start to end (not normalized)."""
        return self.end - self.start

    @property
    def midpoint(self) -> Point3D:
        """Midpoint of line segment."""
        return self.start.midpoint_to(self.end)

    def point_at(self, t: float) -> Point3D:
        """
        Get point at parameter t along line.

        Args:
            t: Parameter (0 = start, 1 = end, can be outside [0,1] for infinite line)

        Returns:
            Point at parameter t
        """
        return self.start.interpolate_to(self.end, t)

    def point_at_distance(self, distance: float) -> Point3D:
        """
        Get point at distance from start.

        Args:
            distance: Distance from start in mm

        Returns:
            Point at specified distance
        """
        t = distance / self.length if self.length > 0 else 0
        return self.point_at(t)

    def closest_point_to(self, point: Point3D, clamp: bool = True) -> Point3D:
        """
        Find closest point on line to given point.

        Args:
            point: Target point
            clamp: If True, clamp to line segment; if False, treat as infinite line

        Returns:
            Closest point on line
        """
        v = self.vector
        w = point - self.start

        c1 = w.dot(v)
        c2 = v.dot(v)

        if c2 < 1e-10:
            return self.start.copy()

        t = c1 / c2

        if clamp:
            t = max(0.0, min(1.0, t))

        return self.point_at(t)

    def distance_to_point(self, point: Point3D, clamp: bool = True) -> float:
        """
        Calculate distance from line to point.

        Args:
            point: Target point
            clamp: If True, use line segment; if False, treat as infinite line

        Returns:
            Distance in mm
        """
        closest = self.closest_point_to(point, clamp)
        return closest.distance_to(point)

    def intersection_with_plane(self, plane: "Plane") -> Optional[Point3D]:
        """
        Find intersection point with a plane.

        Args:
            plane: Target plane

        Returns:
            Intersection point or None if parallel
        """
        denom = self.direction.dot(plane.normal)

        if abs(denom) < 1e-10:
            return None  # Line parallel to plane

        d = plane.point - self.start
        t = d.dot(plane.normal) / denom

        return self.point_at(t)

    def intersection_with_line(
        self, other: "Line3D", tolerance: float = 1e-6
    ) -> Optional[Point3D]:
        """
        Find intersection point with another line.

        Args:
            other: Other line
            tolerance: Distance tolerance for intersection

        Returns:
            Intersection point or None if lines don't intersect
        """
        # Uses the algorithm for finding closest points between two lines
        p1, p2 = self.start, self.end
        p3, p4 = other.start, other.end

        d1 = p2 - p1
        d2 = p4 - p3
        d21 = p3 - p1

        d1d1 = d1.dot(d1)
        d2d2 = d2.dot(d2)
        d1d2 = d1.dot(d2)
        d21d1 = d21.dot(d1)
        d21d2 = d21.dot(d2)

        denom = d1d1 * d2d2 - d1d2 * d1d2

        if abs(denom) < 1e-10:
            return None  # Lines are parallel

        t1 = (d21d1 * d2d2 - d21d2 * d1d2) / denom
        t2 = (d21d1 * d1d2 - d21d2 * d1d1) / denom

        pt1 = self.point_at(t1)
        pt2 = other.point_at(t2)

        if pt1.distance_to(pt2) <= tolerance:
            return pt1.midpoint_to(pt2)

        return None

    def split_at(self, t: float) -> Tuple["Line3D", "Line3D"]:
        """
        Split line at parameter t.

        Args:
            t: Split parameter (0-1)

        Returns:
            Tuple of two line segments
        """
        mid = self.point_at(t)
        return (Line3D(self.start, mid), Line3D(mid, self.end))

    def split_at_point(self, point: Point3D) -> Tuple["Line3D", "Line3D"]:
        """
        Split line at given point.

        Args:
            point: Split point (should be on line)

        Returns:
            Tuple of two line segments
        """
        return (Line3D(self.start, point), Line3D(point, self.end))

    def extend_start(self, distance: float) -> "Line3D":
        """
        Extend line from start by distance.

        Args:
            distance: Extension distance (positive = extend beyond start)

        Returns:
            New extended line
        """
        new_start = self.start - self.direction * distance
        return Line3D(new_start, self.end)

    def extend_end(self, distance: float) -> "Line3D":
        """
        Extend line at end by distance.

        Args:
            distance: Extension distance (positive = extend beyond end)

        Returns:
            New extended line
        """
        new_end = self.end + self.direction * distance
        return Line3D(self.start, new_end)

    def reverse(self) -> "Line3D":
        """
        Create reversed line (swap start and end).

        Returns:
            Reversed line
        """
        return Line3D(self.end, self.start)

    def translate(self, vector: Vector3D) -> "Line3D":
        """
        Translate line by vector.

        Args:
            vector: Translation vector

        Returns:
            Translated line
        """
        return Line3D(self.start + vector, self.end + vector)

    def copy(self) -> "Line3D":
        """Create a copy of this line."""
        return Line3D(self.start.copy(), self.end.copy())

    @classmethod
    def from_point_and_direction(
        cls, point: Point3D, direction: Vector3D, length: float
    ) -> "Line3D":
        """
        Create line from point, direction, and length.

        Args:
            point: Start point
            direction: Direction vector (will be normalized)
            length: Line length

        Returns:
            Line3D
        """
        end = point + direction.normalize() * length
        return cls(point, end)
