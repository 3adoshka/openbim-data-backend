from __future__ import annotations

import hashlib
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.shape

from app.schemas import ElementAuditRecord, ModelIngestionReport


SKIP_CLASSES = ("IfcSpatialStructureElement", "IfcProject", "IfcSite")
QTO_TARGET_CLASSES = ("IfcWall", "IfcColumn", "IfcSlab", "IfcBeam", "IfcDoor", "IfcWindow")


def _extract_qto_metrics(elem: ifcopenshell.entity_instance) -> tuple[float, float]:
    volume = 0.0
    area = 0.0
    psets = ifcopenshell.util.element.get_psets(elem, qtos_only=True)
    for props in psets.values():
        for key, val in props.items():
            if not isinstance(val, (int, float)):
                continue
            k = key.lower()
            if "volume" in k and volume == 0.0:
                volume = float(val)
            elif "area" in k and area == 0.0:
                area = float(val)
    return volume, area


def ingest_ifc_file(filepath: str | Path, check_geometry: bool = True) -> ModelIngestionReport:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"IFC file not found: {path}")

    raw_bytes = path.read_bytes()
    revision_id = hashlib.sha256(raw_bytes).hexdigest()[:12]
    model = ifcopenshell.open(str(path))

    geom_settings = None
    if check_geometry:
        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set(geom_settings.USE_WORLD_COORDS, True)

    counts_by_class: dict[str, int] = {cls: len(model.by_type(cls)) for cls in QTO_TARGET_CLASSES}
    records: list[ElementAuditRecord] = []

    healthy_geom = 0
    corrupt_geom = 0
    ids_pass = 0
    ids_fail = 0
    total_volume = 0.0
    total_area = 0.0

    for elem in model.by_type("IfcProduct"):
        if any(elem.is_a(skip) for skip in SKIP_CLASSES):
            continue

        ifc_class = elem.is_a()
        name = elem.Name or "Unnamed"
        guid = elem.GlobalId or ""

        geom_status = "HEALTHY"
        geom_error: str | None = None
        geom_vol = 0.0
        geom_area = 0.0
        if check_geometry and geom_settings is not None:
            try:
                shape = ifcopenshell.geom.create_shape(geom_settings, elem)
                if not shape:
                    raise ValueError("Empty geometric representation")
                healthy_geom += 1
                geom_vol = float(ifcopenshell.util.shape.get_volume(shape.geometry))
                geom_area = float(ifcopenshell.util.shape.get_area(shape.geometry))
            except Exception as exc:
                geom_status = "CORRUPT_OR_MISSING"
                geom_error = str(exc).splitlines()[0]
                corrupt_geom += 1
        else:
            healthy_geom += 1

        psets = ifcopenshell.util.element.get_psets(elem)
        material = ifcopenshell.util.element.get_material(elem)
        has_meta = bool(psets or material)
        ids_ok = bool(elem.Name and guid and has_meta)
        if ids_ok:
            ids_pass += 1
        else:
            ids_fail += 1

        vol, area = _extract_qto_metrics(elem)
        if vol == 0.0 and geom_vol > 0.0:
            vol = geom_vol
        if area == 0.0 and geom_area > 0.0:
            area = geom_area
        total_volume += vol
        total_area += area

        records.append(
            ElementAuditRecord(
                global_id=guid,
                ifc_class=ifc_class,
                name=name,
                geometry_status=geom_status,  # type: ignore[arg-type]
                geometry_error=geom_error,
                ids_compliant=ids_ok,
                has_material_or_pset=has_meta,
                volume_m3=round(vol, 4),
                area_m2=round(area, 4),
            )
        )

    total = len(records)
    if total == 0:
        quality_score = 100.0
    else:
        geom_ratio = healthy_geom / total
        ids_ratio = ids_pass / total
        quality_score = round((0.6 * geom_ratio + 0.4 * ids_ratio) * 100.0, 2)

    return ModelIngestionReport(
        revision_id=revision_id,
        filename=path.name,
        schema_version=model.schema,
        total_products=total,
        healthy_geometry_count=healthy_geom,
        corrupt_geometry_count=corrupt_geom,
        ids_pass_count=ids_pass,
        ids_fail_count=ids_fail,
        quality_score=quality_score,
        counts_by_class=counts_by_class,
        qto_totals={
            "total_volume_m3": round(total_volume, 4),
            "total_area_m2": round(total_area, 4),
        },
        elements=records,
    )
