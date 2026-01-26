"""
Material definitions for Schmekla.

Defines structural materials with mechanical properties.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from pathlib import Path
import json
from loguru import logger


@dataclass
class Material:
    """
    Structural material with mechanical properties.

    All values in SI units unless noted.
    """
    name: str
    description: str = ""

    # Mechanical properties
    density: float = 7850.0          # kg/m^3 (steel default)
    elastic_modulus: float = 210000.0  # MPa (N/mm^2)
    poisson_ratio: float = 0.3
    yield_strength: float = 355.0    # MPa
    ultimate_strength: float = 470.0  # MPa
    thermal_expansion: float = 12e-6  # per degree C

    # Display properties
    color: tuple = (0.7, 0.7, 0.7)   # RGB 0-1
    transparency: float = 0.0        # 0 = opaque, 1 = transparent

    # Material category
    category: str = "Steel"          # Steel, Concrete, Timber, etc.

    def to_ifc_material(self, ifc_model):
        """
        Create IFC material entity.

        Args:
            ifc_model: IFC model instance

        Returns:
            IfcMaterial entity
        """
        import ifcopenshell.api

        # Create material
        material = ifcopenshell.api.run(
            "material.add_material",
            ifc_model.ifc,
            name=self.name
        )

        # Add material properties
        pset = ifcopenshell.api.run(
            "pset.add_pset",
            ifc_model.ifc,
            product=material,
            name="Pset_MaterialCommon"
        )

        ifcopenshell.api.run(
            "pset.edit_pset",
            ifc_model.ifc,
            pset=pset,
            properties={
                "MassDensity": self.density,
            }
        )

        # Add mechanical properties
        mech_pset = ifcopenshell.api.run(
            "pset.add_pset",
            ifc_model.ifc,
            product=material,
            name="Pset_MaterialMechanical"
        )

        ifcopenshell.api.run(
            "pset.edit_pset",
            ifc_model.ifc,
            pset=mech_pset,
            properties={
                "YoungModulus": self.elastic_modulus * 1e6,  # Convert to Pa
                "PoissonRatio": self.poisson_ratio,
            }
        )

        return material

    @classmethod
    def default_steel(cls) -> "Material":
        """Create default structural steel (S355)."""
        return cls(
            name="S355",
            description="Structural steel grade S355",
            density=7850,
            elastic_modulus=210000,
            yield_strength=355,
            ultimate_strength=470,
            category="Steel",
            color=(0.6, 0.6, 0.65)
        )

    @classmethod
    def default_concrete(cls) -> "Material":
        """Create default concrete (C30/37)."""
        return cls(
            name="C30/37",
            description="Concrete grade C30/37",
            density=2400,
            elastic_modulus=33000,
            poisson_ratio=0.2,
            yield_strength=30,  # Compressive
            ultimate_strength=37,
            category="Concrete",
            color=(0.7, 0.7, 0.7)
        )

    @classmethod
    def from_name(cls, name: str) -> "Material":
        """
        Get material by name from catalog.

        Args:
            name: Material name

        Returns:
            Material instance
        """
        catalog = MaterialCatalog.get_instance()
        material = catalog.get_material(name)
        if material is None:
            logger.warning(f"Material '{name}' not found, using default steel")
            return cls.default_steel()
        return material


class MaterialCatalog:
    """
    Catalog of available materials.

    Singleton pattern for global access.
    """
    _instance: Optional["MaterialCatalog"] = None

    def __init__(self):
        self._materials: Dict[str, Material] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "MaterialCatalog":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_catalog(self, catalog_path: Path = None):
        """Load material catalog from JSON file."""
        if catalog_path is None:
            catalog_path = Path(__file__).parent.parent.parent / "resources" / "materials" / "materials.json"

        if not catalog_path.exists():
            logger.warning(f"Material catalog not found: {catalog_path}")
            self._create_default_materials()
            return

        try:
            with open(catalog_path, "r") as f:
                data = json.load(f)

            for name, props in data.items():
                material = Material(
                    name=name,
                    description=props.get("description", ""),
                    density=props.get("density", 7850),
                    elastic_modulus=props.get("elastic_modulus", 210000),
                    poisson_ratio=props.get("poisson_ratio", 0.3),
                    yield_strength=props.get("yield_strength", 355),
                    ultimate_strength=props.get("ultimate_strength", 470),
                    category=props.get("category", "Steel"),
                    color=tuple(props.get("color", [0.7, 0.7, 0.7])),
                )
                self._materials[name] = material

            self._loaded = True
            logger.info(f"Loaded {len(self._materials)} materials from {catalog_path}")

        except Exception as e:
            logger.error(f"Failed to load material catalog: {e}")
            self._create_default_materials()

    def _create_default_materials(self):
        """Create default materials."""
        defaults = [
            Material.default_steel(),
            Material(name="S275", description="Structural steel S275", yield_strength=275, category="Steel"),
            Material(name="S235", description="Structural steel S235", yield_strength=235, category="Steel"),
            Material.default_concrete(),
            Material(name="C40/50", description="Concrete C40/50", density=2400, elastic_modulus=35000, yield_strength=40, category="Concrete"),
        ]

        for mat in defaults:
            self._materials[mat.name] = mat

        self._loaded = True
        logger.info(f"Created {len(self._materials)} default materials")

    def get_material(self, name: str) -> Optional[Material]:
        """Get material by name."""
        if not self._loaded:
            self.load_catalog()
        return self._materials.get(name)

    def get_all_materials(self) -> List[Material]:
        """Get all materials."""
        if not self._loaded:
            self.load_catalog()
        return list(self._materials.values())

    def get_materials_by_category(self, category: str) -> List[Material]:
        """Get materials of specific category."""
        if not self._loaded:
            self.load_catalog()
        return [m for m in self._materials.values() if m.category == category]

    def get_material_names(self) -> List[str]:
        """Get list of all material names."""
        if not self._loaded:
            self.load_catalog()
        return list(self._materials.keys())
