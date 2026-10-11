# Geospatial-File-Measurement-API
Production-ready FastAPI service for parsing Shapefiles and KML files, with dynamic UTM CRS reprojection and metric measurement calculations (area &amp; length).

Here is the complete, polished, and structured **`README.md`** modeled after high-standard GitHub challenge submissions (clean badges, structured directory trees, ASCII architecture diagrams, copy-ready cURL snippets, JSON responses, mathematical formulas, design comparison tables, and the required learnings/future scope).

You can copy and paste this directly into your `README.md` file:

```markdown
# 🌍 Geospatial File Measurement API

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Geospatial Libraries](https://img.shields.io/badge/GIS-GeoPandas%20%7C%20Shapely%20%7C%20PyProj-green.svg)](https://geopandas.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)

A production-grade REST backend built with **FastAPI**, **GeoPandas**, **Shapely**, and **PyProj** that accepts geospatial vector datasets (zipped ESRI Shapefiles or KML files), inspects and extracts vector features, reprojects geographic coordinates to optimal metric projections (UTM), and computes metric spatial measurements (area and perimeter/length).

---

## 📑 Table of Contents
- [Problem Overview](#-problem-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Architecture](#-project-architecture)
- [Setup & Local Execution](#-setup--local-execution)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [Docker Setup](#docker-setup)
- [API Documentation](#-api-documentation)
  - [1. Upload File](#1-upload-file)
  - [2. Get File Details](#2-get-file-details)
  - [3. Get Measurements](#3-get-measurements)
- [CRS Handling & Mathematics](#-crs-handling--mathematics)
- [Design Decisions & Trade-offs](#-design-decisions--trade-offs)
- [Learnings & Future Scope](#-learnings--future-scope)
- [License](#-license)

---

## 📌 Problem Overview

Standard GIS vector files often store spatial data using geographic coordinate reference systems (e.g., `EPSG:4326` / WGS 84) where coordinates are represented in spherical angular degrees (latitude and longitude). Computing geometric properties directly using degrees results in distorted, unit-less numbers.

This service solves the problem by:
1. Ingesting both **`.kml`** files and **`.zip`** archives containing ESRI Shapefiles (`.shp`, `.shx`, `.dbf`, `.prj`).
2. Parsing and extracting individual features and properties.
3. Automatically deriving an optimal metric **Projected Coordinate Reference System (UTM zone)** from each feature's centroid.
4. Reprojecting planar coordinates and computing real-world metric units ($m^2$, hectares, meters, and kilometers).
5. Gracefully handling non-measurable geometries (such as `Point` and `MultiPoint`) without throwing exceptions.

---

## ✨ Key Features

- **Multi-Format Ingestion**: Supports `.kml` and zipped Shapefiles containing mandatory sidecar files.
- **Dynamic Projected CRS Selection**: Determines the exact WGS84 Universal Transverse Mercator (UTM) zone for each geometry to prevent projection distortion.
- **Dual Metric Conversions**: Returns areas in both $m^2$ and hectares; returns lengths in both meters and kilometers.
- **Fail-Safe Processing**: Gracefully identifies unsupported or point geometries without failing the batch request.
- **Self-Documenting API**: Interactive OpenAPI (Swagger UI) available at `/docs`.
- **Lightweight Persistence**: Persists files and extracted features via SQLAlchemy (SQLite by default, easily swappable with PostgreSQL).

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Framework** | FastAPI | High-throughput asynchronous REST API |
| **Data Validation** | Pydantic v2 | Request/response schema serialization |
| **Geospatial Engine** | GeoPandas, Shapely | Vector data parsing and planar geometric operations |
| **Coordinate Transformation** | PyProj (PROJ bindings) | Dynamic geodetic-to-projected CRS conversions |
| **GIS File Drivers** | Fiona (GDAL/OGR) | Format drivers for KML and Shapefile archives |
| **ORM & Database** | SQLAlchemy & SQLite | Relational metadata and feature persistence |
| **Testing** | Pytest & HTTPX | Automated endpoint and geometry calculation tests |

---

## 🏗 Project Architecture

### Directory Tree

```text
geospatial-measurement-api/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Application settings and directory paths
│   ├── database.py               # SQLAlchemy engine and session dependency
│   ├── models.py                 # FileRecord & FeatureRecord ORM models
│   ├── schemas.py                # Pydantic validation schemas
│   ├── main.py                   # FastAPI application factory and route mounts
│   ├── routers/
│   │   ├── __init__.py
│   │   └── files.py              # HTTP endpoints (/api/files/)
│   └── services/
│       ├── __init__.py
│       ├── crs_service.py        # Centroid calculation & UTM zone selection
│       ├── measurement_service.py# Geometry reprojection and measurement logic
│       └── parser_service.py     # KML and Shapefile (.zip) extraction logic
├── tests/
│   ├── __init__.py
│   └── test_api.py               # Automated pytest suite
├── uploads/                      # Temporary buffer directory (gitignored)
│   └── .gitkeep
├── .gitignore
├── Dockerfile
├── LICENSE
├── requirements.txt
└── README.md

