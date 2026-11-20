from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from app.services.boq_gate import validate_boq_csv
from app.services.ifc_engine import ingest_ifc_file
from app.services.versioning import diff_revisions

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openbim")
    sub = parser.add_subparsers(dest="command", required=True)
    p_in = sub.add_parser("ingest")
    p_in.add_argument("ifc_file", type=Path)
    p_in.add_argument("--no-geom", action="store_true")
    p_in.add_argument("--summary-only", action="store_true")
    p_df = sub.add_parser("diff")
    p_df.add_argument("base_ifc", type=Path)
    p_df.add_argument("target_ifc", type=Path)
    p_bq = sub.add_parser("boq")
    p_bq.add_argument("csv_file", type=Path)
    args = parser.parse_args(argv)
    if args.command == "ingest":
        r = ingest_ifc_file(args.ifc_file, check_geometry=not args.no_geom)
        print(json.dumps(r.model_dump(mode="json", exclude={"elements"} if args.summary_only else None), indent=2))
        return 0 if r.corrupt_geometry_count == 0 else 2
    if args.command == "diff":
        print(json.dumps(diff_revisions(ingest_ifc_file(args.base_ifc, check_geometry=False), ingest_ifc_file(args.target_ifc, check_geometry=False)).model_dump(mode="json"), indent=2))
        return 0
    if args.command == "boq":
        res = validate_boq_csv(args.csv_file)
        print(json.dumps(res.model_dump(mode="json"), indent=2))
        return 0 if res.passed else 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
