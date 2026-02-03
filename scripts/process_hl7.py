# scripts/process_hl7.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.fhir_convert import convert_file
from scripts.piqi_score import score_bundle
from scripts.fhir_annotate import add_piqi_to_bundle
from scripts.push_to_iris import push_bundle


def write_ndjson(objs: List[Dict[str, Any]], out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for o in objs:
            f.write(json.dumps(o))
            f.write("\n")


if __name__ == "__main__":
    import argparse
    import os

    ap = argparse.ArgumentParser(description="HL7 -> FHIR -> PIQI -> annotate -> (optional) push to IRIS")
    ap.add_argument("--hl7", required=True, help="Input HL7 file (can contain multiple messages)")
    ap.add_argument("--sam", required=True, help="piqi_sam_library.yaml")
    ap.add_argument("--profile", required=True, help="profile YAML (e.g. profile_clinical_minimal.yaml)")
    ap.add_argument("--plausibility", default=None, help="Optional plausibility.yaml")
    ap.add_argument("--out-bundles", required=True, help="Output NDJSON of annotated bundles")
    ap.add_argument("--out-scores", required=True, help="Output NDJSON of PIQI results")
    ap.add_argument("--push", action="store_true", help="If set, POST annotated bundles to IRIS")
    ap.add_argument("--iris-base-url", default=os.getenv("IRIS_FHIR_BASE_URL", ""), help="IRIS FHIR base URL")
    ap.add_argument("--iris-token", default=os.getenv("IRIS_TOKEN", None), help="Bearer token (optional)")
    args = ap.parse_args()

    bundles = convert_file(args.hl7)

    scores: List[Dict[str, Any]] = []
    annotated: List[Dict[str, Any]] = []

    for b in bundles:
        piqi = score_bundle(
            b,
            sam_library_yaml=args.sam,
            profile_yaml=args.profile,
            plausibility_yaml=args.plausibility,
        )
        scores.append(piqi)
        annotated_bundle = add_piqi_to_bundle(b, piqi)
        annotated.append(annotated_bundle)

        if args.push:
            if not args.iris_base_url:
                raise SystemExit("Missing --iris-base-url (or IRIS_FHIR_BASE_URL env var).")
            push_bundle(annotated_bundle, args.iris_base_url, args.iris_token)

    write_ndjson(scores, args.out_scores)
    write_ndjson(annotated, args.out_bundles)

    print("[OK]", {"messages": len(bundles), "scores_out": args.out_scores, "bundles_out": args.out_bundles, "pushed": bool(args.push)})
