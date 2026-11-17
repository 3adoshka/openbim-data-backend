# openbim-data-backend

An open-source Python backend for ingesting, validating, enriching, versioning, and serving IFC/openBIM data.

## What it does

`openbim-data-backend` turns IFC models into structured, queryable BIM data.

It is designed for headless openBIM workflows:

```text
IFC upload
  -> IFC validation
  -> element and property extraction
  -> unit normalization
  -> PostgreSQL / PostGIS storage
  -> IDS compliance checking
  -> BCF issue generation
  -> REST API
```

## Why it exists

BIM teams often receive IFC models from architects, structural engineers, and MEP consultants, then manually check whether required properties, classifications, and quantities are present.

This project automates that workflow using open standards and open-source tools:

- **IFC** for model data
- **IDS** for machine-readable information requirements
- **BCF** for coordination issues
- **bSDD** for standardized classification and property dictionaries
- **PostgreSQL + PostGIS** for persistent, spatially queryable data
- **IfcOpenShell** for IFC parsing, validation, and automation

## Planned features

- [ ] IFC upload and revision tracking
- [ ] IFC validation reports
- [ ] Element, property, and classification extraction
- [ ] Spatial hierarchy extraction
- [ ] Unit normalization
- [ ] PostgreSQL and PostGIS storage
- [ ] IDS compliance checks
- [ ] Automated BCF issue generation
- [ ] bSDD enrichment
- [ ] Model revision diffing
- [ ] Geometry metadata and Fragments export
- [ ] Docker Compose development environment

## Tech stack

- Python
- FastAPI
- IfcOpenShell
- PostgreSQL
- PostGIS
- SQLAlchemy
- Alembic
- Celery
- Redis
- MinIO
- Docker Compose
- pytest

## Status

**Early development.** The first milestone is a local Docker-based service that accepts an IFC file, validates it, and returns a structured validation report.

## License

MIT
