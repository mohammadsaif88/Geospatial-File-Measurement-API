from typing import Tuple, Optional
import pyproj
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from app.services.crs_service import get_projected_crs_for_geometry

def calculate_feature_measurements(
    geom: BaseGeometry,
    source_crs: Optional[pyproj.CRS]
) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    """
    Transforms geometry to a planar UTM projection and calculates:
    - Area (sq meters) for Polygons
    - Length (meters) for LineStrings
    Returns: (area_sq_m, length_m, projected_crs_name, notes)
    """
    if geom is None or geom.is_empty:
        return None, None, None, "Geometry is empty or null"

    geom_type = geom.geom_type

    if geom_type in ["Point", "MultiPoint"]:
        return None, None, None, "Point geometry has no area or length"

    if source_crs is None:
        source_crs = pyproj.CRS.from_epsg(4326)

    target_crs = get_projected_crs_for_geometry(geom, source_crs)

    if source_crs != target_crs:
        projector = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True).transform
        transformed_geom = transform(projector, geom)
    else:
        transformed_geom = geom

    target_crs_str = f"EPSG:{target_crs.to_epsg()}" if target_crs.to_epsg() else target_crs.name

    if geom_type in ["Polygon", "MultiPolygon"]:
        area = transformed_geom.area
        return round(area, 4), None, target_crs_str, "Calculated surface area"

    elif geom_type in ["LineString", "MultiLineString"]:
        length = transformed_geom.length
        return None, round(length, 4), target_crs_str, "Calculated path length"

    elif geom_type == "GeometryCollection":
        return None, None, target_crs_str, "GeometryCollection measurement is not directly supported"

    return None, None, target_crs_str, f"Unsupported geometry type: {geom_type}"
