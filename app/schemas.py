from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


class ElementAuditRecord(BaseModel):
    global_id: str
    ifc_class: str
    name: str
    geometry_status: Literal["HEALTHY", "CORRUPT_OR_MISSING"]
    geometry_error: str | None = None
    ids_compliant: bool
    has_material_or_pset: bool
    volume_m3: float = 0.0
    area_m2: float = 0.0


class ModelIngestionReport(BaseModel):
    revision_id: str
    filename: str
    schema_version: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_products: int
    healthy_geometry_count: int
    corrupt_geometry_count: int
    ids_pass_count: int
    ids_fail_count: int
    quality_score: float
    counts_by_class: dict[str, int]
    qto_totals: dict[str, float]
    elements: list[ElementAuditRecord]


class RevisionDiffReport(BaseModel):
    base_revision_id: str
    target_revision_id: str
    added_guids: list[str]
    removed_guids: list[str]
    modified_guids: list[str]
    unchanged_count: int
    qto_deltas: dict[str, float]


class BoqViolation(BaseModel):
    row_index: int
    column: str
    check: str
    failure_value: str


class BoqValidationReport(BaseModel):
    filename: str
    passed: bool
    total_rows: int
    violation_count: int
    quality_score: float
    total_estimated_cost: float
    violations: list[BoqViolation]
