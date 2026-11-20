from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.versioning import diff_revisions
from app.services.ifc_engine import ingest_ifc_file

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def test_ingest_duplex_ifc():
    ifc_path = FIXTURES / "duplex.ifc"
    with ifc_path.open("rb") as f:
        res = client.post("/api/v1/models/ingest", files={"file": ("duplex.ifc", f, "application/octet-stream")})
    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "IFC2X3"
    assert body["total_products"] > 0
    assert body["healthy_geometry_count"] > 0
    assert 0.0 <= body["quality_score"] <= 100.0


def test_revision_diff_endpoint():
    r1 = ingest_ifc_file(FIXTURES / "sample.ifc", check_geometry=False)
    r2 = ingest_ifc_file(FIXTURES / "duplex.ifc", check_geometry=False)
    diff = diff_revisions(r1, r2)
    assert len(diff.added_guids) > 0
    assert len(diff.removed_guids) > 0


def test_boq_quality_gate_catches_dirty_subcontractor_csv():
    csv_path = FIXTURES / "dirty_subcontractor_boq.csv"
    with csv_path.open("rb") as f:
        res = client.post("/api/v1/boq/validate", files={"file": ("dirty_subcontractor_boq.csv", f, "text/csv")})
    assert res.status_code == 200
    body = res.json()
    assert body["passed"] is False
    assert body["violation_count"] > 0
    assert body["quality_score"] < 100.0
