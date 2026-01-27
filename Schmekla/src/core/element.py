"""
Base structural element class for Schmekla.

All structural elements (beams, columns, plates, etc.) inherit from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from typing import Any, Dict, Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.material import Material
    from src.core.profile import Profile
    from src.core.numbering import ComparisonConfig, PartSignature
    from src.geometry.point import Point3D
    from src.geometry.vector import Vector3D


class ElementType(Enum):
    """Types of structural elements."""
    BEAM = "beam"
    COLUMN = "column"
    PLATE = "plate"
    SLAB = "slab"
    WALL = "wall"
    FOOTING = "footing"
    BRACE = "brace"
    PURLIN = "purlin"
    GIRT = "girt"


class PositionOnPlane(Enum):
    """Profile position relative to reference line on local XY plane."""
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"


class PositionAtDepth(Enum):
    """Profile position in depth direction."""
    FRONT = "front"
    MIDDLE = "middle"
    BEHIND = "behind"


@dataclass
class EndPointOffsets:
    """Offset values at element endpoint in local coordinates."""
    dx: float = 0.0  # Along element axis
    dy: float = 0.0  # Perpendicular in-plane
    dz: float = 0.0  # Perpendicular out-of-plane

    def is_zero(self) -> bool:
        """Check if all offsets are zero."""
        return self.dx == 0.0 and self.dy == 0.0 and self.dz == 0.0

    def copy(self) -> "EndPointOffsets":
        """Create a copy of these offsets."""
        return EndPointOffsets(self.dx, self.dy, self.dz)


@dataclass
class LocalCoordinateSystem:
    """Local coordinate system for linear element."""
    origin: "Point3D"
    x_axis: "Vector3D"  # Along element
    y_axis: "Vector3D"  # Up direction
    z_axis: "Vector3D"  # Right-hand perpendicular

    def transform_offsets_to_global(self, offsets: EndPointOffsets) -> "Vector3D":
        """Convert local offsets to global vector."""
        from src.geometry.vector import Vector3D
        return Vector3D(
            offsets.dx * self.x_axis.x + offsets.dy * self.y_axis.x + offsets.dz * self.z_axis.x,
            offsets.dx * self.x_axis.y + offsets.dy * self.y_axis.y + offsets.dz * self.z_axis.y,
            offsets.dx * self.x_axis.z + offsets.dy * self.y_axis.z + offsets.dz * self.z_axis.z
        )


class StructuralElement(ABC):
    """
    Base class for all structural elements.

    Provides common functionality for identification, materials, profiles,
    geometry generation, and IFC export.
    """

    def __init__(self):
        """Initialize base element properties."""
        self._id: UUID = uuid4()
        self._name: str = ""
        self._material: Optional["Material"] = None
        self._profile: Optional["Profile"] = None

        # Geometry caching
        self._solid: Optional[Any] = None  # OpenCascade TopoDS_Shape
        self._mesh: Optional[Any] = None   # PyVista mesh for display
        self._dirty: bool = True           # Needs geometry regeneration

        # Metadata
        self._user_attributes: Dict[str, Any] = {}
        self._phase: str = ""
        self._class_number: int = 0

        # Tekla-style numbering
        self._part_number: str = ""
        self._assembly_number: str = ""

        logger.debug(f"Created {self.__class__.__name__} with ID {self._id}")

    @property
    def id(self) -> UUID:
        """Unique identifier for this element."""
        return self._id

    @property
    def name(self) -> str:
        """Element name/mark."""
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def material(self) -> Optional["Material"]:
        """Element material."""
        return self._material

    @material.setter
    def material(self, value: "Material"):
        self._material = value
        self.invalidate()

    @property
    def profile(self) -> Optional["Profile"]:
        """Element profile/section."""
        return self._profile

    @profile.setter
    def profile(self, value: "Profile"):
        self._profile = value
        self.invalidate()

    @property
    def part_number(self) -> str:
        """Element part number (Tekla-style, e.g. B1, C2)."""
        return self._part_number

    @part_number.setter
    def part_number(self, value: str):
        self._part_number = value

    @property
    def assembly_number(self) -> str:
        """Element assembly number."""
        return self._assembly_number

    @assembly_number.setter
    def assembly_number(self, value: str):
        self._assembly_number = value

    @property
    @abstractmethod
    def element_type(self) -> ElementType:
        """Return the element type."""
        pass

    @abstractmethod
    def generate_solid(self) -> Any:
        """
        Generate the 3D solid geometry for this element.

        Returns:
            OpenCascade TopoDS_Shape
        """
        pass

    @abstractmethod
    def to_ifc(self, exporter: "IFCExporter") -> Any:
        """
        Export this element to IFC.

        Args:
            exporter: IFC exporter instance

        Returns:
            IFC entity
        """
        pass

    def get_solid(self) -> Any:
        """
        Get the solid geometry, regenerating if needed.

        Returns:
            OpenCascade TopoDS_Shape
        """
        if self._dirty or self._solid is None:
            logger.debug(f"Regenerating solid for {self._id}")
            self._solid = self.generate_solid()
            self._mesh = None  # Invalidate mesh
            self._dirty = False
        return self._solid

    def get_mesh(self) -> Any:
        """
        Get the display mesh, generating from solid if needed.

        Returns:
            PyVista mesh for visualization
        """
        if self._mesh is None:
            solid = self.get_solid()
            if solid is not None:
                self._mesh = self._tessellate(solid)
        return self._mesh

    def _tessellate(self, solid: Any) -> Any:
        """
        Convert solid geometry to display mesh.

        Args:
            solid: OpenCascade TopoDS_Shape

        Returns:
            PyVista mesh
        """
        try:
            import pyvista as pv
            from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
            from OCC.Core.TopExp import TopExp_Explorer
            from OCC.Core.TopAbs import TopAbs_FACE
            from OCC.Core.BRep import BRep_Tool
            from OCC.Core.TopLoc import TopLoc_Location

            # Mesh the shape
            mesh_algo = BRepMesh_IncrementalMesh(solid, 1.0, False, 0.5, True)
            mesh_algo.Perform()

            # Extract triangles from faces
            vertices = []
            faces = []
            vertex_offset = 0

            explorer = TopExp_Explorer(solid, TopAbs_FACE)
            while explorer.More():
                face = explorer.Current()
                location = TopLoc_Location()
                triangulation = BRep_Tool.Triangulation(face, location)

                if triangulation is not None:
                    # Get vertices
                    for i in range(1, triangulation.NbNodes() + 1):
                        node = triangulation.Node(i)
                        if not location.IsIdentity():
                            node = node.Transformed(location.Transformation())
                        vertices.append([node.X(), node.Y(), node.Z()])

                    # Get triangles
                    for i in range(1, triangulation.NbTriangles() + 1):
                        tri = triangulation.Triangle(i)
                        n1, n2, n3 = tri.Get()
                        faces.append([3, vertex_offset + n1 - 1,
                                     vertex_offset + n2 - 1,
                                     vertex_offset + n3 - 1])

                    vertex_offset += triangulation.NbNodes()

                explorer.Next()

            if vertices and faces:
                import numpy as np
                vertices_array = np.array(vertices)
                faces_array = np.hstack(faces)
                return pv.PolyData(vertices_array, faces_array)

            return None

        except ImportError as e:
            logger.warning(f"Cannot tessellate: {e}")
            return None
        except Exception as e:
            logger.error(f"Tessellation failed: {e}")
            return None

    def invalidate(self):
        """Mark element as needing geometry regeneration."""
        self._dirty = True
        self._solid = None
        self._mesh = None

    def get_properties(self) -> Dict[str, Any]:
        """
        Get element properties for display in UI.

        Returns:
            Dictionary of property names and values
        """
        props = {
            "ID": str(self._id),
            "Part Number": self._part_number,
            "Assembly Number": self._assembly_number,
            "Name": self._name,
            "Type": self.element_type.value,
            "Material": self._material.name if self._material else "",
            "Profile": self._profile.name if self._profile else "",
            "Phase": self._phase,
            "Class": self._class_number,
        }
        props.update(self._get_specific_properties())
        return props

    def _get_specific_properties(self) -> Dict[str, Any]:
        """
        Get element-type-specific properties.

        Override in subclasses.

        Returns:
            Dictionary of property names and values
        """
        return {}

    def set_property(self, name: str, value: Any) -> bool:
        """
        Set element property by name.

        Args:
            name: Property name
            value: New value

        Returns:
            True if property was set
        """
        if name == "Name":
            self._name = str(value)
            return True
        elif name == "Phase":
            self._phase = str(value)
            return True
        elif name == "Class":
            try:
                self._class_number = int(value) if value else 0
                return True
            except (ValueError, TypeError):
                logger.warning(f"Invalid Class value: {value}")
                return False
        return False

    def get_user_attribute(self, name: str) -> Any:
        """Get user-defined attribute."""
        return self._user_attributes.get(name)

    def set_user_attribute(self, name: str, value: Any):
        """Set user-defined attribute."""
        self._user_attributes[name] = value

    def get_bounding_box(self) -> tuple:
        """
        Get axis-aligned bounding box.

        Returns:
            Tuple of (min_point, max_point) as Point3D
        """
        solid = self.get_solid()
        if solid is None:
            from src.geometry.point import Point3D
            return (Point3D.origin(), Point3D.origin())

        try:
            from OCC.Core.Bnd import Bnd_Box
            from OCC.Core.BRepBndLib import brepbndlib_Add
            from src.geometry.point import Point3D

            bbox = Bnd_Box()
            brepbndlib_Add(solid, bbox)

            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            return (
                Point3D(xmin, ymin, zmin),
                Point3D(xmax, ymax, zmax)
            )
        except Exception as e:
            logger.error(f"Failed to get bounding box: {e}")
            from src.geometry.point import Point3D
            return (Point3D.origin(), Point3D.origin())

    def calculate_signature(self, config: "ComparisonConfig") -> "PartSignature":
        """
        Calculate part signature for identical parts detection.

        This method computes a signature based on the comparison configuration,
        which determines what properties are compared when identifying identical
        parts for Tekla-style numbering.

        Args:
            config: ComparisonConfig specifying which properties to compare

        Returns:
            PartSignature that can be used for identical parts detection
        """
        from src.core.numbering import PartSignature

        profile_key = self._profile.name if config.compare_profile and self._profile else None
        material_key = self._material.name if config.compare_material and self._material else None
        name_key = self._name if config.compare_name else None
        geometry_key = self._calculate_geometry_key(config.geometry_tolerance) if config.compare_geometry else ""
        rotation_key = self._get_rotation_key() if config.compare_rotation else None

        return PartSignature(
            element_type=self.element_type.value,
            profile_name=profile_key or "",
            material_name=material_key or "",
            element_name=name_key or "",
            geometry_key=geometry_key,
            rotation_key=str(rotation_key) if rotation_key is not None else ""
        )

    def _calculate_geometry_key(self, tolerance: float = 1.0) -> str:
        """
        Calculate geometry key for signature.

        Override in subclasses to provide element-specific geometry.
        Default implementation returns empty string (no geometry comparison).

        Args:
            tolerance: Rounding tolerance in mm

        Returns:
            Geometry key string
        """
        return ""

    def _get_rotation_key(self) -> Optional[int]:
        """
        Get rotation key for signature comparison.

        Override in subclasses that have rotation.
        Default returns None (no rotation comparison).

        Returns:
            Rotation in degrees (rounded) or None if not applicable
        """
        return None

    @abstractmethod
    def move(self, vector: "Vector3D"):
        """
        Move the element by a vector.

        Args:
            vector: Translation vector
        """
        pass

    def move_by_coordinates(self, dx: float, dy: float, dz: float):
        """
        Move the element by coordinates (Tekla-style move).
        
        Args:
            dx: Delta X
            dy: Delta Y
            dz: Delta Z
        """
        from src.geometry.vector import Vector3D
        self.move(Vector3D(dx, dy, dz))

    def copy(self) -> "StructuralElement":
        """
        Create a deep copy of this element.

        Returns:
            New element with same properties but new ID
        """
        # Subclasses should implement this
        raise NotImplementedError("Copy not implemented for this element type")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id}, name='{self._name}')"
