#!/usr/bin/env python3
"""Discover and ingest official European, Chinese, and Japanese force-sensor catalogs."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from harvest_and_ingest_all import atomic_json_write, load_envelope, slug, upsert

SENSORS_PATH = Path("data/sensors.json")
FAMILIES_PATH = Path("data/families.json")
COVERAGE_PATH = Path("data/coverage-gaps.json")
OUTPUT_PATH = Path("data/regional-force-sensor-products.json")
SOURCE_TAG = "Official regional manufacturer catalog crawl (2026-07-25)"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 25

SOURCE_METADATA: dict[str, dict[str, str]] = {
    "scaime": {
        "manufacturer": "SCAIME",
        "region": "Europe",
        "hqCountry": "France",
    },
    "minebea-intec": {
        "manufacturer": "Minebea Intec",
        "region": "Europe",
        "hqCountry": "Germany",
    },
    "lcm": {
        "manufacturer": "LCM Systems",
        "region": "Europe",
        "hqCountry": "United Kingdom",
    },
    "locosc": {
        "manufacturer": "LOCOSC Ningbo Precision Technology",
        "region": "China",
        "hqCountry": "China",
    },
    "fibos": {
        "manufacturer": "FIBOS Measurement Technology",
        "region": "China",
        "hqCountry": "China",
    },
    "minebeamitsumi": {
        "manufacturer": "MinebeaMitsumi",
        "region": "Japan",
        "hqCountry": "Japan",
    },
}

LCM_CATEGORY_URLS = [
    "https://www.lcmsystems.com/compression-load-cells",
    "https://www.lcmsystems.com/tension-compression-load-cells",
    "https://www.lcmsystems.com/tension-load-cells",
    "https://www.lcmsystems.com/beam-load-cells",
    "https://www.lcmsystems.com/load-pins",
    "https://www.lcmsystems.com/load-links",
    "https://www.lcmsystems.com/load-shackles",
    "https://www.lcmsystems.com/wireless-load-cells",
]
LCM_EXCLUDED_SLUGS = {
    "compression-load-cells",
    "tension-compression-load-cells",
    "tension-load-cells",
    "beam-load-cells",
    "load-pins",
    "load-links",
    "load-shackles",
    "wireless-load-cells",
    "load-cells",
    "products",
}
MINEBEA_SENSOR_BRANCHES = {
    "compression",
    "singlepoint",
    "tension",
    "special",
    "compression_stainless_loadcell",
    "forcesensor",
    "hygienic_weighing",
    "compression_hygienic_loadcell",
    "tension_stainless_loadcell",
    "beam_stainless_loadcell",
    "process_loadcell",
}


def fetch(url: str) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            if "text/" in response.headers.get("content-type", "") or "xml" in response.headers.get("content-type", ""):
                response.encoding = "utf-8"
            return response
        except (requests.RequestException, TimeoutError) as error:
            last_error = error
            if attempt < 3:
                time.sleep(2**attempt)
    raise last_error or RuntimeError(f"Failed to fetch {url}")


def sitemap_urls(url: str) -> list[str]:
    response = fetch(url)
    return re.findall(r"<loc>(.*?)</loc>", response.text, re.IGNORECASE)


def page_links(url: str) -> list[str]:
    response = fetch(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return sorted(
        {
            urljoin(response.url, anchor.get("href"))
            for anchor in soup.select("a[href]")
            if anchor.get("href")
        }
    )


def discover_candidates() -> dict[str, list[str]]:
    candidates: dict[str, set[str]] = {key: set() for key in SOURCE_METADATA}

    for url in page_links("https://www.scaime.com/all-load-cell-products"):
        if re.fullmatch(r"https://scaime\.com/product/post/[a-z0-9-]+", url):
            candidates["scaime"].add(url)

    for url in sitemap_urls("https://www.minebea-intec.com/en/sitemap.xml"):
        parsed = urlparse(url)
        final = parsed.path.rstrip("/").split("/")[-1]
        if "/en/load-cells/" in parsed.path and re.search(r"(?:^|-)load-cell(?:-|$)", final):
            candidates["minebea-intec"].add(url)

    for url in sitemap_urls("https://www.lcmsystems.com/sitemap.xml"):
        parsed = urlparse(url)
        final = parsed.path.rstrip("/").split("/")[-1]
        if parsed.netloc != "www.lcmsystems.com" or final in LCM_EXCLUDED_SLUGS:
            continue
        if any(part in parsed.path for part in ("/Markets/", "/Applications/", "/resources/", "/shop/")):
            continue
        if re.search(r"(?:amplifier|indicator|display)", final, re.IGNORECASE):
            continue
        if not re.match(r"[a-z]{2,10}-?\d", final, re.IGNORECASE):
            continue
        if re.search(r"(?:load-cell|load-pin|load-link|load-shackle|force-washer)", final):
            candidates["lcm"].add(url)

    for url in sitemap_urls("https://www.locosc.com/sitemap.xml"):
        if re.search(r"(?:Load-Cell|Force-Load-Cell)-pd\d+\.html$", url, re.IGNORECASE):
            candidates["locosc"].add(url)

    for url in sitemap_urls("https://www.fibossensor.com/sitemap.xml"):
        if re.search(r"(?:^|[-_])FA\d+[A-Z]?(?:\.|-|$)", url, re.IGNORECASE):
            candidates["fibos"].add(url)

    for url in sitemap_urls("https://product.minebeamitsumi.com/sitemap.xml"):
        marker = "/en/product/category/mcd/loadcell/"
        if marker not in url or "/parts/" not in url or not url.endswith(".html"):
            continue
        branch = url.split(marker, 1)[1].split("/", 1)[0]
        if branch in MINEBEA_SENSOR_BRANCHES:
            candidates["minebeamitsumi"].add(url)

    return {key: sorted(values) for key, values in candidates.items()}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n|-–—")


def model_from_page(source: str, heading: str, title: str, url: str) -> str:
    combined = f"{heading} {title}"
    if source == "scaime":
        return heading
    if source == "locosc":
        match = re.match(r"([A-Z]{1,5}\d+[A-Z0-9-]*)\b", heading)
        if match:
            return match.group(1)
    if source == "fibos":
        match = re.search(r"\b(FA\d+[A-Z]?)\b", combined, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    if source == "minebeamitsumi":
        ascii_heading = heading.encode("ascii", "ignore").decode()
        ascii_heading = re.sub(r"series", "", ascii_heading, flags=re.IGNORECASE)
        ascii_heading = re.sub(r"-{2,}", "-", ascii_heading)
        match = re.search(
            r"((?:[A-Z][A-Z0-9]*\d[A-Z0-9]*|BCL)(?:\([A-Z]\))?(?:-+[A-Z0-9/]+)*)",
            ascii_heading,
        )
        if match:
            model = match.group(1).replace("(", "").replace(")", "").rstrip("-")
            if re.match(r"PR\d+$", model) and re.match(r"\s+DB\b", ascii_heading[match.end() :]):
                model += "-DB"
            return model
    if source == "minebea-intec":
        model = re.sub(r"^Load cells?\s+", "", heading, flags=re.IGNORECASE)
        return clean_text(model.replace("®", ""))
    if source == "lcm":
        match = re.match(r"([A-Z][A-Z0-9-]{1,15})\b", heading)
        if match:
            return match.group(1)
    return heading


def classify_sensor(text: str) -> tuple[str, str | None]:
    lowered = text.lower()
    if re.search(r"(?:six|6)[ -]?(?:axis|component)|multi[ -]?axis|triaxial", lowered):
        return "Multi-axis Force / Torque Transducer", "Multi-axis"
    if "torque" in lowered:
        return "Torque Sensor", "Torque transducer"
    if "load pin" in lowered or "load-pin" in lowered:
        return "Load Cell", "Load pin"
    if "load shackle" in lowered or "load-shackle" in lowered:
        return "Load Cell", "Load shackle"
    if "load link" in lowered or "load-link" in lowered:
        return "Load Cell", "Load link"
    if "s-type" in lowered or "s type" in lowered or "s-beam" in lowered:
        return "Load Cell", "S-beam"
    if "single point" in lowered or "single-point" in lowered:
        return "Load Cell", "Single point"
    if "beam" in lowered:
        return "Load Cell", "Beam"
    if "washer" in lowered or "donut" in lowered or "annular" in lowered:
        return "Force Sensor", "Through-hole / washer"
    if "compression" in lowered:
        return "Load Cell", "Compression"
    if "tension" in lowered:
        return "Load Cell", "Tension / compression"
    if "force sensor" in lowered or "force transducer" in lowered:
        return "Force Sensor", None
    return "Load Cell", None


def datasheet_links(soup: BeautifulSoup, page_url: str, model: str) -> list[str]:
    links = {
        urljoin(page_url, anchor.get("href"))
        for anchor in soup.select("a[href]")
        if ".pdf" in anchor.get("href", "").lower()
    }
    model_key = re.sub(r"[^a-z0-9]", "", model.lower())

    def rank(url: str) -> tuple[int, str]:
        normalized = re.sub(r"[^a-z0-9]", "", url.lower())
        relevant = int(bool(model_key and model_key in normalized))
        datasheet = int(bool(re.search(r"data.?sheet|specification|catalog", url, re.IGNORECASE)))
        return (-(relevant * 2 + datasheet), url)

    return sorted(links, key=rank)


def extract_product(item: tuple[str, str]) -> dict[str, Any] | None:
    source, url = item
    try:
        response = fetch(url)
    except Exception as error:
        return {"source": source, "productUrl": url, "error": str(error)}
    soup = BeautifulSoup(response.text, "html.parser")
    title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    heading_node = soup.select_one("h1")
    heading = clean_text(heading_node.get_text(" ", strip=True) if heading_node else "")
    text = clean_text(f"{heading} {title}")
    recognized = re.search(
        r"load cell|loadcell|force sensor|force transducer|torque sensor|load pin|load link|load shackle|force washer",
        text,
        re.IGNORECASE,
    )
    if not heading or (not recognized and source != "minebeamitsumi"):
        return {"source": source, "productUrl": url, "error": "page is not a force-sensor product"}
    model = clean_text(model_from_page(source, heading, title, response.url))
    if not model or len(model) > 140 or (source == "minebeamitsumi" and model == heading):
        return {"source": source, "productUrl": url, "error": "model could not be identified"}
    sensor_type, form_factor = classify_sensor(text)
    metadata = SOURCE_METADATA[source]
    pdfs = datasheet_links(soup, response.url, model)
    if source == "lcm" and not pdfs:
        return {"source": source, "productUrl": url, "error": "no product datasheet link"}
    return {
        "source": source,
        "manufacturer": metadata["manufacturer"],
        "region": metadata["region"],
        "hqCountry": metadata["hqCountry"],
        "model": model,
        "name": heading,
        "sensorType": sensor_type,
        "formFactor": form_factor,
        "productUrl": response.url,
        "datasheetUrls": pdfs,
        "pageTitle": title,
    }


def model_key(manufacturer: str, model: str) -> tuple[str, str]:
    return (slug(manufacturer), slug(model).removeprefix("model-"))


def ingest(products: list[dict[str, Any]], dry_run: bool) -> tuple[int, int]:
    sensors = load_envelope(SENSORS_PATH, "sensors")
    families = load_envelope(FAMILIES_PATH, "families")
    existing = {
        model_key(record.get("manufacturer", ""), record.get("model", "")): record
        for record in sensors["sensors"]
    }
    added = 0
    skipped = 0
    now = datetime.now(UTC).isoformat()

    for product in products:
        key = model_key(product["manufacturer"], product["model"])
        prior = existing.get(key)
        if prior and prior.get("recordType") != "family":
            skipped += 1
            continue
        mfr_slug, model_slug = key
        datasheets = product["datasheetUrls"]
        sensor = {
            "id": f"{mfr_slug}--{model_slug}",
            "recordType": "catalog_model",
            "model": product["model"],
            "name": product["name"],
            "manufacturer": product["manufacturer"],
            "status": "Active",
            "sensorType": product["sensorType"],
            "formFactor": product.get("formFactor"),
            "productUrl": product["productUrl"],
            "productUrls": [product["productUrl"]],
            "datasheetUrl": datasheets[0] if datasheets else None,
            "datasheetUrls": datasheets,
            "datasheetStatus": "remote_url" if datasheets else "not_found",
            "mistralOcrStatus": "none",
            "sources": [SOURCE_TAG, product["productUrl"]],
            "region": product["region"],
            "hqCountry": product["hqCountry"],
            "sourceEvidence": {
                "pageTitle": product["pageTitle"],
                "heading": product["name"],
                "retrievedAt": now,
            },
        }
        sensor = {key: value for key, value in sensor.items() if value is not None}
        family = {
            "id": f"{mfr_slug}--{model_slug}--official-product",
            "manufacturer": product["manufacturer"],
            "family": product["model"],
            "familySource": "official_product_page",
            "recordCount": 1,
            "models": [product["model"]],
            "sensorTypes": [product["sensorType"]],
            "sources": [SOURCE_TAG, product["productUrl"]],
            "productUrls": [product["productUrl"]],
            "datasheetUrls": datasheets,
            "region": product["region"],
            "hqCountry": product["hqCountry"],
        }
        upsert(sensors["sensors"], sensor, "id")
        upsert(families["families"], family, "id")
        existing[key] = sensor
        added += 1

    if dry_run:
        return added, skipped

    sensors["generatedAt"] = now
    sensors["recordCount"] = len(sensors["sensors"])
    sensors["manufacturerCount"] = len(
        {record.get("manufacturer") for record in sensors["sensors"] if record.get("manufacturer")}
    )
    families["generatedAt"] = now
    families["familyCount"] = len(families["families"])
    atomic_json_write(SENSORS_PATH, sensors)
    atomic_json_write(FAMILIES_PATH, families)

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    coverage["generatedAt"] = now
    coverage["coveredManufacturers"] = sorted(
        {record.get("manufacturer") for record in sensors["sensors"] if record.get("manufacturer")}
    )
    coverage["coveredManufacturerCount"] = len(coverage["coveredManufacturers"])
    coverage["regionalCatalogExpansion"] = {
        "source": OUTPUT_PATH.as_posix(),
        "productCount": len(products),
        "regions": dict(sorted(__import__("collections").Counter(p["region"] for p in products).items())),
    }
    atomic_json_write(COVERAGE_PATH, coverage)
    return added, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 24:
        parser.error("--workers must be between 1 and 24")

    candidates = discover_candidates()
    work = [(source, url) for source, urls in candidates.items() for url in urls]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        extracted = list(executor.map(extract_product, work))
    products = [item for item in extracted if item and not item.get("error")]
    failures = [item for item in extracted if item and item.get("error")]
    products.sort(key=lambda item: (item["region"], item["manufacturer"], item["model"]))

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "method": "Official manufacturer product pages discovered from sitemaps and catalog indexes",
        "candidateCount": len(work),
        "productCount": len(products),
        "failureCount": len(failures),
        "regions": dict(sorted(__import__("collections").Counter(p["region"] for p in products).items())),
        "sources": {
            source: {
                **SOURCE_METADATA[source],
                "candidateCount": len(urls),
                "productCount": sum(1 for item in products if item["source"] == source),
            }
            for source, urls in candidates.items()
        },
        "products": products,
        "failures": failures,
    }
    if not args.dry_run:
        atomic_json_write(OUTPUT_PATH, payload)
    added, skipped = ingest(products, args.dry_run)
    print(json.dumps({
        "candidates": len(work),
        "products": len(products),
        "failures": len(failures),
        "regions": payload["regions"],
        "addedOrUpdated": added,
        "skippedExisting": skipped,
        "dryRun": args.dry_run,
    }, indent=2))


if __name__ == "__main__":
    main()
