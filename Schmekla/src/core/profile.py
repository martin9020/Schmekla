"""
Profile (cross-section) definitions for Schmekla.

Defines structural section profiles for beams, columns, etc.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
from loguru import logger


class ProfileType(Enum):
    """Types of profile cross-sections."""
    I_SECTION = "I"           # Universal beams/columns, W-shapes
    CHANNEL = "C"             # Channel sections (PFC, C-shapes)
    ANGLE = "L"               # Angle sections
    TEE = "T"                 # Tee sections
    RECTANGULAR_HOLLOW = "RHS"  # Rectangular hollow sections
    SQUARE_HOLLOW = "SHS"     # Square hollow sections
    CIRCULAR_HOLLOW = "CHS"   # Circular hollow sections
    CIRCULAR_SOLID = "CIRC"   # Solid circular
    RECTANGULAR_SOLID = "RECT"  # Solid rectangular
    PLATE = "PL"              # Flat plate
    ARBITRARY = "ARB"         # Arbitrary polygon


@dataclass
class Profile:
    """
    Structural section profile.

    Stores section geometry and properties.
    """
    name: str
    profile_type: ProfileType

    # Dimensions (all in mm)
    # For I-sections
    h: float = 0.0       # Overall depth
    b: float = 0.0       # Flange width
    tw: float = 0.0      # Web thickness
    tf: float = 0.0      # Flange thickness
    r: float = 0.0       # Root radius

    # For hollow sections
    t: float = 0.0       # Wall thickness

    # For circular sections
    d: float = 0.0       # Diameter

    # For rectangular/plate
    width: float = 0.0
    height: float = 0.0
    thickness: float = 0.0

    # For channels/angles
    cy: float = 0.0      # Centroid Y offset
    cz: float = 0.0      # Centroid Z offset

    # Section properties (computed or from catalog)
    area: float = 0.0           # Cross-sectional area (mm^2)
    weight: float = 0.0         # Mass per unit length (kg/m)
    ix: float = 0.0             # Second moment of area about X (cm^4)
    iy: float = 0.0             # Second moment of area about Y (cm^4)
    wx: float = 0.0             # Elastic section modulus X (cm^3)
    wy: float = 0.0             # Elastic section modulus Y (cm^3)
    rx: float = 0.0             # Radius of gyration X (cm)
    ry: float = 0.0             # Radius of gyration Y (cm)

    # Arbitrary profile points (for ProfileType.ARBITRARY)
    polygon_points: List[tuple] = field(default_factory=list)

    def to_cadquery_wire(self):
        """
        Create a CadQuery wire representation of this profile.

        Returns:
            CadQuery Workplane with profile
        """
        try:
            import cadquery as cq

            if self.profile_type == ProfileType.I_SECTION:
                return self._create_i_section_cq()
            elif self.profile_type == ProfileType.RECTANGULAR_HOLLOW:
                return self._create_rhs_cq()
            elif self.profile_type == ProfileType.SQUARE_HOLLOW:
                return self._create_shs_cq()
            elif self.profile_type == ProfileType.CIRCULAR_HOLLOW:
                return self._create_chs_cq()
            elif self.profile_type == ProfileType.RECTANGULAR_SOLID:
                return cq.Workplane("XY").rect(self.width, self.height)
            elif self.profile_type == ProfileType.CIRCULAR_SOLID:
                return cq.Workplane("XY").circle(self.d / 2)
            elif self.profile_type == ProfileType.PLATE:
                return cq.Workplane("XY").rect(self.width, self.thickness)
            elif self.profile_type == ProfileType.CHANNEL:
                return self._create_channel_cq()
            elif self.profile_type == ProfileType.ANGLE:
                return self._create_angle_cq()
            else:
                # Default to rectangle
                return cq.Workplane("XY").rect(100, 100)

        except ImportError:
            logger.error("CadQuery not available")
            raise

    def _create_i_section_cq(self):
        """Create I-section profile with CadQuery."""
        import cadquery as cq

        # Create I-section by subtracting rectangles
        # Start with overall bounding rectangle
        result = (
            cq.Workplane("XY")
            .rect(self.b, self.h)
            .extrude(1)  # Temporary extrude for boolean
        )

        # Subtract web cutouts (left and right of web)
        cutout_width = (self.b - self.tw) / 2
        cutout_height = self.h - 2 * self.tf

        if cutout_width > 0 and cutout_height > 0:
            # Left cutout
            result = result.faces(">Z").workplane().center(
                -(self.b/2 - cutout_width/2), 0
            ).rect(cutout_width, cutout_height).cutThruAll()

            # Right cutout
            result = result.faces(">Z").workplane().center(
                (self.b/2 - cutout_width/2), 0
            ).rect(cutout_width, cutout_height).cutThruAll()

        # Return as 2D wire for sweeping
        return cq.Workplane("XY").rect(self.b, self.h)  # Simplified

    def _create_rhs_cq(self):
        """Create rectangular hollow section profile."""
        import cadquery as cq

        outer = cq.Workplane("XY").rect(self.b, self.h)
        inner_w = self.b - 2 * self.t
        inner_h = self.h - 2 * self.t

        if inner_w > 0 and inner_h > 0:
            # For hollow section, we need boolean subtraction
            # Return outer for now, hollow handled in solid generation
            pass

        return outer

    def _create_shs_cq(self):
        """Create square hollow section profile."""
        import cadquery as cq
        return cq.Workplane("XY").rect(self.b, self.b)

    def _create_chs_cq(self):
        """Create circular hollow section profile."""
        import cadquery as cq
        return cq.Workplane("XY").circle(self.d / 2)

    def _create_channel_cq(self):
        """Create channel section profile."""
        import cadquery as cq
        # Simplified C-channel
        return cq.Workplane("XY").rect(self.b, self.h)

    def _create_angle_cq(self):
        """Create angle section profile."""
        import cadquery as cq
        # L-shaped profile
        return cq.Workplane("XY").rect(self.b, self.h)

    def to_ifc_profile_def(self, ifc_model):
        """
        Create IFC profile definition.

        Args:
            ifc_model: IFC model instance

        Returns:
            IFC profile entity
        """
        ifc = ifc_model.ifc

        if self.profile_type == ProfileType.I_SECTION:
            return ifc.create_entity(
                "IfcIShapeProfileDef",
                ProfileType="AREA",
                ProfileName=self.name,
                OverallWidth=self.b,
                OverallDepth=self.h,
                WebThickness=self.tw,
                FlangeThickness=self.tf,
                FilletRadius=self.r if self.r > 0 else None
            )
        elif self.profile_type == ProfileType.RECTANGULAR_HOLLOW:
            return ifc.create_entity(
                "IfcRectangleHollowProfileDef",
                ProfileType="AREA",
                ProfileName=self.name,
                XDim=self.b,
                YDim=self.h,
                WallThickness=self.t
            )
        elif self.profile_type in (ProfileType.CIRCULAR_HOLLOW, ProfileType.CIRCULAR_SOLID):
            if self.t > 0:
                return ifc.create_entity(
                    "IfcCircleHollowProfileDef",
                    ProfileType="AREA",
                    ProfileName=self.name,
                    Radius=self.d / 2,
                    WallThickness=self.t
                )
            else:
                return ifc.create_entity(
                    "IfcCircleProfileDef",
                    ProfileType="AREA",
                    ProfileName=self.name,
                    Radius=self.d / 2
                )
        elif self.profile_type == ProfileType.RECTANGULAR_SOLID:
            return ifc.create_entity(
                "IfcRectangleProfileDef",
                ProfileType="AREA",
                ProfileName=self.name,
                XDim=self.width,
                YDim=self.height
            )
        elif self.profile_type == ProfileType.CHANNEL:
            return ifc.create_entity(
                "IfcCShapeProfileDef",
                ProfileType="AREA",
                ProfileName=self.name,
                Depth=self.h,
                Width=self.b,
                WallThickness=self.tw,
                Girth=self.tf
            )
        elif self.profile_type == ProfileType.ANGLE:
            return ifc.create_entity(
                "IfcLShapeProfileDef",
                ProfileType="AREA",
                ProfileName=self.name,
                Depth=self.h,
                Width=self.b,
                Thickness=self.tw
            )
        else:
            # Fallback to arbitrary profile
            return self._create_arbitrary_ifc_profile(ifc)

    def _create_arbitrary_ifc_profile(self, ifc):
        """Create arbitrary closed profile for IFC."""
        # Create polyline from polygon points or bounding box
        if self.polygon_points:
            points = self.polygon_points
        else:
            # Create rectangle as fallback
            w, h = self.width or 100, self.height or 100
            points = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]

        ifc_points = [
            ifc.create_entity("IfcCartesianPoint", Coordinates=list(p))
            for p in points
        ]
        # Close the loop
        ifc_points.append(ifc_points[0])

        polyline = ifc.create_entity("IfcPolyline", Points=ifc_points)

        return ifc.create_entity(
            "IfcArbitraryClosedProfileDef",
            ProfileType="AREA",
            ProfileName=self.name,
            OuterCurve=polyline
        )

    @classmethod
    def from_name(cls, name: str) -> "Profile":
        """
        Load profile from catalog by name.

        Args:
            name: Profile name (e.g., "UB 305x165x40")

        Returns:
            Profile instance
        """
        catalog = ProfileCatalog.get_instance()
        profile = catalog.get_profile(name)
        if profile is None:
            logger.warning(f"Profile '{name}' not found, creating placeholder")
            return cls(name=name, profile_type=ProfileType.I_SECTION, h=300, b=165, tw=6, tf=10)
        return profile

    @classmethod
    def create_plate(cls, width: float, thickness: float) -> "Profile":
        """Create a plate profile."""
        return cls(
            name=f"PL {width}x{thickness}",
            profile_type=ProfileType.PLATE,
            width=width,
            thickness=thickness,
            height=thickness
        )


class ProfileCatalog:
    """
    Catalog of available structural profiles.

    Singleton pattern for global access.
    """
    _instance: Optional["ProfileCatalog"] = None

    def __init__(self):
        self._profiles: Dict[str, Profile] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ProfileCatalog":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_catalog(self, catalog_path: Path = None):
        """
        Load profile catalog from JSON file.

        Args:
            catalog_path: Path to catalog JSON
        """
        if catalog_path is None:
            # Default to bundled catalog
            catalog_path = Path(__file__).parent.parent.parent / "resources" / "profiles" / "uk_sections.json"

        if not catalog_path.exists():
            logger.warning(f"Profile catalog not found: {catalog_path}")
            self._create_default_profiles()
            return

        try:
            with open(catalog_path, "r") as f:
                data = json.load(f)

            for section_type, sections in data.items():
                for name, props in sections.items():
                    profile = self._parse_profile(name, section_type, props)
                    self._profiles[name] = profile

            self._loaded = True
            logger.info(f"Loaded {len(self._profiles)} profiles from {catalog_path}")

        except Exception as e:
            logger.error(f"Failed to load profile catalog: {e}")
            self._create_default_profiles()

    def _parse_profile(self, name: str, section_type: str, props: dict) -> Profile:
        """Parse profile from catalog data."""
        type_map = {
            "UB": ProfileType.I_SECTION,
            "UC": ProfileType.I_SECTION,
            "PFC": ProfileType.CHANNEL,
            "SHS": ProfileType.SQUARE_HOLLOW,
            "RHS": ProfileType.RECTANGULAR_HOLLOW,
            "CHS": ProfileType.CIRCULAR_HOLLOW,
            "L": ProfileType.ANGLE,
        }

        profile_type = type_map.get(section_type, ProfileType.I_SECTION)

        return Profile(
            name=name,
            profile_type=profile_type,
            h=props.get("h", props.get("D", 0)),
            b=props.get("b", props.get("B", 0)),
            tw=props.get("tw", props.get("t", 0)),
            tf=props.get("tf", 0),
            r=props.get("r", 0),
            t=props.get("t", 0),
            d=props.get("D", props.get("d", 0)),
            area=props.get("area", props.get("A", 0)),
            weight=props.get("weight", props.get("M", 0)),
            ix=props.get("Ix", props.get("I", 0)),
            iy=props.get("Iy", 0),
        )

    def _create_default_profiles(self):
        """Create a minimal set of default profiles."""
        defaults = [
            Profile("UB 305x165x40", ProfileType.I_SECTION, h=303.4, b=165, tw=6, tf=10.2, r=8.9, weight=40.3),
            Profile("UB 406x178x54", ProfileType.I_SECTION, h=402.6, b=177.7, tw=7.7, tf=10.9, r=10.2, weight=54.1),
            Profile("UC 203x203x46", ProfileType.I_SECTION, h=203.2, b=203.6, tw=7.2, tf=11, r=10.2, weight=46.1),
            Profile("UC 254x254x73", ProfileType.I_SECTION, h=254, b=254.6, tw=8.6, tf=14.2, r=12.7, weight=73.1),
            Profile("SHS 100x100x5", ProfileType.SQUARE_HOLLOW, h=100, b=100, t=5, weight=14.4),
            Profile("SHS 150x150x8", ProfileType.SQUARE_HOLLOW, h=150, b=150, t=8, weight=34.8),
            Profile("RHS 200x100x6", ProfileType.RECTANGULAR_HOLLOW, h=100, b=200, t=6, weight=26.4),
            Profile("CHS 168.3x7.1", ProfileType.CIRCULAR_HOLLOW, d=168.3, t=7.1, weight=28.3),
            Profile("PFC 200x90x30", ProfileType.CHANNEL, h=200, b=90, tw=6.5, tf=14, weight=29.7),
        ]

        for profile in defaults:
            self._profiles[profile.name] = profile

        self._loaded = True
        logger.info(f"Created {len(self._profiles)} default profiles")

    def get_profile(self, name: str) -> Optional[Profile]:
        """Get profile by name."""
        if not self._loaded:
            self.load_catalog()
        return self._profiles.get(name)

    def get_all_profiles(self) -> List[Profile]:
        """Get all profiles."""
        if not self._loaded:
            self.load_catalog()
        return list(self._profiles.values())

    def get_profiles_by_type(self, profile_type: ProfileType) -> List[Profile]:
        """Get profiles of specific type."""
        if not self._loaded:
            self.load_catalog()
        return [p for p in self._profiles.values() if p.profile_type == profile_type]

    def get_profile_names(self) -> List[str]:
        """Get list of all profile names."""
        if not self._loaded:
            self.load_catalog()
        return list(self._profiles.keys())
