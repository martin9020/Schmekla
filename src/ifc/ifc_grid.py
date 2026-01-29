"""
IFC Grid export implementation.
"""
from typing import Any, List
import math
from loguru import logger

from src.core.grid import GridSystem
if "IFCExporter" not in locals():
    from src.ifc.exporter import IFCExporter

def create_ifc_grid(grid_system: GridSystem, exporter: "IFCExporter") -> Any:
    """
    Create IfcGrid entity from GridSystem.

    Args:
        grid_system: GridSystem element
        exporter: IFC exporter instance

    Returns:
        IfcGrid entity
    """
    ifc = exporter.ifc
    
    # Create U-axes (X-grids, vertical lines in plan)
    u_axes = []
    for grid_line in grid_system.x_grids:
        axis = _create_grid_axis(ifc, grid_line.label, grid_line.position, True, grid_system)
        u_axes.append(axis)
        
    # Create V-axes (Y-grids, horizontal lines in plan)
    v_axes = []
    for grid_line in grid_system.y_grids:
        axis = _create_grid_axis(ifc, grid_line.label, grid_line.position, False, grid_system)
        v_axes.append(axis)
        
    # Grid placement
    placement = exporter.create_local_placement(grid_system.origin)
    
    # Create IfcGrid
    ifc_grid = ifc.create_entity(
        "IfcGrid",
        GlobalId=ifc.create_entity("IfcGloballyUniqueId", str(grid_system.id).replace("-", "")[:22]), # Simplified GUID
        OwnerHistory=exporter.get_owner_history(),
        Name=grid_system.name,
        ObjectPlacement=placement,
        UAxes=u_axes,
        VAxes=v_axes
    )
    
    return ifc_grid

def _create_grid_axis(ifc, label: str, position: float, is_u_axis: bool, grid_system: GridSystem):
    """Create IfcGridAxis."""
    # Define length of grid lines (should cover the model)
    # For now, hardcode or estimate based on grid extent
    # A better way is to compute the bounding box of the other grid lines
    
    min_other = 0.0
    max_other = 10000.0
    
    if is_u_axis:
        # This is a line along Y axis at X = position
        # Start: (position, min_y) End: (position, max_y)
        if grid_system.y_grids:
            min_other = min(g.position for g in grid_system.y_grids) - 1000.0
            max_other = max(g.position for g in grid_system.y_grids) + 1000.0
            
        p1 = ifc.create_entity("IfcCartesianPoint", Coordinates=[float(position), float(min_other), 0.0])
        p2 = ifc.create_entity("IfcCartesianPoint", Coordinates=[float(position), float(max_other), 0.0])
        
    else:
        # This is a line along X axis at Y = position
        # Start: (min_x, position) End: (max_x, position)
        if grid_system.x_grids:
            min_other = min(g.position for g in grid_system.x_grids) - 1000.0
            max_other = max(g.position for g in grid_system.x_grids) + 1000.0
            
        p1 = ifc.create_entity("IfcCartesianPoint", Coordinates=[float(min_other), float(position), 0.0])
        p2 = ifc.create_entity("IfcCartesianPoint", Coordinates=[float(max_other), float(position), 0.0])
        
    line = ifc.create_entity("IfcPolyline", Points=[p1, p2])
    
    axis = ifc.create_entity(
        "IfcGridAxis",
        AxisTag=label,
        AxisCurve=line,
        SameSense=True
    )
    
    return axis
