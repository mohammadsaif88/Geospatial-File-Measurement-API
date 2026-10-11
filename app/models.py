import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Enum, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    filename = Column(String, nullable=False)
    feature_count = Column(Integer, default=0)
    crs = Column(String, nullable=True)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    features = relationship("FeatureRecord", back_populates="file", cascade="all, delete-orphan")

class FeatureRecord(Base):
    __tablename__ = "feature_records"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("file_records.id"), nullable=False)
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String, nullable=False)
    geometry_geojson = Column(JSON, nullable=False)
    properties = Column(JSON, nullable=False)
    projected_crs = Column(String, nullable=True)
    area_sq_m = Column(Float, nullable=True)
    length_m = Column(Float, nullable=True)
    measurement_notes = Column(String, nullable=True)

    file = relationship("FileRecord", back_populates="features")
