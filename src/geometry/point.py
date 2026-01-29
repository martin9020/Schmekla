"""
3D Point class for Schmekla.

Represents a point in 3D space with full coordinate operations.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, Tuple, Union
import numpy as np

if TYPE_CHECKING:
    from src.geometry.vector import Vector3D
    from src.geometry.transform import Transform


class Point3D:
    """
    3D point with full coordinate operations.

    All coordinates are stored in millimeters (mm).
    """

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """
        Create a 3D point.

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            z: Z coordinate in mm
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self) -> str:
        return f"Point3D({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def __str__(self) -> str:
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point3D):
            return False
        return (
            math.isclose(self.x, other.x, abs_tol=1e-9)
            and math.isclose(self.y, other.y, abs_tol=1e-9)
            and math.isclose(self.z, other.z, abs_tol=1e-9)
        )

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6), round(self.z, 6)))

    def __add__(self, other: "Vector3D") -> "Point3D":
        """Add a vector to this point, returning a new point."""
        from src.geometry.vector import Vector3D
        if not isinstance(other, Vector3D):
            raise TypeError(f"Cannot add {type(other)} to Point3D")
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Union["Point3D", "Vector3D"]) -> Union["Vector3D", "Point3D"]:
        """
        Subtract from this point.

        Point - Point = Vector (displacement between points)
        Point - Vector = Point (move point by negative vector)
        """
        from src.geometry.vector import Vector3D
        if isinstance(other, Point3D):
            return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, Vector3D):
            return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)
        raise TypeError(f"Cannot subtract {type(other)} from Point3D")

    def __neg__(self) -> "Point3D":
        """Negate point coordinates."""
        return Point3D(-self.x, -self.y, -self.z)

    def distance_to(self, other: "Point3D") -> float:
        """
        Calculate distance to another point.

        Args:
            other: Target point

        Returns:
            Distance in mm
        """
        dx = other.x - self.x
        dy = other.y - self.y
        dz = other.z - self.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def midpoint_to(self, other: "Point3D") -> "Point3D":
        """
        Calculate midpoint between this point and another.

        Args:
            other: Other point

        Returns:
            Midpoint
        """
        return Point3D(
            (self.x + other.x) / 2,
            (self.y + other.y) / 2,
            (self.z + other.z) / 2,
        )

    def interpolate_to(self, other: "Point3D", t: float) -> "Point3D":
        """
        Linear interpolation to another point.

        Args:
            other: Target point
            t: Interpolation parameter (0=self, 1=other)

        Returns:
            Interpolated point
        """
        return Point3D(
            self.x + t * (other.x - self.x),
            self.y + t * (other.y - self.y),
            self.z + t * (other.z - self.z),
        )

    def transform(self, matrix: "Transform") -> "Point3D":
        """
        Apply transformation matrix to this point.

        Args:
            matrix: 4x4 transformation matrix

        Returns:
            Transformed point
        """
        return matrix.apply_to_point(self)

    def translate(self, dx: float = 0, dy: float = 0, dz: float = 0) -> "Point3D":
        """
        Create a translated copy of this point.

        Args:
            dx: X translation
            dy: Y translation
            dz: Z translation

        Returns:
            New translated point
        """
        return Point3D(self.x + dx, self.y + dy, self.z + dz)

    def rotate_around_z(self, angle_deg: float, center: "Point3D" = None) -> "Point3D":
        """
        Rotate point around Z axis.

        Args:
            angle_deg: Rotation angle in degrees
            center: Center of rotation (defaults to origin)

        Returns:
            Rotated point
        """
        if center is None:
            center = Point3D.origin()

        # Translate to origin
        px = self.x - center.x
        py = self.y - center.y

        # Rotate
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a

        # Translate back
        return Point3D(rx + center.x, ry + center.y, self.z)

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    def to_list(self) -> list:
        """Convert to list."""
        return [self.x, self.y, self.z]

    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])

    def to_occ(self):
        """
        Convert to OpenCascade gp_Pnt.

        Returns:
            OCC.Core.gp.gp_Pnt
        """
        try:
            from OCP.gp import gp_Pnt
            return gp_Pnt(self.x, self.y, self.z)
        except ImportError:
            raise ImportError("OpenCascade (OCC) not available")

    def copy(self) -> "Point3D":
        """Create a copy of this point."""
        return Point3D(self.x, self.y, self.z)

    def is_close_to(self, other: "Point3D", tolerance: float = 1e-6) -> bool:
        """
        Check if this point is close to another within tolerance.

        Args:
            other: Point to compare
            tolerance: Distance tolerance in mm

        Returns:
            True if points are within tolerance
        """
        return self.distance_to(other) <= tolerance

    # Class methods for common points
    @classmethod
    def origin(cls) -> "Point3D":
        """Create point at origin (0, 0, 0)."""
        return cls(0, 0, 0)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float]) -> "Point3D":
        """Create point from tuple."""
        return cls(coords[0], coords[1], coords[2])

    @classmethod
    def from_list(cls, coords: list) -> "Point3D":
        """Create point from list."""
        return cls(coords[0], coords[1], coords[2] if len(coords) > 2 else 0)

    @classmethod
    def from_array(cls, arr: np.ndarray) -> "Point3D":
        """Create point from numpy array."""
        return cls(float(arr[0]), float(arr[1]), float(arr[2]) if len(arr) > 2 else 0)

    @classmethod
    def from_occ(cls, occ_pnt) -> "Point3D":
        """
        Create from OpenCascade gp_Pnt.

        Args:
            occ_pnt: OCC.Core.gp.gp_Pnt

        Returns:
            Point3D
        """
        return cls(occ_pnt.X(), occ_pnt.Y(), occ_pnt.Z())
