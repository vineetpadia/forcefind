#!/usr/bin/env python3
"""
Harvest and ingest force sensor datasheets from multiple manufacturers.
Updates data/documents.json, data/sensors.json, data/families.json, data/ocr-queue.json,
and data/coverage-gaps.json atomically.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def load_envelope(path: Path, list_key: str) -> dict[str, Any]:
    if not path.exists():
        return {list_key: []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {list_key: payload}
    if not isinstance(payload, dict) or not isinstance(payload.get(list_key), list):
        raise ValueError(f"Invalid {path}: expected object with '{list_key}' array")
    return payload

def upsert(items: list[dict[str, Any]], record: dict[str, Any], key: str) -> None:
    for index, item in enumerate(items):
        if item.get(key) == record[key]:
            items[index] = record
            return
    items.append(record)

def fetch_and_save_pdf(url: str, destination: Path) -> bytes | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 1000:
        data = destination.read_bytes()
        if b"%PDF" in data[:2048]:
            return data
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
        if b"%PDF" in data[:2048]:
            destination.write_bytes(data)
            return data
        else:
            print(f"URL did not return PDF: {url}")
            return None
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def ingest_datasheet(
    mfr: str,
    name: str,
    pdf_url: str | None,
    local_pdf_path: Path | None,
    product_url: str | None = None,
    sensor_type: str | None = None,
    form_factor: str | None = None,
    max_force_n: float | None = None,
    documents_dict: dict = None,
    sensors_dict: dict = None,
    families_dict: dict = None,
    queue_dict: dict = None,
    source_tag: str = "Catalog harvester",
) -> bool:
    mfr_slug = slug(mfr)
    name_slug = slug(name)
    destination = Path(f"datasheets/{mfr_slug}/{name_slug}.pdf")

    data = None
    if local_pdf_path and local_pdf_path.exists():
        data = local_pdf_path.read_bytes()
        if b"%PDF" not in data[:2048]:
            print(f"Local file is not PDF: {local_pdf_path}")
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        if local_pdf_path.resolve() != destination.resolve():
            shutil.copyfile(local_pdf_path, destination)
    elif pdf_url:
        data = fetch_and_save_pdf(pdf_url, destination)
        if not data:
            return False
    else:
        return False

    digest = hashlib.sha256(data).hexdigest()
    doc_id = f"sha256-{digest[:16]}"
    now = datetime.now(UTC).isoformat()
    source_urls = [pdf_url] if pdf_url else []
    product_pages = [product_url] if product_url else []

    # Document
    doc = {
        "id": doc_id,
        "sha256": digest,
        "pdfPath": destination.as_posix(),
        "bytes": len(data),
        "pages": 0,
        "mistralOcrPath": f"ocr_results/{mfr_slug}/{name_slug}.md",
        "mistralOcr": {
            "status": "pending_auth",
            "model": "mistral-ocr-latest",
        },
        "manufacturers": [mfr],
        "mpns": [name],
        "titles": [f"{mfr} {name} datasheet"],
        "sourceUrls": source_urls,
        "productPages": product_pages,
        "sources": [source_tag],
        "provenanceStatus": "verified_source_url" if source_urls else "local_file",
    }
    upsert(documents_dict["documents"], doc, "sha256")

    # Sensor record
    sensor_id = f"{mfr_slug}--{name_slug}"
    sensor = {
        "id": sensor_id,
        "recordType": "family" if "family" in name.lower() or "series" in name.lower() else "catalog_model",
        "model": name,
        "name": f"{mfr} {name}",
        "manufacturer": mfr,
        "status": "Active",
        "sensorType": sensor_type or "Force Sensor / Load Cell",
        "datasheetUrl": pdf_url,
        "datasheetUrls": source_urls,
        "pdfPath": destination.as_posix(),
        "ocrPath": f"ocr_results/{mfr_slug}/{name_slug}.md",
        "productUrl": product_url,
        "productUrls": product_pages,
        "sources": [source_tag],
        "datasheetStatus": "local_pdf",
        "mistralOcrStatus": "pending_auth",
    }
    if form_factor:
        sensor["formFactor"] = form_factor
    if max_force_n is not None:
        sensor["maxForceN"] = max_force_n
    upsert(sensors_dict["sensors"], sensor, "id")

    # Family record
    family_id = f"{mfr_slug}--{name_slug}--catalog-model"
    family = {
        "id": family_id,
        "manufacturer": mfr,
        "family": name,
        "familySource": "catalog_model",
        "recordCount": 1,
        "models": [name],
        "sensorTypes": [sensor_type] if sensor_type else ["Force Sensor / Load Cell"],
        "sources": [source_tag],
        "datasheetUrls": source_urls,
        "pdfPaths": [destination.as_posix()],
    }
    if max_force_n is not None:
        family["minMaxForceN"] = max_force_n
        family["maxMaxForceN"] = max_force_n
    upsert(families_dict["families"], family, "id")

    # Queue record
    queue_record = {
        "id": doc_id,
        "pdfPath": destination.as_posix(),
        "sha256": digest,
        "sourceUrls": source_urls,
        "status": "pending_auth",
        "ocrPath": f"ocr_results/{mfr_slug}/{name_slug}.md",
    }
    upsert(queue_dict["documents"], queue_record, "sha256")

    print(f"[OK] Ingested {mfr} {name} ({len(data)} bytes, sha256={digest[:8]})")
    return True

def main():
    documents_path = Path("data/documents.json")
    sensors_path = Path("data/sensors.json")
    families_path = Path("data/families.json")
    queue_path = Path("data/ocr-queue.json")
    gaps_path = Path("data/coverage-gaps.json")

    docs = load_envelope(documents_path, "documents")
    sensors = load_envelope(sensors_path, "sensors")
    families = load_envelope(families_path, "families")
    queue = load_envelope(queue_path, "documents")

    ingested_count = 0

    # 1. Harvest Burster
    burster_path = Path("data/burster-products.json")
    if burster_path.exists():
        bdata = json.loads(burster_path.read_text())
        for doc in bdata.get("documents", []):
            url = doc.get("url")
            model = doc.get("model", "Unknown")
            ppage = doc.get("productPage")
            local_p = Path(doc["file"]) if doc.get("file") else None
            if ingest_datasheet(
                mfr="Burster",
                name=f"Model {model}",
                pdf_url=url,
                local_pdf_path=local_p,
                product_url=ppage,
                sensor_type="Precision Load Cell",
                documents_dict=docs,
                sensors_dict=sensors,
                families_dict=families,
                queue_dict=queue,
                source_tag="Burster catalog harvest",
            ):
                ingested_count += 1

    # 2. Harvest Lorenz Messtechnik
    lorenz_path = Path("data/lorenz-products.json")
    if lorenz_path.exists():
        ldata = json.loads(lorenz_path.read_text())
        for prod in ldata.get("products", []):
            model = prod.get("model", "Unknown")
            ppage = prod.get("url")
            for ds in prod.get("datasheets", []):
                durl = ds.get("url")
                if durl and durl.endswith(".pdf"):
                    link_text = ds.get("linkText", "")
                    if "kabel" in durl.lower() or "cable" in link_text.lower():
                        continue  # skip pure cable datasheets
                    if ingest_datasheet(
                        mfr="Lorenz Messtechnik",
                        name=f"Model {model}",
                        pdf_url=durl,
                        local_pdf_path=None,
                        product_url=ppage,
                        sensor_type="Force Transducer",
                        documents_dict=docs,
                        sensors_dict=sensors,
                        families_dict=families,
                        queue_dict=queue,
                        source_tag="Lorenz Messtechnik catalog harvest",
                    ):
                        ingested_count += 1

    # 3. Harvest PCB Piezotronics
    pcb_path = Path("data/pcb-catalogs.json")
    if pcb_path.exists():
        pdata = json.loads(pcb_path.read_text())
        for doc in pdata.get("documents", []):
            url = doc.get("url")
            text = doc.get("text", "Catalog")
            local_p = Path(doc["file"]) if doc.get("file") else None
            if ingest_datasheet(
                mfr="PCB Piezotronics",
                name=text,
                pdf_url=url,
                local_pdf_path=local_p,
                product_url=doc.get("sourcePage"),
                sensor_type="Piezoelectric Force Sensor / Load Cell",
                documents_dict=docs,
                sensors_dict=sensors,
                families_dict=families,
                queue_dict=queue,
                source_tag="PCB Piezotronics catalog harvest",
            ):
                ingested_count += 1

    # Write updated envelope JSONs
    now = datetime.now(UTC).isoformat()
    docs["generatedAt"] = now
    docs["documentCount"] = len(docs["documents"])
    docs["uniqueSha256Count"] = len({item["sha256"] for item in docs["documents"]})
    atomic_json_write(documents_path, docs)

    sensors["generatedAt"] = now
    sensors["recordCount"] = len(sensors["sensors"])
    sensors["manufacturerCount"] = len({s.get("manufacturer") for s in sensors["sensors"]})
    atomic_json_write(sensors_path, sensors)

    families["generatedAt"] = now
    families["familyCount"] = len(families["families"])
    atomic_json_write(families_path, families)

    queue["generatedAt"] = now
    atomic_json_write(queue_path, queue)

    # Update coverage-gaps.json
    all_mfrs = sorted(list({s.get("manufacturer") for s in sensors["sensors"] if s.get("manufacturer")}))
    gaps_data = {
        "generatedAt": now,
        "coveredManufacturers": all_mfrs,
        "coveredManufacturerCount": len(all_mfrs),
        "priorityUncoveredManufacturers": [
            "Novatech Measurements",
            "Rice Lake Weighing Systems",
            "Minebea Intec",
            "Zemic",
            "ANYLOAD",
            "LAUMAS",
            "Thames Side Sensors",
            "Keli Sensing Technology",
            "Kistler",
            "HBK Nobel/BLH Nobel",
            "Sensata Technologies",
            "Kyowa Electronic Instruments",
            "Nippon Liniax",
            "A&D Company",
            "Tedea-Huntleigh legacy",
            "Sensortronics legacy",
            "Revere Transducers legacy",
            "Celtron legacy",
            "Loadstar Sensors",
            "Phidgets",
            "Forsentek",
            "SENSY",
            "Utilcell",
            "Pavone Sistemi",
            "Applied Measurements",
            "Sherborne Sensors",
            "Strainsert",
            "Kulite",
            "X-SENSORS",
            "XSENSOR",
            "Pressure Profile Systems"
        ],
        "method": "Current data/sensors.json names compared with official manufacturer catalog and datasheet portals; list remains open-ended."
    }
    atomic_json_write(gaps_path, gaps_data)

    print(f"\nSuccessfully harvested and ingested {ingested_count} datasheets!")
    print(f"Total Sensors: {len(sensors['sensors'])}")
    print(f"Total Unique PDFs: {docs['uniqueSha256Count']}")
    print(f"Total Manufacturers Covered: {len(all_mfrs)}")

if __name__ == "__main__":
    main()
