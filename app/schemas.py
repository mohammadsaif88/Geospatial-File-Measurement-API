from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.models import ProcessingStatus

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: Optional[str] = None
    status: ProcessingStatus
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class FeatureMeasurement(BaseModel):
    feature_index: int
    geometry_type: str
    area_sq_meters: Optional[float] = None
    area_hectares: Optional[float] = None
    length_meters: Optional[float] = None
    length_kilometers: Optional[float] = None
    properties: Dict[str, Any]
    projected_crs_used: Optional[str] = None
    notes: Optional[str] = None

class FileMeasurementResponse(BaseModel):
    file_id: str
    filename: str
    total_features: int
    measurements: List[FeatureMeasurement]
