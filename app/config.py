from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Geospatial File Measurement API"
    UPLOAD_DIR: Path = Path("./uploads")
    DATABASE_URL: str = "sqlite:///./geospatial_measurements.db"

    class Config:
        env_file = ".env"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
