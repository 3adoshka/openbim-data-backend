from __future__ import annotations

import tempfile
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas import BoqValidationReport, ModelIngestionReport, RevisionDiffReport
from app.services.boq_gate import validate_boq_csv
from app.services.ifc_engine import ingest_ifc_file
from app.services.versioning import diff_revisions

router = APIRouter(prefix="/api/v1", tags=["openbim"])

_REVISION_STORE: dict[str, ModelIngestionReport] = {}


@router.post("/models/ingest", response_model=ModelIngestionReport)
async def ingest_model_endpoint(
    file: UploadFile = File(...),
    check_geometry: bool = Query(True, description="Run OpenCASCADE B-Rep/mesh health validation"),
) -> ModelIngestionReport:
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Uploaded file must have a .ifc extension.")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        report = ingest_ifc_file(tmp_path, check_geometry=check_geometry)
        report.filename = file.filename
        _REVISION_STORE[report.revision_id] = report
        return report
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"IFC ingestion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/models/revisions", response_model=list[str])
def list_revisions() -> list[str]:
    return list(_REVISION_STORE.keys())


@router.get("/models/revisions/{revision_id}", response_model=ModelIngestionReport)
def get_revision(revision_id: str) -> ModelIngestionReport:
    if revision_id not in _REVISION_STORE:
        raise HTTPException(status_code=404, detail=f"Revision '{revision_id}' not found.")
    return _REVISION_STORE[revision_id]


@router.get("/models/diff", response_model=RevisionDiffReport)
def diff_model_revisions(base_id: str, target_id: str) -> RevisionDiffReport:
    if base_id not in _REVISION_STORE or target_id not in _REVISION_STORE:
        raise HTTPException(status_code=404, detail="One or both revision IDs not found.")
    return diff_revisions(_REVISION_STORE[base_id], _REVISION_STORE[target_id])


@router.post("/boq/validate", response_model=BoqValidationReport)
async def validate_boq_endpoint(file: UploadFile = File(...)) -> BoqValidationReport:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must have a .csv extension.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        report = validate_boq_csv(tmp_path)
        report.filename = file.filename
        return report
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"BoQ validation failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
