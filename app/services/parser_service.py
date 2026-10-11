import zipfile
import tempfile
from pathlib import Path
import geopandas as gpd
import fiona

# Safely enable KML drivers in Fiona
try:
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
except Exception:
    pass

def parse_geospatial_file(file_path: Path, filename: str) -> gpd.GeoDataFrame:
    """Extracts features from either a .kml file or a zipped ESRI Shapefile."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".kml":
        try:
            return gpd.read_file(file_path, driver="KML")
        except Exception:
            return gpd.read_file(file_path)

    elif suffix == ".zip":
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            shp_files = list(Path(extract_dir).rglob("*.shp"))
            if not shp_files:
                raise ValueError("No .shp file found inside the uploaded ZIP archive.")

            gdf = gpd.read_file(shp_files[0])
            return gdf
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported formats: .kml, .zip")
