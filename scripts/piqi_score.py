# scripts/piqi_score.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from piqi_eval import PIQIEvaluator  # your existing PIQI evaluator


def load_yaml_path(p: str) -> str:
    # evaluator expects paths; keep as-is
    return str(Path(p).resolve())


def score_bundle(
    bundle: Dict[str, Any],
    *,
    sam_library_yaml: str,
    profile_yaml: str,
    plausibility_yaml: Optional[str] = None,
) -> Dict[str, Any]:
    evaluator = PIQIEvaluator(
        sam_library_path=load_yaml_path(sam_library_yaml),
        profile_path=load_yaml_path(profile_yaml),
        plausibility_path=load_yaml_path(plausibility_yaml) if plausibility_yaml else None,
    )
    return evaluator.evaluate_bundle(bundle)


def read_ndjson(path: str) -> List[Dict[str, Any]]:
    bundles: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                bundles.append(json.loads(line))
    return bundles


def write_json(obj: Any, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run PIQI evaluation on FHIR bundles")
    ap.add_argument("--in", dest="inp", required=True, help="Input NDJSON (bundles) or JSON (single bundle)")
    ap.add_argument("--out", dest="out", required=True, help="Output JSON")
    ap.add_argument("--sam", required=True, help="SAM library YAML (piqi_sam_library.yaml)")
    ap.add_argument("--profile", required=True, help="Profile YAML (e.g. profile_clinical_minimal.yaml)")
    ap.add_argument("--plausibility", required=False, default=None, help="Optional plausibility YAML")
    args = ap.parse_args()

    p = Path(args.inp)
    if p.suffix.lower() == ".ndjson":
        bundles = read_ndjson(args.inp)
        results = [
            score_bundle(b, sam_library_yaml=args.sam, profile_yaml=args.profile, plausibility_yaml=args.plausibility)
            for b in bundles
        ]
        write_json(results, args.out)
        print("[OK]", {"bundles": len(bundles), "out": args.out})
    else:
        bundle = json.loads(p.read_text(encoding="utf-8"))
        result = score_bundle(bundle, sam_library_yaml=args.sam, profile_yaml=args.profile, plausibility_yaml=args.plausibility)
        write_json(result, args.out)
        print("[OK]", {"out": args.out})
