# scripts/fhir_convert.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure repo root is importable (so we can import fhir_convert_backend.py at root)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import fhir_convert_backend as fhir  # uses your existing converter


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_hl7_messages(hl7_text: str) -> List[str]:
    # use your backend splitter if present
    if hasattr(fhir, "split_messages"):
        return fhir.split_messages(hl7_text)
    # fallback (simple): split on repeated MSH|
    parts = []
    buf = []
    for line in hl7_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith("MSH|") and buf:
            parts.append("\r".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        parts.append("\r".join(buf))
    return [p.strip() for p in parts if p.strip()]


def convert_hl7_text_to_bundles(hl7_text: str) -> List[Dict[str, Any]]:
    messages = split_hl7_messages(hl7_text)
    bundles: List[Dict[str, Any]] = []

    for msg in messages:
        try:
            bundle = fhir.convert_message_to_bundle(msg)
            if bundle:
                bundles.append(bundle)
        except Exception as e:
            # Don't swallow: surface the failure to caller
            raise RuntimeError(f"Failed to convert HL7 message to FHIR bundle: {e}") from e

    return bundles


def convert_file(path: str) -> List[Dict[str, Any]]:
    return convert_hl7_text_to_bundles(read_text(Path(path)))


def write_ndjson(bundles: List[Dict[str, Any]], out_path: str) -> None:
    import json
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for b in bundles:
            f.write(json.dumps(b))
            f.write("\n")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert HL7 v2 text/files into FHIR message Bundles")
    ap.add_argument("--in", dest="inp", required=True, help="HL7 file path")
    ap.add_argument("--out", dest="out", required=True, help="Output NDJSON file")
    args = ap.parse_args()

    bundles = convert_file(args.inp)
    write_ndjson(bundles, args.out)
    print("[OK]", {"bundles": len(bundles), "out": args.out})
