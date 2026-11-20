from __future__ import annotations

from pathlib import Path
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

from app.schemas import BoqValidationReport, BoqViolation


BOQ_SCHEMA = DataFrameSchema(
    {
        "item_code": Column(str, Check.str_matches(r"^[A-Z0-9_\-\.]+$"), nullable=False),
        "description": Column(str, nullable=False),
        "unit": Column(str, Check.isin(["m3", "m2", "m", "ton", "pcs", "ls"]), nullable=False),
        "quantity": Column(float, Check.ge(0), nullable=False),
        "unit_rate": Column(float, Check.ge(0), nullable=False),
    },
    strict=True,
)


def validate_boq_csv(csv_path: str | Path) -> BoqValidationReport:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"BoQ CSV not found: {path}")

    df = pd.read_csv(path)
    total_rows = len(df)
    if total_rows == 0:
        return BoqValidationReport(
            filename=path.name,
            passed=False,
            total_rows=0,
            violation_count=1,
            quality_score=0.0,
            total_estimated_cost=0.0,
            violations=[
                BoqViolation(row_index=-1, column="*", check="non_empty", failure_value="empty_csv")
            ],
        )

    try:
        validated = BOQ_SCHEMA.validate(df, lazy=True)
        total_cost = float((validated["quantity"] * validated["unit_rate"]).sum())
        return BoqValidationReport(
            filename=path.name,
            passed=True,
            total_rows=total_rows,
            violation_count=0,
            quality_score=100.0,
            total_estimated_cost=round(total_cost, 2),
            violations=[],
        )
    except pa.errors.SchemaErrors as err:
        cases = err.failure_cases
        violations = [
            BoqViolation(
                row_index=int(row["index"]) if pd.notna(row["index"]) else -1,
                column=str(row["column"]),
                check=str(row["check"]),
                failure_value=str(row["failure_case"]),
            )
            for _, row in cases.iterrows()
        ]
        penalty = min(len(violations) / (total_rows * len(BOQ_SCHEMA.columns)), 1.0)
        score = round(max(0.0, (1.0 - penalty) * 100.0), 2)

        qty = pd.to_numeric(df.get("quantity", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        rate = pd.to_numeric(df.get("unit_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        est_cost = float((qty.clip(lower=0) * rate.clip(lower=0)).sum())

        return BoqValidationReport(
            filename=path.name,
            passed=False,
            total_rows=total_rows,
            violation_count=len(violations),
            quality_score=score,
            total_estimated_cost=round(est_cost, 2),
            violations=violations,
        )
