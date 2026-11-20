# openbim-data-backend

[![CI](https://github.com/3adoshka/openbim-data-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/3adoshka/openbim-data-backend/actions/workflows/ci.yml)

Production-grade openBIM data engineering backend and headless CLI for **IFC2x3 / IFC4 / IFC4.3** ingestion, **OpenCASCADE** B-Rep/mesh geometry health auditing, **buildingSMART IDS v1.0** XML validation, **`GlobalId`** revision diffing, and **Pandera** Bill of Quantities (BoQ) quality gates.

## Architecture & Capabilities

- **IFC Ingestion, Geometry Audit & QTO (`POST /api/v1/models/ingest`)**: Validates every `IfcProduct` solid via `ifcopenshell.geom` (OpenCASCADE), audits metadata/material completeness, extracts `BaseQuantities` with automatic OpenCASCADE solid volume (`m3`) and surface area (`m2`) fallback, persists revision reports to PostgreSQL/SQLite, and archives raw `.ifc` artifacts to MinIO/S3.
- **buildingSMART IDS v1.0 Validation (`POST /api/v1/models/validate-ids`)**: Evaluates `.ifc` models directly against `.ids` XML specifications via `ifctester`.
- **buildingSMART BCF 2.1 Issue Export (`POST /api/v1/models/export-bcf`)**: Packages failed IDS specifications and invalid OpenCASCADE geometry elements into downloadable `.bcfzip` issue archives for Revit, Navisworks, Solibri, BIMcollab, and Bonsai.
- **GlobalId Revision Diffing (`GET /api/v1/models/diff`)**: Computes element-level additions, removals, geometry/material/QTO modifications, and net volume/area deltas between `base_id` and `target_id`.
- **BoQ Data Quality Gate (`POST /api/v1/boq/validate`)**: Enforces strict Pandera schema contracts on subcontractor CSV submissions (`item_code`, engineering `unit`, non-negative `quantity` & `unit_rate`) with row-level diagnostics.
- **Unified CLI (`python -m app.cli`)**: Headless CI/CD execution (`ingest`, `diff`, `boq`).

## Quickstart

### Local Python
```bash
pip install -e .
uvicorn app.main:app --reload
# Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
```

### Docker Stack (FastAPI + PostGIS + MinIO + Redis)
```bash
docker compose up --build
# API: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) | MinIO Console: [http://127.0.0.1:9001](http://127.0.0.1:9001)
```

### Headless CLI
```bash
python -m app.cli ingest tests/fixtures/duplex.ifc --summary-only
python -m app.cli diff tests/fixtures/sample.ifc tests/fixtures/duplex.ifc
python -m app.cli boq tests/fixtures/dirty_subcontractor_boq.csv
```
