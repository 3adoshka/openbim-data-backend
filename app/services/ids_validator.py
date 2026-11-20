from __future__ import annotations
from pathlib import Path
import ifcopenshell
from ifctester import ids

def validate_ifc_against_ids(ifc_path: Path, ids_path: Path) -> dict:
    model = ifcopenshell.open(str(ifc_path))
    spec_file = ids.open(str(ids_path))
    spec_file.validate(model)
    specs = []
    passed_total = 0
    failed_total = 0
    for s in spec_file.specifications:
        p = len(s.passed_entities)
        f = len(s.failed_entities)
        passed_total += p
        failed_total += f
        specs.append({"name": s.name, "status": bool(s.status), "passed_count": p, "failed_count": f})
    return {"ids_title": spec_file.info.get("title", ids_path.name), "passed": failed_total == 0, "passed_entities": passed_total, "failed_entities": failed_total, "specifications": specs}
