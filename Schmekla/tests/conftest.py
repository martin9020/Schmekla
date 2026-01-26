"""
Pytest configuration and fixtures for Schmekla tests.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


@pytest.fixture
def model():
    """Create a fresh StructuralModel for testing."""
    from src.core.model import StructuralModel
    return StructuralModel()


@pytest.fixture
def sample_beam():
    """Create a sample beam for testing."""
    from src.core.beam import Beam
    from src.core.profile import Profile
    from src.core.material import Material
    from src.geometry.point import Point3D

    return Beam(
        start_point=Point3D(0, 0, 0),
        end_point=Point3D(6000, 0, 0),
        profile=Profile.from_name("UB 305x165x40"),
        material=Material.default_steel(),
        name="Test Beam"
    )


@pytest.fixture
def point_at_origin():
    """Point at origin."""
    from src.geometry.point import Point3D
    return Point3D(0, 0, 0)


@pytest.fixture
def unit_vector_x():
    """Unit vector in X direction."""
    from src.geometry.vector import Vector3D
    return Vector3D(1, 0, 0)
