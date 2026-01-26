"""
Base structural element class for Schmekla.

All structural elements (beams, columns, plates, etc.) inherit from this class.
"""

from abc import ABC, abstractmethod
from enum import Enum
from uuid import UUID, uuid4
from typing import Any, Dict, Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from src.core.material import Material
    from src.core.profile import Profile


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
            self._class_number = int(value)
            return True
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
