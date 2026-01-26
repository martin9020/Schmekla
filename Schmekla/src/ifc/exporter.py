"""
IFC Exporter for Schmekla.

Exports structural models to IFC2X3 format for Tekla import.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID
from loguru import logger

from src.core.model import StructuralModel
from src.core.element import StructuralElement, ElementType


class IFCExporter:
    """
    Export Schmekla model to IFC2X3 format.

    Creates IFC files compatible with Tekla Structures import.
    """

    def __init__(self, model: StructuralModel):
        """
        Initialize exporter.

        Args:
            model: Schmekla model to export
        """
        self.model = model
        self.ifc = None
        self._element_map: Dict[UUID, Any] = {}

        # IFC entities
        self.project = None
        self.site = None
        self.building = None
        self.storey = None
        self.body_context = None

    def export(self, file_path: str, schema: str = "IFC2X3"):
        """
        Export model to IFC file.

        Args:
            file_path: Output file path
            schema: IFC schema version (IFC2X3 recommended for Tekla)
        """
        try:
            import ifcopenshell
            import ifcopenshell.api
        except ImportError:
            logger.error("ifcopenshell not installed")
            raise ImportError("Please install ifcopenshell: pip install ifcopenshell")

        logger.info(f"Starting IFC export to {file_path}")

        # Create new IFC file
        self.ifc = ifcopenshell.file(schema=schema)

        # Setup project structure
        self._create_project_structure()

        # Setup units
        self._setup_units()

        # Setup geometry contexts
        self._setup_contexts()

        # Export grids (if any)
        self._export_grids()

        # Export elements
        element_count = 0
        for element in self.model.get_all_elements():
            try:
                self._export_element(element)
                element_count += 1
            except Exception as e:
                logger.warning(f"Failed to export element {element.id}: {e}")

        # Write to file
        self.ifc.write(file_path)

        logger.info(f"Exported {element_count} elements to {file_path}")

    def _create_project_structure(self):
        """Create IFC project, site, building, storey hierarchy."""
        import ifcopenshell.api

        # Create owner history first (required by ifcopenshell)
        self._create_owner_history()

        # Create project
        self.project = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcProject",
            name=self.model.name
        )

        # Create site
        self.site = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcSite",
            name="Site"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.project,
            products=[self.site]
        )

        # Create building
        self.building = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcBuilding",
            name="Building"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.site,
            products=[self.building]
        )

        # Create default storey
        self.storey = ifcopenshell.api.run(
            "root.create_entity", self.ifc,
            ifc_class="IfcBuildingStorey",
            name="Ground Floor"
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", self.ifc,
            relating_object=self.building,
            products=[self.storey]
        )

        logger.debug("Created IFC project structure")

    def _create_owner_history(self):
        """Create owner history (required by ifcopenshell API)."""
        import ifcopenshell.api

        # Create application (using correct parameter names)
        application = ifcopenshell.api.run(
            "owner.add_application", self.ifc,
            application_developer=None,
            application_full_name="Schmekla Structural Modeler",
            application_identifier="Schmekla",
            version="0.1.0"
        )

        # Create person
        person = ifcopenshell.api.run(
            "owner.add_person", self.ifc,
            identification=self.model.author or "User",
            family_name=self.model.author or "User",
            given_name=""
        )

        # Create organization
        organisation = ifcopenshell.api.run(
            "owner.add_organisation", self.ifc,
            identification="ORG",
            name="Organization"
        )

        # Create person and organization
        person_org = ifcopenshell.api.run(
            "owner.add_person_and_organisation", self.ifc,
            person=person,
            organisation=organisation
        )

        # Create owner history
        ifcopenshell.api.run(
            "owner.create_owner_history", self.ifc
        )

        logger.debug("Created IFC owner history")

    def _setup_units(self):
        """Setup IFC units (millimeters)."""
        import ifcopenshell.api

        ifcopenshell.api.run(
            "unit.assign_unit", self.ifc,
            length={"is_metric": True, "raw": "MILLIMETRE"},
            area={"is_metric": True, "raw": "SQUARE_METRE"},
            volume={"is_metric": True, "raw": "CUBIC_METRE"}
        )

        logger.debug("Set IFC units to millimeters")

    def _setup_contexts(self):
        """Setup geometric representation contexts."""
        import ifcopenshell.api

        self.body_context = ifcopenshell.api.run(
            "context.add_context", self.ifc,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW"
        )

        logger.debug("Created IFC geometry context")

    def _export_element(self, element: StructuralElement):
        """
        Export single element to IFC.

        Args:
            element: Element to export
        """
        import ifcopenshell.api

        # Get IFC entity from element
        ifc_entity = element.to_ifc(self)

        if ifc_entity is None:
            logger.warning(f"No IFC entity created for {element.id}")
            return

        self._element_map[element.id] = ifc_entity

        # Assign to storey
        ifcopenshell.api.run(
            "spatial.assign_container", self.ifc,
            relating_structure=self.storey,
            products=[ifc_entity]
        )

        # Assign material
        if element.material:
            self._assign_material(ifc_entity, element.material)

        logger.debug(f"Exported element {element.id}")

    def _assign_material(self, ifc_entity, material):
        """Assign material to IFC entity."""
        import ifcopenshell.api

        ifc_material = ifcopenshell.api.run(
            "material.add_material", self.ifc,
            name=material.name
        )

        ifcopenshell.api.run(
            "material.assign_material", self.ifc,
            products=[ifc_entity],
            material=ifc_material
        )

    def _export_grids(self):
        """Export grid lines to IFC."""
        # TODO: Implement grid export
        pass

    def create_axis_placement(self, point, direction=None, ref_direction=None):
        """
        Create IFC axis placement at point.

        Args:
            point: Origin point
            direction: Z-axis direction (optional)
            ref_direction: X-axis direction (optional)

        Returns:
            IfcAxis2Placement3D
        """
        location = self.ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=[point.x, point.y, point.z]
        )

        if direction is None and ref_direction is None:
            return self.ifc.create_entity(
                "IfcAxis2Placement3D",
                Location=location
            )

        axis = None
        if direction is not None:
            d = direction.normalize()
            axis = self.ifc.create_entity(
                "IfcDirection",
                DirectionRatios=[d.x, d.y, d.z]
            )

        ref = None
        if ref_direction is not None:
            r = ref_direction.normalize()
            ref = self.ifc.create_entity(
                "IfcDirection",
                DirectionRatios=[r.x, r.y, r.z]
            )

        return self.ifc.create_entity(
            "IfcAxis2Placement3D",
            Location=location,
            Axis=axis,
            RefDirection=ref
        )

    def create_local_placement(self, point, relative_to=None):
        """
        Create IFC local placement.

        Args:
            point: Placement origin
            relative_to: Parent placement (optional)

        Returns:
            IfcLocalPlacement
        """
        axis_placement = self.create_axis_placement(point)

        return self.ifc.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=axis_placement,
            PlacementRelTo=relative_to
        )

    def create_direction(self, vector):
        """Create IFC direction from vector."""
        v = vector.normalize()
        return self.ifc.create_entity(
            "IfcDirection",
            DirectionRatios=[v.x, v.y, v.z]
        )
