from fastapi import FastAPI
from app.database import Base, engine
from app.routers import files

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Processes Shapefiles and KML files to reproject and calculate metric area and length.",
    version="1.0.0"
)

app.include_router(files.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
