"""
Unit tests for geometry module.
"""

import pytest
import math
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.geometry.line import Line3D
from src.geometry.plane import Plane
from src.geometry.transform import Transform


class TestPoint3D:
    """Tests for Point3D class."""

    def test_create_point(self):
        """Test point creation."""
        p = Point3D(1, 2, 3)
        assert p.x == 1
        assert p.y == 2
        assert p.z == 3

    def test_origin(self):
        """Test origin factory method."""
        p = Point3D.origin()
        assert p.x == 0
        assert p.y == 0
        assert p.z == 0

    def test_distance_to(self):
        """Test distance calculation."""
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(3, 4, 0)
        assert p1.distance_to(p2) == 5.0

    def test_midpoint(self):
        """Test midpoint calculation."""
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(10, 10, 10)
        mid = p1.midpoint_to(p2)
        assert mid.x == 5
        assert mid.y == 5
        assert mid.z == 5

    def test_add_vector(self):
        """Test adding vector to point."""
        p = Point3D(1, 2, 3)
        v = Vector3D(10, 20, 30)
        result = p + v
        assert result.x == 11
        assert result.y == 22
        assert result.z == 33

    def test_subtract_point(self):
        """Test subtracting points gives vector."""
        p1 = Point3D(10, 20, 30)
        p2 = Point3D(1, 2, 3)
        v = p1 - p2
        assert isinstance(v, Vector3D)
        assert v.x == 9
        assert v.y == 18
        assert v.z == 27

    def test_equality(self):
        """Test point equality."""
        p1 = Point3D(1, 2, 3)
        p2 = Point3D(1, 2, 3)
        p3 = Point3D(1, 2, 4)
        assert p1 == p2
        assert p1 != p3

    def test_to_tuple(self):
        """Test conversion to tuple."""
        p = Point3D(1, 2, 3)
        assert p.to_tuple() == (1, 2, 3)


class TestVector3D:
    """Tests for Vector3D class."""

    def test_create_vector(self):
        """Test vector creation."""
        v = Vector3D(1, 2, 3)
        assert v.x == 1
        assert v.y == 2
        assert v.z == 3

    def test_length(self):
        """Test vector length."""
        v = Vector3D(3, 4, 0)
        assert v.length == 5.0

    def test_normalize(self):
        """Test vector normalization."""
        v = Vector3D(10, 0, 0)
        n = v.normalize()
        assert abs(n.length - 1.0) < 1e-9
        assert n.x == 1.0
        assert n.y == 0.0
        assert n.z == 0.0

    def test_dot_product(self):
        """Test dot product."""
        v1 = Vector3D(1, 0, 0)
        v2 = Vector3D(1, 0, 0)
        v3 = Vector3D(0, 1, 0)
        assert v1.dot(v2) == 1.0
        assert v1.dot(v3) == 0.0

    def test_cross_product(self):
        """Test cross product."""
        v1 = Vector3D(1, 0, 0)
        v2 = Vector3D(0, 1, 0)
        v3 = v1.cross(v2)
        assert v3.x == 0
        assert v3.y == 0
        assert v3.z == 1

    def test_add_vectors(self):
        """Test vector addition."""
        v1 = Vector3D(1, 2, 3)
        v2 = Vector3D(4, 5, 6)
        v3 = v1 + v2
        assert v3.x == 5
        assert v3.y == 7
        assert v3.z == 9

    def test_scalar_multiply(self):
        """Test scalar multiplication."""
        v = Vector3D(1, 2, 3)
        v2 = v * 2
        assert v2.x == 2
        assert v2.y == 4
        assert v2.z == 6

    def test_is_parallel(self):
        """Test parallel check."""
        v1 = Vector3D(1, 0, 0)
        v2 = Vector3D(2, 0, 0)
        v3 = Vector3D(0, 1, 0)
        assert v1.is_parallel_to(v2)
        assert not v1.is_parallel_to(v3)

    def test_is_perpendicular(self):
        """Test perpendicular check."""
        v1 = Vector3D(1, 0, 0)
        v2 = Vector3D(0, 1, 0)
        v3 = Vector3D(1, 1, 0)
        assert v1.is_perpendicular_to(v2)
        assert not v1.is_perpendicular_to(v3)


class TestLine3D:
    """Tests for Line3D class."""

    def test_create_line(self):
        """Test line creation."""
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(10, 0, 0)
        line = Line3D(p1, p2)
        assert line.length == 10.0

    def test_direction(self):
        """Test line direction."""
        line = Line3D(Point3D(0, 0, 0), Point3D(10, 0, 0))
        d = line.direction
        assert d.x == 1.0
        assert d.y == 0.0
        assert d.z == 0.0

    def test_point_at(self):
        """Test point at parameter."""
        line = Line3D(Point3D(0, 0, 0), Point3D(10, 0, 0))
        mid = line.point_at(0.5)
        assert mid.x == 5
        assert mid.y == 0
        assert mid.z == 0

    def test_closest_point(self):
        """Test closest point on line."""
        line = Line3D(Point3D(0, 0, 0), Point3D(10, 0, 0))
        point = Point3D(5, 5, 0)
        closest = line.closest_point_to(point)
        assert closest.x == 5
        assert closest.y == 0
        assert closest.z == 0


class TestPlane:
    """Tests for Plane class."""

    def test_create_xy_plane(self):
        """Test XY plane creation."""
        plane = Plane.xy()
        assert plane.normal.x == 0
        assert plane.normal.y == 0
        assert plane.normal.z == 1

    def test_distance_to_point(self):
        """Test distance from plane to point."""
        plane = Plane.xy(z=0)
        point = Point3D(0, 0, 10)
        assert plane.distance_to_point(point) == 10.0

    def test_project_point(self):
        """Test point projection onto plane."""
        plane = Plane.xy(z=0)
        point = Point3D(5, 5, 10)
        projected = plane.project_point(point)
        assert projected.x == 5
        assert projected.y == 5
        assert projected.z == 0


class TestTransform:
    """Tests for Transform class."""

    def test_identity(self):
        """Test identity transform."""
        t = Transform.identity()
        p = Point3D(1, 2, 3)
        result = t.apply_to_point(p)
        assert result == p

    def test_translation(self):
        """Test translation transform."""
        t = Transform.translation(10, 20, 30)
        p = Point3D(0, 0, 0)
        result = t.apply_to_point(p)
        assert result.x == 10
        assert result.y == 20
        assert result.z == 30

    def test_rotation_z(self):
        """Test rotation around Z axis."""
        t = Transform.rotation_z(90)
        p = Point3D(1, 0, 0)
        result = t.apply_to_point(p)
        assert abs(result.x - 0) < 1e-6
        assert abs(result.y - 1) < 1e-6
        assert abs(result.z - 0) < 1e-6

    def test_scale(self):
        """Test scaling transform."""
        t = Transform.scale(2, 2, 2)
        p = Point3D(1, 1, 1)
        result = t.apply_to_point(p)
        assert result.x == 2
        assert result.y == 2
        assert result.z == 2

    def test_compose(self):
        """Test transform composition."""
        t1 = Transform.translation(10, 0, 0)
        t2 = Transform.scale(2, 2, 2)
        combined = t1.compose(t2)

        p = Point3D(0, 0, 0)
        result = combined.apply_to_point(p)
        # First translate, then scale
        assert result.x == 20
