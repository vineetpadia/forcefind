#!/usr/bin/env python3
"""
Build compiled selector-data.json for ForceFind spreadsheet UI.
Aggregates sensors.json, families.json, documents.json, and ocr_results.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SENSORS_PATH = Path("data/sensors.json")
FAMILIES_PATH = Path("data/families.json")
DOCUMENTS_PATH = Path("data/documents.json")
OCR_DIR = Path("ocr_results")
OUTPUT_PATH = Path("public/selector-data.json")
ROOT_OUTPUT_PATH = Path("data/selector-data.json")

def format_force(newtons: float | None) -> str:
    if newtons is None or newtons <= 0:
        return "Unspecified"
    if newtons >= 1_000_000:
        return f"{newtons/1_000_000:.2f} MN ({newtons/9806.65:.1f} tf)"
    elif newtons >= 1000:
        return f"{newtons/1000:.2f} kN ({newtons/9.80665:.1f} kgf / {newtons/4.44822:.1f} lbf)"
    else:
        return f"{newtons:.1f} N ({newtons/9.80665:.1f} kgf / {newtons/4.44822:.1f} lbf)"

def main() -> None:
    sensors_envelope = json.loads(SENSORS_PATH.read_text(encoding="utf-8"))
    docs_envelope = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))
    families_envelope = json.loads(FAMILIES_PATH.read_text(encoding="utf-8"))

    sensors = sensors_envelope.get("sensors", [])
    docs = docs_envelope.get("documents", [])
    families = families_envelope.get("families", [])

    # Map sha256 to doc
    doc_by_sha = {d["sha256"]: d for d in docs if "sha256" in d}
    doc_by_pdf = {d.get("pdfPath"): d for d in docs if d.get("pdfPath")}

    # Pre-cache OCR files content or snippets
    ocr_texts: dict[str, str] = {}
    for ocr_file in OCR_DIR.rglob("*.md"):
        try:
            ocr_texts[ocr_file.as_posix()] = ocr_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    records: list[dict[str, Any]] = []
    types_set: set[str] = set()
    mfrs_set: set[str] = set()

    for idx, s in enumerate(sensors, 1):
        mfr = s.get("manufacturer") or s.get("mfr") or "Unknown Manufacturer"
        name = s.get("model") or s.get("name") or s.get("mpn") or f"Sensor #{idx}"
        stype = s.get("type") or s.get("sensorType") or s.get("category") or "Load Cell / Force Transducer"
        form = s.get("formFactor") or s.get("form_factor") or "Standard"
        max_force = s.get("maxForce") or s.get("max_force") or s.get("capacityNewtons")
        price = s.get("price") or s.get("unitPrice")
        pdf_path = s.get("pdfPath") or s.get("localPdf") or s.get("local_pdf")
        ocr_path = s.get("ocrPath") or s.get("mistralOcrPath")
        remote_url = s.get("datasheetUrl") or s.get("remoteUrl") or s.get("productUrl")
        family = s.get("family") or name

        # Get OCR content if available
        ocr_content = ""
        if ocr_path and ocr_path in ocr_texts:
            ocr_content = ocr_texts[ocr_path]
        elif pdf_path:
            doc = doc_by_pdf.get(pdf_path)
            if doc and doc.get("mistralOcrPath") in ocr_texts:
                ocr_path = doc.get("mistralOcrPath")
                ocr_content = ocr_texts[ocr_path]

        # Extract brief OCR snippet (first 300 chars excluding header)
        ocr_snippet = ""
        if ocr_content:
            lines = [line.strip() for line in ocr_content.splitlines() if line.strip() and not line.startswith("#")]
            ocr_snippet = " ".join(lines[:6])[:300]

        records.append({
            "id": f"s-{idx}",
            "name": name,
            "manufacturer": mfr,
            "type": stype,
            "formFactor": form,
            "maxForceN": max_force,
            "maxForceFormatted": format_force(max_force),
            "price": price,
            "pdfPath": pdf_path,
            "ocrPath": ocr_path,
            "remoteUrl": remote_url,
            "ocrSnippet": ocr_snippet,
            "ocrText": ocr_content, # included for in-browser client searching
            "family": family,
            "sourceTag": s.get("sourceTag") or s.get("source") or "ForceFind Audit"
        })

        mfrs_set.add(mfr)
        types_set.add(stype)

    output_data = {
        "metadata": {
            "totalSensors": len(records),
            "totalManufacturers": len(mfrs_set),
            "totalFamilies": len(families),
            "totalDocuments": len(docs),
            "ocrCompletedCount": sum(1 for r in records if r["ocrPath"]),
            "generatedAt": sensors_envelope.get("generatedAt")
        },
        "manufacturers": sorted(list(mfrs_set)),
        "types": sorted(list(types_set)),
        "sensors": records
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_bytes = json.dumps(output_data, indent=2).encode("utf-8")
    OUTPUT_PATH.write_bytes(json_bytes)
    ROOT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROOT_OUTPUT_PATH.write_bytes(json_bytes)

    print(f"Successfully generated selector dataset:")
    print(f" - Output: {OUTPUT_PATH} ({len(json_bytes)/1024/1024:.2f} MB)")
    print(f" - Sensors: {len(records)}")
    print(f" - Manufacturers: {len(mfrs_set)}")
    print(f" - OCR completed items: {output_data['metadata']['ocrCompletedCount']}")

if __name__ == "__main__":
    main()
