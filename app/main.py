from fastapi import FastAPI

app = FastAPI(
    title="openbim-data-backend",
    description=(
        "Open-source backend for ingesting, validating, enriching, "
        "versioning, and serving IFC/openBIM data."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}