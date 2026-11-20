from __future__ import annotations
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from app.db import SessionLocal, init_db, list_revision_ids, load_revision, save_revision
from app.schemas import BoqValidationReport, ModelIngestionReport, RevisionDiffReport
from app.services.boq_gate import validate_boq_csv
from app.services.ifc_engine import ingest_ifc_file
from app.services.storage import store_ifc_bytes
from app.services.versioning import diff_revisions

router = APIRouter(prefix="/api/v1", tags=["openbim"])

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/models/ingest", response_model=ModelIngestionReport)
async def ingest_model_endpoint(file: UploadFile = File(...), check_geometry: bool = Query(True), db: Session = Depends(get_db)) -> ModelIngestionReport:
    if not file.filename or not file.filename.lower().endswith(".ifc"):
        raise HTTPException(status_code=400, detail="Uploaded file must have a .ifc extension.")
    raw = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)
    try:
        report = ingest_ifc_file(tmp_path, check_geometry=check_geometry)
        report.filename = file.filename
        uri = store_ifc_bytes(report.revision_id, file.filename, raw)
        save_revision(db, report, uri)
        return report
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"IFC ingestion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

@router.get("/models/revisions", response_model=list[str])
def list_revisions(db: Session = Depends(get_db)) -> list[str]:
    return list_revision_ids(db)

@router.get("/models/revisions/{revision_id}", response_model=ModelIngestionReport)
def get_revision(revision_id: str, db: Session = Depends(get_db)) -> ModelIngestionReport:
    report = load_revision(db, revision_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Revision {revision_id} not found.")
    return report

@router.get("/models/diff", response_model=RevisionDiffReport)
def diff_model_revisions(base_id: str, target_id: str, db: Session = Depends(get_db)) -> RevisionDiffReport:
    base = load_revision(db, base_id)
    target = load_revision(db, target_id)
    if not base or not target:
        raise HTTPException(status_code=404, detail="One or both revision IDs not found.")
    return diff_revisions(base, target)

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
