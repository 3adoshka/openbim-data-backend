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
    assert body["qto_totals"]["total_volume_m3"] > 1000.0
    assert body["qto_totals"]["total_area_m2"] > 4000.0


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


def test_persisted_revision_retrieval():
    ifc_path = FIXTURES / "duplex.ifc"
    with ifc_path.open("rb") as f:
        ing = client.post("/api/v1/models/ingest", files={"file": ("duplex.ifc", f, "application/octet-stream")})
    rev_id = ing.json()["revision_id"]
    fetched = client.get(f"/api/v1/models/revisions/{rev_id}")
    assert fetched.status_code == 200
    assert fetched.json()["revision_id"] == rev_id


def test_buildingsmart_ids_xml_validation():
    with (FIXTURES / "duplex.ifc").open("rb") as f_ifc, (FIXTURES / "structural_baseline.ids").open("rb") as f_ids:
        res = client.post("/api/v1/models/validate-ids", files={"ifc_file": ("duplex.ifc", f_ifc, "application/octet-stream"), "ids_file": ("structural_baseline.ids", f_ids, "application/xml")})
    assert res.status_code == 200
    data = res.json()
    assert data["ids_title"] == "Al-Amin Structural Baseline IDS"
    assert data["passed_entities"] == 57


def test_export_bcfzip_archive():
    import io, zipfile
    with (FIXTURES / "duplex.ifc").open("rb") as f_ifc, (FIXTURES / "structural_baseline.ids").open("rb") as f_ids:
        res = client.post(
            "/api/v1/models/export-bcf",
            files={
                "ifc_file": ("duplex.ifc", f_ifc, "application/octet-stream"),
                "ids_file": ("structural_baseline.ids", f_ids, "application/xml"),
            },
        )
    assert res.status_code == 200
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        assert "bcf.version" in zf.namelist()
        assert any(n.endswith("/markup.bcf") for n in zf.namelist())
