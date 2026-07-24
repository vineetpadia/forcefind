#!/usr/bin/env python3
"""Process ForceFind's deduplicated PDF queue with Mistral OCR."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ingest_datasheet import OCR_MODEL, atomic_json_write, response_markdown, run_mistral_ocr

QUEUE_PATH = Path("data/ocr-queue.json")
DOCUMENTS_PATH = Path("data/documents.json")
SENSORS_PATH = Path("data/sensors.json")
OCR_ROOT = Path("ocr_results/mistral")


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON envelope: {path}")
    return payload


def process(record: dict[str, Any]) -> dict[str, Any]:
    pdf_path = Path(record["pdfPath"])
    response = run_mistral_ocr(pdf_path)
    output_path = OCR_ROOT / f"sha256-{record['sha256'][:16]}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        response_markdown(response, pdf_path, record["sha256"]),
        encoding="utf-8",
    )
    return {
        "sha256": record["sha256"],
        "pdfPath": record["pdfPath"],
        "ocrPath": output_path.as_posix(),
        "pages": len(response.pages),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=5, help="Concurrent OCR jobs")
    parser.add_argument("--limit", type=int, help="Maximum documents to process")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Include records previously marked failed",
    )
    args = parser.parse_args()
    if not 1 <= args.workers <= 50:
        parser.error("--workers must be between 1 and 50")

    queue = load(QUEUE_PATH)
    eligible = {"pending", "pending_auth"}
    if args.retry_failed:
        eligible.add("failed")
    pending = [item for item in queue["documents"] if item.get("status") in eligible]
    if args.limit is not None:
        pending = pending[: args.limit]
    if not pending:
        print("No eligible OCR documents")
        return

    # One synchronous request prevents an invalid credential from fanning out.
    try:
        first = process(pending[0])
    except Exception as error:
        now = datetime.now(UTC).isoformat()
        if "401" in str(error) or "Unauthorized" in str(error):
            queue["status"] = "blocked_unauthorized"
            queue["blocker"] = "Mistral API returned HTTP 401 Unauthorized."
            queue["lastAttemptAt"] = now
            atomic_json_write(QUEUE_PATH, queue)
        raise

    remaining = pending[1:]
    results = [first]
    failures: list[dict[str, str]] = []

    def flush_state() -> None:
        now_str = datetime.now(UTC).isoformat()
        res_by_sha = {item["sha256"]: item for item in results}
        fail_by_sha = {item["sha256"]: item["error"] for item in failures}
        for rec in queue["documents"]:
            d = rec["sha256"]
            if d in res_by_sha:
                r = res_by_sha[d]
                rec.update(
                    status="complete",
                    ocrPath=r["ocrPath"],
                    pages=r["pages"],
                    completedAt=now_str,
                )
                rec.pop("error", None)
            elif d in fail_by_sha:
                rec.update(status="failed", error=fail_by_sha[d], lastAttemptAt=now_str)

        docs = load(DOCUMENTS_PATH)
        for doc in docs["documents"]:
            r = res_by_sha.get(doc["sha256"])
            if r:
                doc["mistralOcrPath"] = r["ocrPath"]
                doc["pages"] = r["pages"]
                doc["mistralOcr"] = {
                    "status": "complete",
                    "model": OCR_MODEL,
                    "completedAt": now_str,
                }
        docs["generatedAt"] = now_str
        docs["mistralOcrStatus"] = (
            "complete"
            if all(item.get("status") == "complete" for item in queue["documents"])
            else "partial"
        )

        sens = load(SENSORS_PATH)
        by_pdf_path = {item["pdfPath"]: item for item in results}
        for sensor in sens["sensors"]:
            r = by_pdf_path.get(sensor.get("pdfPath"))
            if r:
                sensor["ocrPath"] = r["ocrPath"]
                sensor["mistralOcrStatus"] = "complete"
        sens["generatedAt"] = now_str

        rem_count = sum(item.get("status") != "complete" for item in queue["documents"])
        queue["generatedAt"] = now_str
        queue["status"] = "complete" if rem_count == 0 else "partial"
        queue["completedCount"] = len(queue["documents"]) - rem_count
        queue["remainingCount"] = rem_count
        queue.pop("blocker", None)

        atomic_json_write(DOCUMENTS_PATH, docs)
        atomic_json_write(SENSORS_PATH, sens)
        atomic_json_write(QUEUE_PATH, queue)

    flush_state()

    completed_counter = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process, record): record for record in remaining}
        for future in as_completed(futures):
            record = futures[future]
            try:
                results.append(future.result())
            except Exception as error:
                failures.append({"sha256": record["sha256"], "error": str(error)})
            completed_counter += 1
            if completed_counter % 5 == 0 or completed_counter == len(remaining):
                flush_state()
                print(f"Progress: {len(results)}/{len(pending)} succeeded ({len(failures)} failed)")

    flush_state()
    rem_count = sum(item.get("status") != "complete" for item in queue["documents"])
    print(
        f"Mistral OCR complete: {len(results)} succeeded, "
        f"{len(failures)} failed, {rem_count} remaining"
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"OCR batch failed: {error}", file=sys.stderr)
        raise SystemExit(1)