```

### File Processing & Measurement Flow

```text
               Client (HTTP Request)
                         │
                         ▼
        [POST /api/files/] (Multipart Stream)
                         │
                         ▼
       Save Temporary Buffer in ./uploads/
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
    [.kml Format]                 [.zip Shapefile]
  Fiona KML Driver             Extract .shp, .dbf, .shx
         │                               │
         └───────────────┬───────────────┘
                         ▼
           Load into GeoPandas GeoDataFrame
                         │
                         ▼
       Iterate over Features & Geometries
                         │
            Is Geometry a Point/Null?
             ├── YES ──► Log note, skip calculation
             └── NO
                  │
                  ▼
         Calculate Centroid (Lon, Lat)
                  │
                  ▼
         Derive Optimal UTM Zone (EPSG)
                  │
                  ▼
       Reproject Geometry via PyProj
                  │
         ┌────────┴────────┐
         ▼                 ▼
   [Polygon/Multi]   [Line/MultiLine]
   Calculate Area     Calculate Length
         │                 │
         └────────┬────────┘
                  ▼
      Store Features in Database
                  │
                  ▼
     Clean up Temporary Files from Disk
                  │
                  ▼
         Return HTTP 201 Response

```

---

## ⚙ Setup & Local Execution

### Prerequisites

Ensure you have Python 3.10+ installed along with system-level geospatial C/C++ libraries (`GDAL`, `GEOS`, `PROJ`):

* **Ubuntu / Debian**:
```bash
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev libproj-dev build-essential

```


* **macOS (Homebrew)**:
```bash
brew install gdal geos proj

