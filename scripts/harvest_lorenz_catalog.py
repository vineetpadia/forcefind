#!/usr/bin/env python3
"""Harvest every Lorenz force-sensor/load-cell product and its sensor datasheets."""

from __future__ import annotations

import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SENSORS_PATH = Path("data/sensors.json")
FAMILIES_PATH = Path("data/families.json")
DOCUMENTS_PATH = Path("data/documents.json")
QUEUE_PATH = Path("data/ocr-queue.json")
OCR_SPECS_PATH = Path("data/ocr-specifications.json")
MANIFEST_PATH = Path("data/lorenz-products.json")
PDF_ROOT = Path("datasheets/lorenz-messtechnik")
SOURCE_TAG = "Lorenz Messtechnik catalog harvest"
MANUFACTURER = "Lorenz Messtechnik"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SOURCE_PAGES = [
    "https://www.lorenz-messtechnik.de/english/products/force-sensors.php",
    "https://www.lorenz-messtechnik.de/english/products/tension_force_sensors.php",
    "https://www.lorenz-messtechnik.de/english/products/compression_force_sensors.php",
    "https://www.lorenz-messtechnik.de/english/products/compression_tension.php",
    "https://www.lorenz-messtechnik.de/english/products/special_sensors.php",
    "https://www.lorenz-messtechnik.de/english/products/torque_static_force.php",
    "https://www.lorenz-messtechnik.de/english/products/torque_rotary_force.php",
    "https://www.lorenz-messtechnik.de/english/products/load-cells.php",
    "https://www.lorenz-messtechnik.de/english/products/lc_single-point.php",
    "https://www.lorenz-messtechnik.de/english/products/lc_compression.php",
    "https://www.lorenz-messtechnik.de/english/products/lc_tension-compression.php",
    "https://www.lorenz-messtechnik.de/english/products/lc_bending_shear-beam.php",
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON envelope: {path}")
    return payload


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def fetch(url: str) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/" in content_type or "xml" in content_type:
                response.encoding = "utf-8"
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < 3:
                time.sleep(2**attempt)
    raise last_error or RuntimeError(f"Failed to fetch {url}")


def discover_products() -> list[str]:
    products: set[str] = set()
    for source_url in SOURCE_PAGES:
        response = fetch(source_url)
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            url = urljoin(response.url, anchor.get("href")).split("#", 1)[0]
            if re.search(r"/english/products/[^/]+/[^/?#]+\.php$", url):
                products.add(url)
    return sorted(products)


def product_model(url: str) -> str:
    return unquote(urlparse(url).path.rsplit("/", 1)[-1].removesuffix(".php")).upper()


def extract_product(url: str) -> dict[str, Any]:
    response = fetch(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = re.sub(r"\s+", " ", soup.title.get_text(" ", strip=True) if soup.title else "").strip()
    sensor_datasheets: list[dict[str, str]] = []
    accessory_pdfs: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        page_pdf_url = urljoin(response.url, anchor.get("href")).split("#", 1)[0]
        if ".pdf" not in page_pdf_url.lower() or page_pdf_url in seen:
            continue
        seen.add(page_pdf_url)
        link_text = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
        alternate_url = None
        if re.fullmatch(r"[^/]+\.pdf", link_text, re.IGNORECASE):
            candidate = urljoin(page_pdf_url, link_text)
            if candidate != page_pdf_url:
                alternate_url = candidate
        item = {
            "url": page_pdf_url,
            "linkText": link_text,
            **({"alternateUrl": alternate_url} if alternate_url else {}),
        }
        path = urlparse(page_pdf_url).path.lower()
        if re.search(r"/pdfdatbl/(?:f|waegung|mehrkomp)/", path):
            sensor_datasheets.append(item)
        else:
            accessory_pdfs.append(item)
    if not sensor_datasheets:
        raise RuntimeError(f"No sensor datasheet found on {url}")
    return {
        "url": response.url,
        "status": "ok",
        "httpStatus": response.status_code,
        "model": product_model(response.url),
        "title": title,
        "datasheets": sensor_datasheets,
        "accessoryPdfs": accessory_pdfs,
    }


def variant_model(datasheet_url: str) -> str:
    filename = unquote(urlparse(datasheet_url).path.rsplit("/", 1)[-1]).removesuffix(".pdf")
    match = re.search(r"_(w-[a-z0-9-]+?)(?:_en)?$", filename, re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot derive variant model from {datasheet_url}")
    return match.group(1).upper()


def download_pdf(datasheet: dict[str, str], destination: Path) -> tuple[bytes, str, str]:
    attempted: list[str] = []
    for url in (datasheet["url"], datasheet.get("alternateUrl")):
        if not url:
            continue
        attempted.append(url)
        response = fetch(url)
        data = response.content
        if b"%PDF" not in data[:2048]:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return data, hashlib.sha256(data).hexdigest(), response.url
    raise ValueError(f"URLs did not return a PDF: {attempted}")


def upsert(items: list[dict[str, Any]], record: dict[str, Any], key: str) -> None:
    for index, item in enumerate(items):
        if item.get(key) == record[key]:
            items[index] = record
            return
    items.append(record)


def migrate_spec_targets() -> None:
    if not OCR_SPECS_PATH.exists():
        return
    payload = load(OCR_SPECS_PATH)
    changed = False
    for document in payload.get("documents", []):
        for product in document.get("products", []):
            if product.get("targetId") == "lorenz-messtechnik--model-w-ak":
                product["targetId"] = "lorenz-messtechnik--model-w-ak-60"
                changed = True
    if changed:
        atomic_write(OCR_SPECS_PATH, payload)


def ingest(products: list[dict[str, Any]]) -> dict[str, int]:
    sensors = load(SENSORS_PATH)
    families = load(FAMILIES_PATH)
    documents = load(DOCUMENTS_PATH)
    queue = load(QUEUE_PATH)
    old_documents = {
        document["sha256"]: document
        for document in documents["documents"]
        if MANUFACTURER in document.get("manufacturers", [])
    }
    old_queue = {
        record["sha256"]: record
        for record in queue["documents"]
        if str(record.get("pdfPath", "")).startswith(f"{PDF_ROOT.as_posix()}/")
    }

    sensors["sensors"] = [
        record for record in sensors["sensors"] if record.get("manufacturer") != MANUFACTURER
    ]
    families["families"] = [
        record for record in families["families"] if record.get("manufacturer") != MANUFACTURER
    ]
    documents["documents"] = [
        record for record in documents["documents"] if MANUFACTURER not in record.get("manufacturers", [])
    ]
    queue["documents"] = [
        record
        for record in queue["documents"]
        if not str(record.get("pdfPath", "")).startswith(f"{PDF_ROOT.as_posix()}/")
    ]

    now = datetime.now(UTC).isoformat()
    added = 0
    reused_ocr = 0
    pending_ocr = 0
    for product in products:
        load_cell = "/lc_" in product["url"]
        for index, datasheet in enumerate(product["datasheets"]):
            model = (
                variant_model(datasheet["url"])
                if len(product["datasheets"]) > 1
                else product["model"]
            )
            name = f"Model {model}"
            model_slug = slug(name)
            pdf_path = PDF_ROOT / f"{model_slug}.pdf"
            data, digest, resolved_url = download_pdf(datasheet, pdf_path)
            datasheet["url"] = resolved_url
            doc_id = f"sha256-{digest[:16]}"
            prior_doc = old_documents.get(digest)
            prior_queue = old_queue.get(digest)
            complete = bool(
                prior_doc
                and prior_doc.get("mistralOcr", {}).get("status") == "complete"
                and prior_doc.get("mistralOcrPath")
                and Path(prior_doc["mistralOcrPath"]).exists()
            )
            ocr_path = (
                prior_doc["mistralOcrPath"]
                if complete
                else f"ocr_results/mistral/{doc_id}.md"
            )
            pages = prior_doc.get("pages", 0) if prior_doc else 0
            doc = {
                "id": doc_id,
                "sha256": digest,
                "pdfPath": pdf_path.as_posix(),
                "bytes": len(data),
                "pages": pages,
                "mistralOcrPath": ocr_path,
                "mistralOcr": {
                    "status": "complete" if complete else "pending_auth",
                    "model": "mistral-ocr-latest",
                    **({"completedAt": prior_doc.get("mistralOcr", {}).get("completedAt")} if complete else {}),
                },
                "manufacturers": [MANUFACTURER],
                "mpns": [name],
                "titles": [f"{MANUFACTURER} {name} datasheet"],
                "sourceUrls": [datasheet["url"]],
                "productPages": [product["url"]],
                "sources": [SOURCE_TAG],
                "provenanceStatus": "verified_source_url",
            }
            upsert(documents["documents"], doc, "sha256")
            sensor = {
                "id": f"lorenz-messtechnik--{model_slug}",
                "recordType": "catalog_model",
                "model": name,
                "name": f"{MANUFACTURER} {name}",
                "manufacturer": MANUFACTURER,
                "status": "Active",
                "sensorType": "Load Cell" if load_cell else "Force Transducer",
                "datasheetUrl": datasheet["url"],
                "datasheetUrls": [datasheet["url"]],
                "pdfPath": pdf_path.as_posix(),
                "ocrPath": ocr_path,
                "productUrl": product["url"],
                "productUrls": [product["url"]],
                "sources": [SOURCE_TAG],
                "datasheetStatus": "local_pdf",
                "mistralOcrStatus": "complete" if complete else "pending_auth",
            }
            upsert(sensors["sensors"], sensor, "id")
            family = {
                "id": f"lorenz-messtechnik--{model_slug}--catalog-model",
                "manufacturer": MANUFACTURER,
                "family": name,
                "familySource": "catalog_model",
                "recordCount": 1,
                "models": [name],
                "sensorTypes": [sensor["sensorType"]],
                "sources": [SOURCE_TAG],
                "datasheetUrls": [datasheet["url"]],
                "pdfPaths": [pdf_path.as_posix()],
            }
            upsert(families["families"], family, "id")
            queue_record = {
                "id": doc_id,
                "pdfPath": pdf_path.as_posix(),
                "sha256": digest,
                "sourceUrls": [datasheet["url"]],
                "status": "complete" if complete else "pending_auth",
                "ocrPath": ocr_path,
                "pages": pages,
            }
            if complete:
                queue_record["completedAt"] = (
                    prior_queue or {}
                ).get("completedAt") or prior_doc.get("mistralOcr", {}).get("completedAt") or now
                reused_ocr += 1
            else:
                pending_ocr += 1
            upsert(queue["documents"], queue_record, "sha256")
            added += 1

    referenced_paths = {
        record["pdfPath"]
        for record in sensors["sensors"]
        if record.get("manufacturer") == MANUFACTURER and record.get("pdfPath")
    }
    for path in PDF_ROOT.glob("*.pdf"):
        if path.as_posix() not in referenced_paths:
            path.unlink()

    sensors["generatedAt"] = now
    sensors["recordCount"] = len(sensors["sensors"])
    sensors["manufacturerCount"] = len(
        {record.get("manufacturer") for record in sensors["sensors"] if record.get("manufacturer")}
    )
    families["generatedAt"] = now
    families["familyCount"] = len(families["families"])
    documents["generatedAt"] = now
    documents["documentCount"] = len(documents["documents"])
    documents["uniqueSha256Count"] = len({record["sha256"] for record in documents["documents"]})
    queue["generatedAt"] = now
    queue["status"] = "complete" if pending_ocr == 0 else "partial"
    queue["completedCount"] = len(queue["documents"]) - pending_ocr
    queue["remainingCount"] = pending_ocr

    atomic_write(SENSORS_PATH, sensors)
    atomic_write(FAMILIES_PATH, families)
    atomic_write(DOCUMENTS_PATH, documents)
    atomic_write(QUEUE_PATH, queue)
    migrate_spec_targets()
    return {"records": added, "reusedOcr": reused_ocr, "pendingOcr": pending_ocr}


def main() -> None:
    product_urls = discover_products()
    with ThreadPoolExecutor(max_workers=12) as executor:
        products = list(executor.map(extract_product, product_urls))
    products.sort(key=lambda product: product["model"])
    sensor_pdf_count = sum(len(product["datasheets"]) for product in products)
    accessory_pdf_count = sum(len(product["accessoryPdfs"]) for product in products)
    payload = {
        "schemaVersion": 2,
        "sourcePages": SOURCE_PAGES,
        "harvestedAt": datetime.now(UTC).isoformat(),
        "productCount": len(products),
        "sensorDatasheetCount": sensor_pdf_count,
        "accessoryPdfCount": accessory_pdf_count,
        "products": products,
    }
    atomic_write(MANIFEST_PATH, payload)
    result = ingest(products)
    print(json.dumps({
        "products": len(products),
        "sensorDatasheets": sensor_pdf_count,
        "accessoryPdfsExcluded": accessory_pdf_count,
        **result,
    }, indent=2))


if __name__ == "__main__":
    main()
