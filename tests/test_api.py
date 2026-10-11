import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_kml_bytes():
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Survey Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              78.4867,17.3850,0
              78.4877,17.3850,0
              78.4877,17.3860,0
              78.4867,17.3860,0
              78.4867,17.3850,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}

def test_upload_kml_and_get_measurements(sample_kml_bytes):
    files = {"file": ("survey.kml", sample_kml_bytes, "application/vnd.google-earth.kml+xml")}
    upload_res = client.post("/api/files/", files=files)
    assert upload_res.status_code == 201
    file_id = upload_res.json()["id"]

    info_res = client.get(f"/api/files/{file_id}/")
    assert info_res.status_code == 200
    assert info_res.json()["status"] == "COMPLETED"

    measure_res = client.get(f"/api/files/{file_id}/measurements/")
    assert measure_res.status_code == 200
    m_data = measure_res.json()
    assert m_data["total_features"] == 1
    assert m_data["measurements"][0]["geometry_type"] == "Polygon"
    assert m_data["measurements"][0]["area_sq_meters"] > 0
