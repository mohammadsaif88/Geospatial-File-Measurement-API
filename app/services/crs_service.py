import pyproj
from shapely.geometry.base import BaseGeometry

def get_utm_epsg_from_lon_lat(lon: float, lat: float) -> int:
    """Computes the corresponding WGS84 Universal Transverse Mercator (UTM) EPSG code."""
    zone_number = int((lon + 180) / 6) + 1
    is_northern = lat >= 0
    return 32600 + zone_number if is_northern else 32700 + zone_number

def get_projected_crs_for_geometry(geom: BaseGeometry, source_crs: pyproj.CRS) -> pyproj.CRS:
    """
    Returns an appropriate metric projected coordinate reference system (UTM zone).
    If the source CRS is already planar/projected, returns it without reprojecting.
    """
    if source_crs.is_projected:
        return source_crs

    centroid = geom.centroid
    utm_code = get_utm_epsg_from_lon_lat(centroid.x, centroid.y)
    return pyproj.CRS.from_epsg(utm_code)
