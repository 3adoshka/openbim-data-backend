from __future__ import annotations

import io
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from app.services.ids_validator import validate_ifc_against_ids
from app.services.ifc_engine import ingest_ifc_file


def _topic_xml(guid: str, title: str, desc: str, ifc_guid: str | None) -> tuple[str, str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sel = (
        f'<Components><Selection><Component IfcGuid="{escape(ifc_guid)}" /></Selection></Components>'
        if ifc_guid
        else "<Components />"
    )
    markup = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Markup xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://roundtable.buildingsmart.org/schemas/BCF/2.1/markup.xsd">\n'
        f'  <Topic Guid="{guid}" TopicType="Issue" TopicStatus="Open">\n'
        f"    <Title>{escape(title)}</Title>\n"
        f"    <CreationDate>{now}</CreationDate>\n"
        f"    <Description>{escape(desc)}</Description>\n"
        "  </Topic>\n"
        f'  <Viewpoints><Viewpoint Guid="{guid}"><Viewpoint>viewpoint.bcfv</Viewpoint></Viewpoint></Viewpoints>\n'
        "</Markup>\n"
    )
    viewpoint = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<VisualizationInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://roundtable.buildingsmart.org/schemas/BCF/2.1/visinfo.xsd">\n'
        f"  {sel}\n"
        "</VisualizationInfo>\n"
    )
    return markup, viewpoint


def build_bcfzip_bytes(ifc_path: Path, ids_path: Path | None = None) -> bytes:
    topics: list[tuple[str, str, str | None]] = []
    report = ingest_ifc_file(ifc_path, check_geometry=True)
    for el in report.elements:
        if el.geometry_status != "valid":
            topics.append((
                f"Invalid Geometry: {el.ifc_class}",
                f"{el.ifc_class} ({el.global_id}) failed geometry audit: {el.geometry_status}",
                el.global_id,
            ))
    if ids_path is not None:
        ids_res = validate_ifc_against_ids(ifc_path, ids_path)
        for sp in ids_res["specifications"]:
            for fe in sp["failed_entities"]:
                topics.append((
                    f"IDS Failed [{sp['name']}]: {fe['ifc_class']}",
                    f"Failed IDS specification '{sp['name']}' for {fe['ifc_class']} (name={fe['name']}).",
                    fe["global_id"],
                ))
    if not topics:
        topics.append((
            "BIM Audit Summary",
            f"Model {ifc_path.name} passed geometry and IDS checks with score {report.quality_score}.",
            None,
        ))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "bcf.version",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Version xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="http://roundtable.buildingsmart.org/schemas/BCF/2.1/version.xsd" '
            'VersionId="2.1" />\n',
        )
        for title, desc, ifc_guid in topics:
            tid = str(uuid.uuid4())
            markup, viewpoint = _topic_xml(tid, title, desc, ifc_guid)
            zf.writestr(f"{tid}/markup.bcf", markup)
            zf.writestr(f"{tid}/viewpoint.bcfv", viewpoint)
    return buf.getvalue()
