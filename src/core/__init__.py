"""
Core module for Schmekla.

Contains data models for structural elements, materials, profiles, and the main model.
"""

from src.core.element import StructuralElement, ElementType
from src.core.model import StructuralModel, Command, AddElementCommand, RemoveElementCommand
from src.core.profile import Profile, ProfileType, ProfileCatalog
from src.core.material import Material, MaterialCatalog
from src.core.beam import Beam
from src.core.curved_beam import CurvedBeam, create_barrel_hoop
from src.core.column import Column
from src.core.plate import Plate
from src.core.slab import Slab
from src.core.wall import Wall
from src.core.footing import Footing

__all__ = [
    # Base classes
    "StructuralElement",
    "ElementType",
    "StructuralModel",
    "Command",
    "AddElementCommand",
    "RemoveElementCommand",
    # Profiles and Materials
    "Profile",
    "ProfileType",
    "ProfileCatalog",
    "Material",
    "MaterialCatalog",
    # Element types
    "Beam",
    "CurvedBeam",
    "create_barrel_hoop",
    "Column",
    "Plate",
    "Slab",
    "Wall",
    "Footing",
]
