# scripts/push_to_iris.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import fhir_convert_backend as fhir


def push_bundle(bundle: Dict[str, Any], base_url: str, token: str | None = None) -> Dict[str, Any]:
    # Prefer your existing helper (it already does the transaction wrapping)
    if hasattr(fhir, "maybe_send_to_iris"):
        return fhir.maybe_send_to_iris(bundle, iris_base_url=base_url, bearer_token=token)

    # Fallback: raw POST to FHIR endpoint (expects transaction bundle)
    import requests
    headers = {"Content-Type": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(base_url.rstrip("/") + "/", headers=headers, json=bundle, timeout=60)
    r.raise_for_status()
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else {"status_code": r.status_code}


def read_ndjson(path: str) -> List[Dict[str, Any]]:
    bundles: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                bundles.append(json.loads(line))
    return bundles


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="POST FHIR bundles to IRIS (FHIR endpoint)")
    ap.add_argument("--in", dest="inp", required=True, help="Input JSON (single bundle) or NDJSON (many bundles)")
    ap.add_argument("--base-url", required=False, default=os.getenv("IRIS_FHIR_BASE_URL", ""), help="IRIS FHIR base URL")
    ap.add_argument("--token", required=False, default=os.getenv("IRIS_TOKEN", None), help="Bearer token (optional)")
    args = ap.parse_args()

    if not args.base_url:
        raise SystemExit("Missing --base-url (or IRIS_FHIR_BASE_URL env var).")

    p = Path(args.inp)
    if p.suffix.lower() == ".ndjson":
        bundles = read_ndjson(args.inp)
        for i, b in enumerate(bundles, start=1):
            resp = push_bundle(b, args.base_url, args.token)
            print("[OK]", {"index": i, "response": resp if isinstance(resp, dict) else str(resp)})
    else:
        bundle = json.loads(p.read_text(encoding="utf-8"))
        resp = push_bundle(bundle, args.base_url, args.token)
        print("[OK]", {"response": resp if isinstance(resp, dict) else str(resp)})
