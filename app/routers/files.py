import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import mapping
import pyproj

from app.database import get_db
from app.config import settings
from app.models import FileRecord, FeatureRecord, ProcessingStatus
from app.schemas import FileInfoResponse, FileMeasurementResponse, FeatureMeasurement
from app.services.parser_service import parse_geospatial_file
from app.services.measurement_service import calculate_feature_measurements

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.post("/", response_model=FileInfoResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith(".zip") or file.filename.endswith(".kml")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Upload a .kml file or a .zip containing an ESRI Shapefile."
        )

    file_id = str(uuid.uuid4())[:8]
    temp_file_path = settings.UPLOAD_DIR / f"{file_id}_{file.filename}"

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_record = FileRecord(
        id=file_id,
        filename=file.filename,
        status=ProcessingStatus.PENDING
    )
    db.add(file_record)
    db.commit()

    try:
        gdf = parse_geospatial_file(temp_file_path, file.filename)
        crs_str = gdf.crs.to_string() if gdf.crs else "EPSG:4326"
        source_crs = pyproj.CRS.from_user_input(crs_str) if gdf.crs else pyproj.CRS.from_epsg(4326)

        file_record.crs = crs_str
        file_record.feature_count = len(gdf)

        for idx, row in gdf.iterrows():
            geom = row.geometry
            geom_type = geom.geom_type if geom else "None"

            props = {
                k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                for k, v in row.drop("geometry", errors="ignore").items()
            }

            area_sq_m, length_m, proj_crs, notes = calculate_feature_measurements(geom, source_crs)

            feature_record = FeatureRecord(
                file_id=file_id,
                feature_index=int(idx),
                geometry_type=geom_type,
                geometry_geojson=mapping(geom) if geom else {},
                properties=props,
                projected_crs=proj_crs,
                area_sq_m=area_sq_m,
                length_m=length_m,
                measurement_notes=notes
            )
            db.add(feature_record)

        file_record.status = ProcessingStatus.COMPLETED
        db.commit()
        db.refresh(file_record)
        return file_record

    except Exception as e:
        db.rollback()
        file_record.status = ProcessingStatus.FAILED
        file_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=422, detail=f"File processing error: {str(e)}")
    finally:
        if temp_file_path.exists():
            os.remove(temp_file_path)

@router.get("/{file_id}/", response_model=FileInfoResponse)
def get_file_info(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File record not found")
    return record

@router.get("/{file_id}/measurements/", response_model=FileMeasurementResponse)
def get_file_measurements(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File record not found")

    measurements = []
    for f in record.features:
        measurements.append(FeatureMeasurement(
            feature_index=f.feature_index,
            geometry_type=f.geometry_type,
            area_sq_meters=f.area_sq_m,
            area_hectares=round(f.area_sq_m / 10000.0, 4) if f.area_sq_m is not None else None,
            length_meters=f.length_m,
            length_kilometers=round(f.length_m / 10000.0, 4) if f.length_m is not None else None,
            properties=f.properties or {},
            projected_crs_used=f.projected_crs,
            notes=f.measurement_notes
        ))

    return FileMeasurementResponse(
        file_id=record.id,
        filename=record.filename,
        total_features=record.feature_count,
        measurements=measurements
    )
