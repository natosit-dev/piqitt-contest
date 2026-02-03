# scripts/fhir_annotate.py
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import fhir_convert_backend as fhir  # where build_piqi_observation may exist


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def minimal_piqi_observation(piqi: Dict[str, Any], *, patient_ref: Optional[str] = None) -> Dict[str, Any]:
    # Fallback if your backend doesn't have build_piqi_observation()
    score = float(piqi.get("piqiIndex", 0.0))
    weighted = float(piqi.get("piqiWeightedIndex", 0.0))
    numer = int(piqi.get("numerator", 0))
    denom = int(piqi.get("denominator", 0))
    crit = int(piqi.get("criticalFailureCount", 0))

    obs = {
        "resourceType": "Observation",
        "id": f"piqi-{int(datetime.now().timestamp())}",
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey"}]}],
        "code": {"text": "PIQI Score"},
        "effectiveDateTime": utc_now_iso(),
        "valueQuantity": {"value": round(score * 100.0, 2), "unit": "%"},
        "component": [
            {"code": {"text": "piqiIndex"}, "valueDecimal": score},
            {"code": {"text": "piqiWeightedIndex"}, "valueDecimal": weighted},
            {"code": {"text": "numerator"}, "valueInteger": numer},
            {"code": {"text": "denominator"}, "valueInteger": denom},
            {"code": {"text": "criticalFailureCount"}, "valueInteger": crit},
        ],
    }
    if patient_ref:
        obs["subject"] = {"reference": patient_ref}
    return obs


def find_patient_reference(bundle: Dict[str, Any]) -> Optional[str]:
    for entry in bundle.get("entry", []):
        r = (entry or {}).get("resource") or {}
        if r.get("resourceType") == "Patient" and r.get("id"):
            return f"Patient/{r['id']}"
    return None


def add_piqi_to_bundle(bundle: Dict[str, Any], piqi: Dict[str, Any]) -> Dict[str, Any]:
    patient_ref = find_patient_reference(bundle)

    if hasattr(fhir, "build_piqi_observation"):
        piqi_obs = fhir.build_piqi_observation(bundle, piqi)
    else:
        piqi_obs = minimal_piqi_observation(piqi, patient_ref=patient_ref)

    bundle.setdefault("entry", []).append({"resource": piqi_obs})
    return bundle


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Annotate a FHIR Bundle with PIQI score (adds a PIQI Observation entry)")
    ap.add_argument("--bundle", required=True, help="Input bundle JSON")
    ap.add_argument("--piqi", required=True, help="PIQI result JSON")
    ap.add_argument("--out", required=True, help="Output bundle JSON")
    args = ap.parse_args()

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    piqi = json.loads(Path(args.piqi).read_text(encoding="utf-8"))

    out_bundle = add_piqi_to_bundle(bundle, piqi)
    Path(args.out).write_text(json.dumps(out_bundle, indent=2), encoding="utf-8")
    print("[OK]", {"out": args.out})
