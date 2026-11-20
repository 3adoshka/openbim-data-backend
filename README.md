# openbim-data-backend

Open-source Python backend and CLI for ingesting, validating, diffing, and serving IFC / openBIM and BoQ data.

## Endpoints & CLI
- `POST /api/v1/models/ingest` — IFC parsing, OpenCASCADE geometry health audit, IDS checks, and QTO summary
- `GET /api/v1/models/diff` — GlobalId-level model revision diffing
- `POST /api/v1/boq/validate` — Pandera data quality gate for subcontractor BoQ CSVs
- `python -m app.cli ingest <file.ifc> --summary-only` — Headless CLI audit