```


* **Windows**:
Using Docker or WSL2 (Ubuntu) is recommended to prevent local GDAL path conflicts.

---

### Local Installation

1. **Clone the repository:**
```bash
git clone [https://github.com/](https://github.com/)<your-username>/geospatial-measurement-api.git
cd geospatial-measurement-api

```


2. **Create and activate a virtual environment:**
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (Git Bash)
python -m venv venv
source venv/Scripts/activate

```


3. **Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt

```


4. **Start the API service:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```


5. **Verify the server:**
* Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Check: [http://localhost:8000/health](http://localhost:8000/health)


6. **Run automated test suite:**
```bash
pytest tests/test_api.py -v

```



---

### Docker Setup

To run the application inside an isolated container with all pre-configured GDAL libraries:

```bash
# Build the Docker image
docker build -t geospatial-measurement-api .

# Run the container
docker run -p 8000:8000 --name geospatial-api-container geospatial-measurement-api

```

Access the API at `http://localhost:8000/docs`.

---

## 📖 API Documentation

### 1. Upload File

Uploads, parses, reprojects, and stores feature measurements from an ESRI Shapefile archive (`.zip`) or Keyhole Markup Language (`.kml`) file.

* **Method**: `POST`
* **Path**: `/api/files/`
* **Request Format**: `multipart/form-data`
* **Parameters**: `file` (Binary file, `.zip` or `.kml`)

#### Sample Request (cURL)

```bash
curl -X 'POST' \
  'http://localhost:8000/api/files/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample_boundary.kml;type=application/vnd.google-earth.kml+xml'

```

#### Sample Response (`201 Created`)

```json
{
  "id": "e8a21f4c",
  "filename": "sample_boundary.kml",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "error_message": null
}

```

---

### 2. Get File Details

Returns metadata, CRS, feature count, and processing status of an uploaded file.

* **Method**: `GET`
* **Path**: `/api/files/{id}/`
* **Parameters**: `id` (string, path parameter)

#### Sample Request (cURL)

```bash
curl -X 'GET' 'http://localhost:8000/api/files/e8a21f4c/' -H 'accept: application/json'

```

#### Sample Response (`200 OK`)

```json
{
  "id": "e8a21f4c",
  "filename": "sample_boundary.kml",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "error_message": null
}

```

---

### 3. Get Measurements

Retrieves calculated spatial measurements for every feature contained in the uploaded file.

* **Method**: `GET`
* **Path**: `/api/files/{id}/measurements/`
* **Parameters**: `id` (string, path parameter)

#### Sample Request (cURL)

```bash
curl -X 'GET' 'http://localhost:8000/api/files/e8a21f4c/measurements/' -H 'accept: application/json'

```

#### Sample Response (`200 OK`)

```json
{
  "file_id": "e8a21f4c",
  "filename": "sample_boundary.kml",
  "total_features": 2,
  "measurements": [
    {
      "feature_index": 0,
      "geometry_type": "Polygon",
      "area_sq_meters": 11762.33,
      "area_hectares": 1.1762,
      "length_meters": null,
      "length_kilometers": null,
      "properties": {
        "Name": "Agricultural Parcel 12",
        "Owner": "State Land Registry"
      },
      "projected_crs_used": "EPSG:32644",
      "notes": "Calculated surface area"
    },
    {
      "feature_index": 1,
      "geometry_type": "LineString",
      "area_sq_meters": null,
      "area_hectares": null,
      "length_meters": 435.80,
      "length_kilometers": 0.4358,
      "properties": {
        "Name": "Irrigation Canal",
        "FlowRate": "Medium"
      },
      "projected_crs_used": "EPSG:32644",
      "notes": "Calculated path length"
    }
  ]
}

```

---

## 🌐 CRS Handling & Mathematics

### The Spherical Degree Problem

When vector features are formatted in `EPSG:4326` (WGS 84), coordinate tuples are expressed in latitude and longitude (angular degrees). Running Euclidean formulas directly on degrees results in:


$$\text{Area} = \Delta \text{degrees}^2 \quad (\text{Invalid for metric measurements})$$

The metric size of 1 degree of longitude varies dramatically depending on latitude:


$$\text{Length of } 1^\circ \text{ Longitude} \approx 111.32 \times \cos(\text{latitude}) \text{ km}$$

### Dynamic UTM Zone Strategy

To avoid scale distortions, our application inspects each feature's centroid $(\text{Lon}, \text{Lat})$ and dynamically assigns it to its local **Universal Transverse Mercator (UTM)** zone projection:

$$\text{Zone} = \left\lfloor \frac{\text{Longitude} + 180}{6} \right\rfloor + 1$$

* **Northern Hemisphere** ($\text{Latitude} \ge 0$): `EPSG: 32600 + Zone`
* **Southern Hemisphere** ($\text{Latitude} < 0$): `EPSG: 32700 + Zone`

Coordinates are reprojected using `pyproj.Transformer(from_crs, to_crs, always_xy=True)` into a local Cartesian plane with metric coordinates $(x, y)$, guaranteeing true planar calculation accuracy.

---

## 💡 Design Decisions & Trade-offs

| Component | Choice Made | Alternatives Considered | Justification |
| --- | --- | --- | --- |
| **Backend Framework** | **FastAPI** | Django / DRF | FastAPI provides native async file streaming, automatic Pydantic request/response validation, and auto-generated Swagger documentation with lower memory overhead. |
| **Projection Strategy** | **Dynamic UTM (Centroid-based)** | Web Mercator (`EPSG:3857`), Equal Earth | Web Mercator inflates surface area significantly away from the equator (up to 300%+ error). Dynamic UTM minimizes local geometric distortion to $< 0.1\%$. |
| **File Parsing** | **GeoPandas & Fiona** | Raw GDAL Python bindings | Fiona and GeoPandas provide clean Pythonic abstractions and simplify managing the multi-file dependencies of Shapefiles (`.shp`, `.dbf`, `.shx`, `.prj`). |
| **Storage Architecture** | **SQLAlchemy + SQLite** | In-memory Dictionary, PostgreSQL/PostGIS | SQLite provides persistent state across endpoints (`POST /api/files/` $\rightarrow$ `GET /measurements/`) without requiring evaluators to configure an external database server locally. |
| **Error Handling** | **Graceful Feature Reporting** | Reject file on Point/Null geometry | GIS datasets often contain mixed geometry layers. Unsupported geometries (e.g., Points) populate a `notes` explanation rather than causing the entire batch to fail. |

---

## 🚀 Learnings & Future Scope

### Learnings

1. **Fiona Driver Registration**: KML files require manual driver registration (`fiona.drvsupport.supported_drivers['KML'] = 'rw'`) due to build variations in standard GDAL packages.
2. **Axis Ordering Caveats**: In modern PROJ versions, EPSG:4326 assumes `(lat, lon)` ordering. Specifying `always_xy=True` in `pyproj.Transformer` ensures consistent `(lon, lat)` planar mapping.
3. **Shapefile Sidecars**: ESRI Shapefiles rely on companion files (`.shx`, `.dbf`, `.prj`). Extracting `.zip` archives into isolated temporary directories ensures proper reading without file conflicts.

### Future Scope

* **Asynchronous Task Queue**: Offload file parsing to **Celery** or **ARQ** backed by Redis to handle multi-gigabyte GIS files without blocking API threads.
* **PostGIS Spatial Indexing**: Migrate database storage to PostgreSQL/PostGIS to support spatial spatial queries (e.g., bounding-box filtering and intersection checks).
* **Direct S3 Pre-Signed Uploads**: Stream file uploads directly to AWS S3 using pre-signed URLs to reduce web server disk utilization.
* **Additional GIS Formats**: Add ingestion support for GeoJSON, GeoPackage (`.gpkg`), and cloud-optimized formats like FlatGeoBuf and GeoParquet.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

---

### How to Add It via Git Bash

Run these commands inside your project folder:

```bash
# 1. Open the file in VS Code or your editor and paste the text above
code README.md

# 2. Stage, commit, and push the changes
git add README.md
git commit -m "docs: complete comprehensive README with architecture, api docs, and design decisions"
git push

```
