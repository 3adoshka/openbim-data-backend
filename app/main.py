from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="openbim-data-backend",
    description=(
        "Open-source Python backend for ingesting, validating, enriching, "
        "versioning, and serving IFC/openBIM data."
    ),
    version="0.2.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.2.0"}
