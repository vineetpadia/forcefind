#!/usr/bin/env python3
"""Ingest one force-sensor PDF and OCR it with Mistral OCR."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import tomllib
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from mistralai import Mistral
except ImportError:
    from mistralai.client import Mistral

OCR_MODEL = "mistral-ocr-latest"
CONFIG_PATH = Path.home() / ".codex" / "config.toml"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def api_key() -> str:
    key = os.environ.get("MISTRAL_API_KEY")
    if key:
        return key
    if CONFIG_PATH.exists():
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        key = (
            config.get("mcp_servers", {})
            .get("mistral_ocr", {})
            .get("env", {})
            .get("MISTRAL_API_KEY")
        )
        if key:
            return key
    raise RuntimeError("MISTRAL_API_KEY is not configured")


def fetch_pdf(source: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        destination.write_bytes(data)
    elif Path(source).resolve() != destination.resolve():
        shutil.copyfile(Path(source), destination)
    if b"%PDF" not in destination.read_bytes()[:2048]:
        destination.unlink(missing_ok=True)
        raise ValueError(f"Source is not a PDF: {source}")


def run_mistral_ocr(pdf_path: Path) -> Any:
    import random
    client = Mistral(api_key=api_key())
    uploaded = None
    for upload_attempt in range(5):
        try:
            with pdf_path.open("rb") as stream:
                uploaded = client.files.upload(
                    file={"file_name": pdf_path.name, "content": stream},
                    purpose="ocr",
                )
            break
        except Exception as error:
            if ("429" in str(error) or "Rate limit" in str(error)) and upload_attempt < 4:
                time.sleep(2**upload_attempt + random.uniform(0.5, 1.5))
            else:
                raise

    if uploaded is None:
        raise RuntimeError("Failed to upload PDF to Mistral")

    last_error: Exception | None = None
    for attempt in range(6):
        try:
            signed_url = client.files.get_signed_url(file_id=uploaded.id)
            return client.ocr.process(
                model=OCR_MODEL,
                document={"type": "document_url", "document_url": signed_url.url},
            )
        except Exception as error:
            last_error = error
            err_str = str(error)
            if ("404" in err_str or "429" in err_str or "500" in err_str or "Rate limit" in err_str or "rate_limited" in err_str or "Service unavailable" in err_str) and attempt < 5:
                time.sleep(2**attempt + random.uniform(0.5, 1.5))
            else:
                raise
    raise last_error or RuntimeError("Mistral OCR failed")


def response_markdown(response: Any, pdf_path: Path, digest: str) -> str:
    blocks = [
        f"# {pdf_path.stem}",
        "",
        f"- PDF: `{pdf_path.as_posix()}`",
        f"- SHA-256: `{digest}`",
        f"- OCR model: `{OCR_MODEL}`",
        "",
    ]
    for number, page in enumerate(response.pages, 1):
        markdown = re.sub(r"!\[[^]]*\]\([^)]+\)", "", page.markdown or "").strip()
        blocks.extend((f"## Page {number}", "", markdown, ""))
    return "\n".join(blocks).rstrip() + "\n"


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Authoritative PDF URL")
    source.add_argument("--file", help="Local PDF path")
    parser.add_argument("--name", required=True, help="Manufacturer model or family")
    parser.add_argument("--mfr", required=True, help="Manufacturer")
    parser.add_argument("--type", help="Published sensor technology or type")
    parser.add_argument("--form-factor", help="Published form factor")
    parser.add_argument("--max-force", type=float, help="Published maximum force in newtons")
    parser.add_argument("--price", type=float, help="Observed unit price in USD")
    parser.add_argument("--product-url", help="Authoritative product page")
    args = parser.parse_args()

    source_value = args.url or args.file
    assert source_value is not None
    manufacturer_slug = slug(args.mfr)
    model_slug = slug(args.name)
    pdf_path = Path("datasheets") / manufacturer_slug / f"{model_slug}.pdf"
    ocr_path = Path("ocr_results") / manufacturer_slug / f"{model_slug}.md"

    fetch_pdf(source_value, pdf_path)
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    response = run_mistral_ocr(pdf_path)
    ocr_path.parent.mkdir(parents=True, exist_ok=True)
    ocr_path.write_text(response_markdown(response, pdf_path, digest), encoding="utf-8")

    now = datetime.now(UTC).isoformat()
    source_urls = [args.url] if args.url else []
    product_pages = [args.product_url] if args.product_url else []

    documents_path = Path("data/documents.json")
    documents = load_envelope(documents_path, "documents")
    document = {
        "id": f"sha256-{digest[:16]}",
        "sha256": digest,
        "pdfPath": pdf_path.as_posix(),
        "bytes": pdf_path.stat().st_size,
        "pages": len(response.pages),
        "mistralOcrPath": ocr_path.as_posix(),
        "mistralOcr": {"status": "complete", "model": OCR_MODEL, "completedAt": now},
        "manufacturers": [args.mfr],
        "mpns": [args.name],
        "titles": [args.name],
        "sourceUrls": source_urls,
        "productPages": product_pages,
        "sources": ["ingest_datasheet.py"],
        "provenanceStatus": "verified_source_url" if source_urls else "local_file",
    }
    upsert(documents["documents"], document, "sha256")
    documents["generatedAt"] = now
    documents["documentCount"] = len(documents["documents"])
    documents["uniqueSha256Count"] = len({item["sha256"] for item in documents["documents"]})
    atomic_json_write(documents_path, documents)

    sensors_path = Path("data/sensors.json")
    sensors = load_envelope(sensors_path, "sensors")
    sensor_id = f"{manufacturer_slug}--{model_slug}"
    sensor = {
        "id": sensor_id,
        "recordType": "family",
        "model": args.name,
        "name": args.name,
        "manufacturer": args.mfr,
        "status": "Cataloged",
        "datasheetUrl": args.url,
        "datasheetUrls": source_urls,
        "pdfPath": pdf_path.as_posix(),
        "ocrPath": ocr_path.as_posix(),
        "productUrl": args.product_url,
        "productUrls": product_pages,
        "sources": ["ingest_datasheet.py"],
        "datasheetStatus": "local_pdf",
        "mistralOcrStatus": "complete",
    }
    optional = {
        "sensorType": args.type,
        "formFactor": args.form_factor,
        "maxForceN": args.max_force,
        "priceUSD": args.price,
    }
    sensor.update({key: value for key, value in optional.items() if value is not None})
    sensor = {key: value for key, value in sensor.items() if value is not None}
    upsert(sensors["sensors"], sensor, "id")
    sensors["generatedAt"] = now
    sensors["recordCount"] = len(sensors["sensors"])
    atomic_json_write(sensors_path, sensors)

    families_path = Path("data/families.json")
    families = load_envelope(families_path, "families")
    family = {
        "id": f"{sensor_id}--catalog-model",
        "manufacturer": args.mfr,
        "family": args.name,
        "familySource": "catalog_model",
        "recordCount": 1,
        "models": [args.name],
        "sensorTypes": [args.type] if args.type else [],
        "sources": ["ingest_datasheet.py"],
        "datasheetUrls": source_urls,
        "pdfPaths": [pdf_path.as_posix()],
        "minMaxForceN": args.max_force,
        "maxMaxForceN": args.max_force,
    }
    upsert(families["families"], family, "id")
    families["generatedAt"] = now
    families["familyCount"] = len(families["families"])
    atomic_json_write(families_path, families)

    queue_path = Path("data/ocr-queue.json")
    queue = load_envelope(queue_path, "documents")
    queue_record = {
        "id": document["id"],
        "pdfPath": pdf_path.as_posix(),
        "sha256": digest,
        "sourceUrls": source_urls,
        "status": "complete",
        "ocrPath": ocr_path.as_posix(),
    }
    upsert(queue["documents"], queue_record, "sha256")
    queue["generatedAt"] = now
    queue["model"] = OCR_MODEL
    atomic_json_write(queue_path, queue)

    print(f"Ingested {args.mfr} {args.name}: {len(response.pages)} OCR pages")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        raise SystemExit(1)
