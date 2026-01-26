"""
Transformation matrix class for Schmekla.

Represents 4x4 transformation matrices for 3D operations.
"""

from __future__ import annotations
import math
from typing import Tuple
import numpy as np
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D


class Transform:
    """
    4x4 transformation matrix for 3D transformations.

    Supports translation, rotation, and scaling.
    Matrix is stored in row-major order.
    """

    def __init__(self, matrix: np.ndarray = None):
        """
        Create transformation matrix.

        Args:
            matrix: 4x4 numpy array, or None for identity
        """
        if matrix is None:
            self._matrix = np.eye(4, dtype=np.float64)
        else:
            if matrix.shape != (4, 4):
                raise ValueError("Transform matrix must be 4x4")
            self._matrix = matrix.astype(np.float64)

    def __repr__(self) -> str:
        return f"Transform(\n{self._matrix})"

    def __matmul__(self, other: "Transform") -> "Transform":
        """Matrix multiplication."""
        return Transform(self._matrix @ other._matrix)

    @property
    def matrix(self) -> np.ndarray:
        """Get the 4x4 transformation matrix."""
        return self._matrix.copy()

    @property
    def inverse(self) -> "Transform":
        """Get inverse transformation."""
        return Transform(np.linalg.inv(self._matrix))

    def apply_to_point(self, point: Point3D) -> Point3D:
        """
        Apply transformation to a point.

        Args:
            point: Point to transform

        Returns:
            Transformed point
        """
        p = np.array([point.x, point.y, point.z, 1.0])
        result = self._matrix @ p
        return Point3D(result[0], result[1], result[2])

    def apply_to_vector(self, vector: Vector3D) -> Vector3D:
        """
        Apply transformation to a vector (ignores translation).

        Args:
            vector: Vector to transform

        Returns:
            Transformed vector
        """
        v = np.array([vector.x, vector.y, vector.z, 0.0])
        result = self._matrix @ v
        return Vector3D(result[0], result[1], result[2])

    def apply_to_points(self, points: list) -> list:
        """
        Apply transformation to multiple points.

        Args:
            points: List of Point3D

        Returns:
            List of transformed Point3D
        """
        return [self.apply_to_point(p) for p in points]

    def compose(self, other: "Transform") -> "Transform":
        """
        Compose with another transformation.

        Args:
            other: Transformation to apply after this one

        Returns:
            Combined transformation
        """
        return Transform(other._matrix @ self._matrix)

    # Factory methods for common transformations
    @classmethod
    def identity(cls) -> "Transform":
        """Identity transformation (no change)."""
        return cls()

    @classmethod
    def translation(cls, dx: float = 0, dy: float = 0, dz: float = 0) -> "Transform":
        """
        Create translation transformation.

        Args:
            dx, dy, dz: Translation in each axis

        Returns:
            Translation transform
        """
        matrix = np.eye(4, dtype=np.float64)
        matrix[0, 3] = dx
        matrix[1, 3] = dy
        matrix[2, 3] = dz
        return cls(matrix)

    @classmethod
    def translation_vec(cls, vector: Vector3D) -> "Transform":
        """Create translation from vector."""
        return cls.translation(vector.x, vector.y, vector.z)

    @classmethod
    def rotation_x(cls, angle_deg: float) -> "Transform":
        """
        Create rotation around X axis.

        Args:
            angle_deg: Rotation angle in degrees

        Returns:
            Rotation transform
        """
        angle_rad = math.radians(angle_deg)
        c, s = math.cos(angle_rad), math.sin(angle_rad)

        matrix = np.eye(4, dtype=np.float64)
        matrix[1, 1] = c
        matrix[1, 2] = -s
        matrix[2, 1] = s
        matrix[2, 2] = c

        return cls(matrix)

    @classmethod
    def rotation_y(cls, angle_deg: float) -> "Transform":
        """
        Create rotation around Y axis.

        Args:
            angle_deg: Rotation angle in degrees

        Returns:
            Rotation transform
        """
        angle_rad = math.radians(angle_deg)
        c, s = math.cos(angle_rad), math.sin(angle_rad)

        matrix = np.eye(4, dtype=np.float64)
        matrix[0, 0] = c
        matrix[0, 2] = s
        matrix[2, 0] = -s
        matrix[2, 2] = c

        return cls(matrix)

    @classmethod
    def rotation_z(cls, angle_deg: float) -> "Transform":
        """
        Create rotation around Z axis.

        Args:
            angle_deg: Rotation angle in degrees

        Returns:
            Rotation transform
        """
        angle_rad = math.radians(angle_deg)
        c, s = math.cos(angle_rad), math.sin(angle_rad)

        matrix = np.eye(4, dtype=np.float64)
        matrix[0, 0] = c
        matrix[0, 1] = -s
        matrix[1, 0] = s
        matrix[1, 1] = c

        return cls(matrix)

    @classmethod
    def rotation_axis(cls, axis: Vector3D, angle_deg: float) -> "Transform":
        """
        Create rotation around arbitrary axis.

        Args:
            axis: Axis of rotation (will be normalized)
            angle_deg: Rotation angle in degrees

        Returns:
            Rotation transform
        """
        angle_rad = math.radians(angle_deg)
        axis = axis.normalize()

        c = math.cos(angle_rad)
        s = math.sin(angle_rad)
        t = 1 - c

        x, y, z = axis.x, axis.y, axis.z

        matrix = np.array([
            [t*x*x + c,   t*x*y - s*z, t*x*z + s*y, 0],
            [t*x*y + s*z, t*y*y + c,   t*y*z - s*x, 0],
            [t*x*z - s*y, t*y*z + s*x, t*z*z + c,   0],
            [0,           0,           0,           1]
        ], dtype=np.float64)

        return cls(matrix)

    @classmethod
    def scale(cls, sx: float = 1, sy: float = 1, sz: float = 1) -> "Transform":
        """
        Create scaling transformation.

        Args:
            sx, sy, sz: Scale factors for each axis

        Returns:
            Scale transform
        """
        matrix = np.eye(4, dtype=np.float64)
        matrix[0, 0] = sx
        matrix[1, 1] = sy
        matrix[2, 2] = sz

        return cls(matrix)

    @classmethod
    def uniform_scale(cls, factor: float) -> "Transform":
        """Create uniform scaling."""
        return cls.scale(factor, factor, factor)

    @classmethod
    def mirror_xy(cls) -> "Transform":
        """Mirror across XY plane (negate Z)."""
        return cls.scale(1, 1, -1)

    @classmethod
    def mirror_xz(cls) -> "Transform":
        """Mirror across XZ plane (negate Y)."""
        return cls.scale(1, -1, 1)

    @classmethod
    def mirror_yz(cls) -> "Transform":
        """Mirror across YZ plane (negate X)."""
        return cls.scale(-1, 1, 1)

    @classmethod
    def from_origin_and_axes(
        cls,
        origin: Point3D,
        x_axis: Vector3D,
        y_axis: Vector3D,
        z_axis: Vector3D = None
    ) -> "Transform":
        """
        Create transformation from local coordinate system.

        Args:
            origin: Origin point of local system
            x_axis: Local X axis direction
            y_axis: Local Y axis direction
            z_axis: Local Z axis direction (computed if not provided)

        Returns:
            Transform from global to local coordinates
        """
        x = x_axis.normalize()
        y = y_axis.normalize()

        if z_axis is None:
            z = x.cross(y).normalize()
        else:
            z = z_axis.normalize()

        matrix = np.array([
            [x.x, y.x, z.x, origin.x],
            [x.y, y.y, z.y, origin.y],
            [x.z, y.z, z.z, origin.z],
            [0,   0,   0,   1]
        ], dtype=np.float64)

        return cls(matrix)

    @classmethod
    def look_at(cls, eye: Point3D, target: Point3D, up: Vector3D = None) -> "Transform":
        """
        Create view transformation (look-at matrix).

        Args:
            eye: Camera/eye position
            target: Look-at target point
            up: Up direction (defaults to Z up)

        Returns:
            View transform
        """
        if up is None:
            up = Vector3D.unit_z()

        z_axis = (eye - target)
        if z_axis.length < 1e-10:
            z_axis = Vector3D.unit_z()
        z_axis = z_axis.normalize()

        x_axis = up.cross(z_axis).normalize()
        y_axis = z_axis.cross(x_axis).normalize()

        return cls.from_origin_and_axes(eye, x_axis, y_axis, z_axis)

    def get_translation(self) -> Vector3D:
        """Extract translation component."""
        return Vector3D(self._matrix[0, 3], self._matrix[1, 3], self._matrix[2, 3])

    def get_scale(self) -> Tuple[float, float, float]:
        """Extract scale factors (approximate, assumes no shear)."""
        sx = math.sqrt(self._matrix[0, 0]**2 + self._matrix[1, 0]**2 + self._matrix[2, 0]**2)
        sy = math.sqrt(self._matrix[0, 1]**2 + self._matrix[1, 1]**2 + self._matrix[2, 1]**2)
        sz = math.sqrt(self._matrix[0, 2]**2 + self._matrix[1, 2]**2 + self._matrix[2, 2]**2)
        return (sx, sy, sz)

    def copy(self) -> "Transform":
        """Create a copy of this transform."""
        return Transform(self._matrix.copy())
