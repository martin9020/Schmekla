"""
3D Vector class for Schmekla.

Represents a direction and magnitude in 3D space.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, Tuple, Union
import numpy as np

if TYPE_CHECKING:
    from src.geometry.point import Point3D


class Vector3D:
    """
    3D vector with full vector operations.

    Represents a direction and magnitude in 3D space.
    """

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """
        Create a 3D vector.

        Args:
            x: X component
            y: Y component
            z: Z component
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self) -> str:
        return f"Vector3D({self.x:.4f}, {self.y:.4f}, {self.z:.4f})"

    def __str__(self) -> str:
        return f"<{self.x:.4f}, {self.y:.4f}, {self.z:.4f}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3D):
            return False
        return (
            math.isclose(self.x, other.x, abs_tol=1e-9)
            and math.isclose(self.y, other.y, abs_tol=1e-9)
            and math.isclose(self.z, other.z, abs_tol=1e-9)
        )

    def __hash__(self) -> int:
        return hash((round(self.x, 6), round(self.y, 6), round(self.z, 6)))

    def __add__(self, other: "Vector3D") -> "Vector3D":
        """Add two vectors."""
        if not isinstance(other, Vector3D):
            raise TypeError(f"Cannot add {type(other)} to Vector3D")
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3D") -> "Vector3D":
        """Subtract two vectors."""
        if not isinstance(other, Vector3D):
            raise TypeError(f"Cannot subtract {type(other)} from Vector3D")
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3D":
        """Multiply vector by scalar."""
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vector3D":
        """Right multiply by scalar."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector3D":
        """Divide vector by scalar."""
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> "Vector3D":
        """Negate vector."""
        return Vector3D(-self.x, -self.y, -self.z)

    @property
    def length(self) -> float:
        """Calculate vector length (magnitude)."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def length_squared(self) -> float:
        """Calculate squared length (avoids sqrt for comparisons)."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    def normalize(self) -> "Vector3D":
        """
        Return unit vector in same direction.

        Returns:
            Normalized vector with length 1
        """
        length = self.length
        if length < 1e-10:
            return Vector3D.zero()
        return Vector3D(self.x / length, self.y / length, self.z / length)

    def dot(self, other: "Vector3D") -> float:
        """
        Calculate dot product with another vector.

        Args:
            other: Other vector

        Returns:
            Dot product (scalar)
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vector3D") -> "Vector3D":
        """
        Calculate cross product with another vector.

        Args:
            other: Other vector

        Returns:
            Cross product vector (perpendicular to both)
        """
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def angle_to(self, other: "Vector3D") -> float:
        """
        Calculate angle between this vector and another.

        Args:
            other: Other vector

        Returns:
            Angle in degrees
        """
        len_self = self.length
        len_other = other.length

        if len_self < 1e-10 or len_other < 1e-10:
            return 0.0

        cos_angle = self.dot(other) / (len_self * len_other)
        # Clamp to avoid floating point errors in acos
        cos_angle = max(-1.0, min(1.0, cos_angle))
        return math.degrees(math.acos(cos_angle))

    def project_onto(self, other: "Vector3D") -> "Vector3D":
        """
        Project this vector onto another vector.

        Args:
            other: Vector to project onto

        Returns:
            Projected vector
        """
        other_length_sq = other.length_squared
        if other_length_sq < 1e-10:
            return Vector3D.zero()
        scalar = self.dot(other) / other_length_sq
        return other * scalar

    def is_parallel_to(self, other: "Vector3D", tolerance: float = 1e-6) -> bool:
        """
        Check if this vector is parallel to another.

        Args:
            other: Vector to compare
            tolerance: Angular tolerance

        Returns:
            True if parallel (or anti-parallel)
        """
        cross = self.cross(other)
        return cross.length < tolerance

    def is_perpendicular_to(self, other: "Vector3D", tolerance: float = 1e-6) -> bool:
        """
        Check if this vector is perpendicular to another.

        Args:
            other: Vector to compare
            tolerance: Dot product tolerance

        Returns:
            True if perpendicular
        """
        return abs(self.dot(other)) < tolerance

    def rotate_around_axis(self, axis: "Vector3D", angle_deg: float) -> "Vector3D":
        """
        Rotate vector around an axis using Rodrigues' rotation formula.

        Args:
            axis: Axis of rotation (will be normalized)
            angle_deg: Rotation angle in degrees

        Returns:
            Rotated vector
        """
        angle_rad = math.radians(angle_deg)
        k = axis.normalize()

        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Rodrigues' rotation formula: v' = v*cos(a) + (k x v)*sin(a) + k*(k.v)*(1-cos(a))
        term1 = self * cos_a
        term2 = k.cross(self) * sin_a
        term3 = k * (k.dot(self) * (1 - cos_a))

        return term1 + term2 + term3

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    def to_list(self) -> list:
        """Convert to list."""
        return [self.x, self.y, self.z]

    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])

    def to_occ_dir(self):
        """
        Convert to OpenCascade gp_Dir.

        Returns:
            OCC.Core.gp.gp_Dir
        """
        try:
            from OCC.Core.gp import gp_Dir
            normalized = self.normalize()
            return gp_Dir(normalized.x, normalized.y, normalized.z)
        except ImportError:
            raise ImportError("OpenCascade (OCC) not available")

    def to_occ_vec(self):
        """
        Convert to OpenCascade gp_Vec.

        Returns:
            OCC.Core.gp.gp_Vec
        """
        try:
            from OCC.Core.gp import gp_Vec
            return gp_Vec(self.x, self.y, self.z)
        except ImportError:
            raise ImportError("OpenCascade (OCC) not available")

    def copy(self) -> "Vector3D":
        """Create a copy of this vector."""
        return Vector3D(self.x, self.y, self.z)

    # Class methods for common vectors
    @classmethod
    def zero(cls) -> "Vector3D":
        """Zero vector."""
        return cls(0, 0, 0)

    @classmethod
    def unit_x(cls) -> "Vector3D":
        """Unit vector in X direction."""
        return cls(1, 0, 0)

    @classmethod
    def unit_y(cls) -> "Vector3D":
        """Unit vector in Y direction."""
        return cls(0, 1, 0)

    @classmethod
    def unit_z(cls) -> "Vector3D":
        """Unit vector in Z direction."""
        return cls(0, 0, 1)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float]) -> "Vector3D":
        """Create vector from tuple."""
        return cls(coords[0], coords[1], coords[2])

    @classmethod
    def from_points(cls, start: "Point3D", end: "Point3D") -> "Vector3D":
        """
        Create vector from start point to end point.

        Args:
            start: Start point
            end: End point

        Returns:
            Vector from start to end
        """
        return cls(end.x - start.x, end.y - start.y, end.z - start.z)

    @classmethod
    def from_occ_dir(cls, occ_dir) -> "Vector3D":
        """Create from OpenCascade gp_Dir."""
        return cls(occ_dir.X(), occ_dir.Y(), occ_dir.Z())

    @classmethod
    def from_occ_vec(cls, occ_vec) -> "Vector3D":
        """Create from OpenCascade gp_Vec."""
        return cls(occ_vec.X(), occ_vec.Y(), occ_vec.Z())
