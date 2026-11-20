from __future__ import annotations

from app.schemas import ModelIngestionReport, RevisionDiffReport


def diff_revisions(base: ModelIngestionReport, target: ModelIngestionReport) -> RevisionDiffReport:
    base_map = {e.global_id: e for e in base.elements if e.global_id}
    target_map = {e.global_id: e for e in target.elements if e.global_id}

    base_guids = set(base_map)
    target_guids = set(target_map)

    added = sorted(target_guids - base_guids)
    removed = sorted(base_guids - target_guids)

    modified: list[str] = []
    unchanged = 0
    for guid in sorted(base_guids & target_guids):
        b = base_map[guid]
        t = target_map[guid]
        if (
            b.ifc_class != t.ifc_class
            or b.name != t.name
            or b.geometry_status != t.geometry_status
            or b.ids_compliant != t.ids_compliant
            or abs(b.volume_m3 - t.volume_m3) > 1e-6
            or abs(b.area_m2 - t.area_m2) > 1e-6
        ):
            modified.append(guid)
        else:
            unchanged += 1

    qto_deltas = {
        k: round(target.qto_totals.get(k, 0.0) - base.qto_totals.get(k, 0.0), 4)
        for k in set(base.qto_totals) | set(target.qto_totals)
    }

    return RevisionDiffReport(
        base_revision_id=base.revision_id,
        target_revision_id=target.revision_id,
        added_guids=added,
        removed_guids=removed,
        modified_guids=modified,
        unchanged_count=unchanged,
        qto_deltas=qto_deltas,
    )
