"""
Plane class for Schmekla.

Represents an infinite plane in 3D space.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D


class Plane:
    """
    Infinite plane in 3D space.

    Defined by a point on the plane and a normal vector.
    """

    def __init__(self, point: Point3D, normal: Vector3D):
        """
        Create a plane.

        Args:
            point: A point on the plane
            normal: Normal vector to the plane (will be normalized)
        """
        self.point = point
        self.normal = normal.normalize()

    def __repr__(self) -> str:
        return f"Plane(point={self.point}, normal={self.normal})"

    @property
    def d(self) -> float:
        """
        Plane equation constant (ax + by + cz + d = 0).

        Returns:
            D value in plane equation
        """
        return -(
            self.normal.x * self.point.x
            + self.normal.y * self.point.y
            + self.normal.z * self.point.z
        )

    def distance_to_point(self, point: Point3D) -> float:
        """
        Calculate signed distance from plane to point.

        Positive = point is on normal side
        Negative = point is on opposite side

        Args:
            point: Target point

        Returns:
            Signed distance in mm
        """
        return (
            self.normal.x * point.x
            + self.normal.y * point.y
            + self.normal.z * point.z
            + self.d
        )

    def closest_point_to(self, point: Point3D) -> Point3D:
        """
        Find closest point on plane to given point.

        Args:
            point: Target point

        Returns:
            Closest point on plane
        """
        dist = self.distance_to_point(point)
        return point - self.normal * dist

    def project_point(self, point: Point3D) -> Point3D:
        """
        Project point onto plane.

        Same as closest_point_to but named for clarity.

        Args:
            point: Point to project

        Returns:
            Projected point
        """
        return self.closest_point_to(point)

    def project_vector(self, vector: Vector3D) -> Vector3D:
        """
        Project vector onto plane (remove normal component).

        Args:
            vector: Vector to project

        Returns:
            Projected vector
        """
        normal_component = self.normal * vector.dot(self.normal)
        return vector - normal_component

    def is_point_on_plane(self, point: Point3D, tolerance: float = 1e-6) -> bool:
        """
        Check if point lies on plane.

        Args:
            point: Point to check
            tolerance: Distance tolerance

        Returns:
            True if point is on plane
        """
        return abs(self.distance_to_point(point)) <= tolerance

    def is_point_above(self, point: Point3D) -> bool:
        """
        Check if point is above plane (on normal side).

        Args:
            point: Point to check

        Returns:
            True if point is on normal side
        """
        return self.distance_to_point(point) > 0

    def intersection_with_line(self, line: "Line3D") -> Optional[Point3D]:
        """
        Find intersection with line.

        Args:
            line: Line to intersect

        Returns:
            Intersection point or None if parallel
        """
        return line.intersection_with_plane(self)

    def intersection_with_plane(self, other: "Plane") -> Optional["Line3D"]:
        """
        Find intersection line with another plane.

        Args:
            other: Other plane

        Returns:
            Intersection line or None if parallel
        """
        from src.geometry.line import Line3D

        # Direction of intersection line is cross product of normals
        direction = self.normal.cross(other.normal)

        if direction.length < 1e-10:
            return None  # Planes are parallel

        direction = direction.normalize()

        # Find a point on the intersection line
        # Solve system of two plane equations with z=0 (or x=0, y=0)
        n1, n2 = self.normal, other.normal
        d1, d2 = self.d, other.d

        # Try to find point by setting one coordinate to 0
        # Use the coordinate with smallest absolute normal component
        abs_dir = [abs(direction.x), abs(direction.y), abs(direction.z)]

        if abs_dir[2] >= abs_dir[0] and abs_dir[2] >= abs_dir[1]:
            # Set z = 0, solve for x and y
            denom = n1.x * n2.y - n1.y * n2.x
            if abs(denom) > 1e-10:
                x = (n1.y * d2 - n2.y * d1) / denom
                y = (n2.x * d1 - n1.x * d2) / denom
                point = Point3D(x, y, 0)
            else:
                return None
        elif abs_dir[1] >= abs_dir[0]:
            # Set y = 0, solve for x and z
            denom = n1.x * n2.z - n1.z * n2.x
            if abs(denom) > 1e-10:
                x = (n1.z * d2 - n2.z * d1) / denom
                z = (n2.x * d1 - n1.x * d2) / denom
                point = Point3D(x, 0, z)
            else:
                return None
        else:
            # Set x = 0, solve for y and z
            denom = n1.y * n2.z - n1.z * n2.y
            if abs(denom) > 1e-10:
                y = (n1.z * d2 - n2.z * d1) / denom
                z = (n2.y * d1 - n1.y * d2) / denom
                point = Point3D(0, y, z)
            else:
                return None

        return Line3D(point, point + direction * 1000)  # Return segment

    def flip(self) -> "Plane":
        """
        Create plane with flipped normal.

        Returns:
            Plane with opposite normal
        """
        return Plane(self.point, -self.normal)

    def translate(self, distance: float) -> "Plane":
        """
        Translate plane along its normal.

        Args:
            distance: Translation distance (positive = along normal)

        Returns:
            Translated plane
        """
        new_point = self.point + self.normal * distance
        return Plane(new_point, self.normal)

    def copy(self) -> "Plane":
        """Create a copy of this plane."""
        return Plane(self.point.copy(), self.normal.copy())

    # Factory methods for common planes
    @classmethod
    def xy(cls, z: float = 0) -> "Plane":
        """XY plane at given Z level."""
        return cls(Point3D(0, 0, z), Vector3D.unit_z())

    @classmethod
    def xz(cls, y: float = 0) -> "Plane":
        """XZ plane at given Y position."""
        return cls(Point3D(0, y, 0), Vector3D.unit_y())

    @classmethod
    def yz(cls, x: float = 0) -> "Plane":
        """YZ plane at given X position."""
        return cls(Point3D(x, 0, 0), Vector3D.unit_x())

    @classmethod
    def from_three_points(cls, p1: Point3D, p2: Point3D, p3: Point3D) -> "Plane":
        """
        Create plane from three points.

        Args:
            p1, p2, p3: Three non-collinear points

        Returns:
            Plane through all three points
        """
        v1 = p2 - p1
        v2 = p3 - p1
        normal = v1.cross(v2)

        if normal.length < 1e-10:
            raise ValueError("Points are collinear, cannot define plane")

        return cls(p1, normal)
