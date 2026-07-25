#!/usr/bin/env python3
"""Extract source-grounded load-cell wiring topology from every OCR transcript."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OCR_ROOT = Path("ocr_results")
OUTPUT_PATH = Path("data/ocr-conductor-specifications.json")

COUNT_WORDS = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
}
COUNT_PATTERN = re.compile(
    r"\b(?P<count>[2-9]|1[0-2]|two|three|four|five|six|seven|eight|nine|ten|twelve)"
    r"\s*(?:-|–|—)?\s*(?:wire|wires|conductor|conductors|core|cores)\b",
    re.IGNORECASE,
)
CONNECTOR_PIN_PATTERN = re.compile(
    r"\b(?P<count>[2-9]|1[0-9]|2[0-4])\s*(?:-|–|—)?\s*pin(?:s|ned)?\b",
    re.IGNORECASE,
)
REMOTE_SENSE_PATTERN = re.compile(
    r"\b(?:remote\s+sense|sense\s+(?:lead|leads|wire|wires)|"
    r"additional\s+(?:sense|sensing)\s+(?:lead|leads|wire|wires)|"
    r"with\s+sense\s+(?:lead|leads|wire|wires)|"
    r"sense\s*[+-]|[+-]\s*sense|sens\s*[+-]|[+-]\s*sens)\b",
    re.IGNORECASE,
)
SHIELD_PATTERN = re.compile(r"\b(?:shield|shielded|screen|screened|drain\s+wire)\b", re.IGNORECASE)
CONDITIONED_PATTERN = re.compile(
    r"\b(?:4\s*mA\s*(?:to|[-–])\s*20\s*mA|4\s*[-–]\s*20\s*mA|0\s*[-–]\s*10\s*V|"
    r"(?:current|voltage)\s+(?:two|three|2|3)\s*(?:-|–)?\s*wire|"
    r"RS\s*[-–]?\s*48[25].{0,40}(?:two|2)\s*(?:-|–)?\s*wire|"
    r"conditioned\s+(?:output|signal)|current\s+output)\b",
    re.IGNORECASE,
)
PAGE_PATTERN = re.compile(r"^## Page\s+(\d+)\s*$", re.MULTILINE)


def compact_quote(lines: list[str], index: int) -> str:
    start = max(0, index - 1)
    end = min(len(lines), index + 2)
    quote = " ".join(line.strip() for line in lines[start:end] if line.strip())
    return re.sub(r"\s+", " ", quote)[:900]


def page_sections(text: str) -> list[tuple[int, str]]:
    matches = list(PAGE_PATTERN.finditer(text))
    if not matches:
        return [(1, text)]
    return [
        (
            int(match.group(1)),
            text[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(text)],
        )
        for index, match in enumerate(matches)
    ]


def numeric_count(value: str) -> int:
    lowered = value.lower()
    return int(lowered) if lowered.isdigit() else COUNT_WORDS[lowered]


def evidence(page: int, quote: str) -> dict[str, Any]:
    return {"page": page, "quote": quote}


def unique_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, str, int | None]] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = (item["page"], item["quote"], item.get("count"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def classify(counts: list[int], remote_sense: bool, conditioned_counts: set[int]) -> str | None:
    if not counts and conditioned_counts and not remote_sense:
        return "conditioned_output"
    if remote_sense and 6 in counts and 4 in counts:
        return "selectable_4_or_6_wire"
    if remote_sense and 6 in counts:
        return "six_wire_remote_sense"
    if remote_sense:
        return "remote_sense_count_unstated"
    if counts == [4]:
        return "four_wire_bridge"
    if counts == [6]:
        return "six_wire_unspecified"
    if len(counts) > 1:
        return "multiple_conductor_options"
    if counts and max(counts) > 6:
        return "more_than_six_conductors"
    return None


def extract_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    count_evidence: list[dict[str, Any]] = []
    conditioned_count_evidence: list[dict[str, Any]] = []
    sense_evidence: list[dict[str, Any]] = []
    shield_evidence: list[dict[str, Any]] = []
    connector_evidence: list[dict[str, Any]] = []
    counts: set[int] = set()
    conditioned_counts: set[int] = set()
    connector_counts: set[int] = set()

    for page, page_text in page_sections(text):
        lines = page_text.splitlines()
        for index, line in enumerate(lines):
            quote = compact_quote(lines, index)
            count_matches = list(COUNT_PATTERN.finditer(line))
            for match in count_matches:
                count = numeric_count(match.group("count"))
                item = {**evidence(page, quote), "count": count}
                if CONDITIONED_PATTERN.search(quote):
                    conditioned_counts.add(count)
                    conditioned_count_evidence.append(item)
                else:
                    counts.add(count)
                    count_evidence.append(item)
            for match in CONNECTOR_PIN_PATTERN.finditer(line):
                count = int(match.group("count"))
                connector_counts.add(count)
                connector_evidence.append({**evidence(page, quote), "count": count})
            if REMOTE_SENSE_PATTERN.search(line):
                sense_evidence.append(evidence(page, quote))
            if SHIELD_PATTERN.search(line) and re.search(
                r"(?i)\b(?:cable|wire|conductor|core|screen|shield|drain)\b", quote
            ):
                shield_evidence.append(evidence(page, quote))

    count_items = unique_evidence(count_evidence)
    conditioned_count_items = unique_evidence(conditioned_count_evidence)
    sense_items = unique_evidence(sense_evidence)
    shield_items = unique_evidence(shield_evidence)
    connector_items = unique_evidence(connector_evidence)
    sorted_counts = sorted(counts)
    remote_sense = bool(sense_items)
    topology = classify(sorted_counts, remote_sense, conditioned_counts)
    return {
        "ocrPath": path.as_posix(),
        "scanned": True,
        "availableConductorCounts": sorted_counts,
        "totalCableConductors": sorted_counts[0] if len(sorted_counts) == 1 else None,
        "conditionedOutputConductorCounts": sorted(conditioned_counts),
        "connectorPinCounts": sorted(connector_counts),
        "hasRemoteSense": True if remote_sense else None,
        "senseLeadCount": 2 if remote_sense and re.search(r"(?i)\b(?:two|2)\s+additional\s+sense", text) else None,
        "hasShield": True if shield_items else None,
        "wiringTopology": topology,
        "evidence": {
            "availableConductorCounts": count_items,
            "conditionedOutputConductorCounts": conditioned_count_items,
            "hasRemoteSense": sense_items,
            "hasShield": shield_items,
            "connectorPinCounts": connector_items,
        },
    }


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    paths = sorted(OCR_ROOT.rglob("*.md"))
    documents = [extract_document(path) for path in paths]
    topology_counts = Counter(document["wiringTopology"] or "not_stated" for document in documents)
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "method": "deterministic_explicit_ocr_wiring_evidence",
        "definitions": {
            "four_wire_bridge": "Excitation +/− and signal +/−; no remote-sense claim.",
            "six_wire_remote_sense": "Six conductors with explicit sense-lead evidence.",
            "selectable_4_or_6_wire": "Datasheet explicitly offers both four- and six-conductor wiring, with sense leads on the six-conductor option.",
            "six_wire_unspecified": "Six conductors are stated but their functions are not explicit.",
            "more_than_six_conductors": "More than six conductors are stated; auxiliary function is not inferred.",
        },
        "metadata": {
            "ocrFilesScanned": len(documents),
            "documentsWithConductorCounts": sum(bool(document["availableConductorCounts"]) for document in documents),
            "documentsWithRemoteSense": sum(document["hasRemoteSense"] is True for document in documents),
            "documentsWithShield": sum(document["hasShield"] is True for document in documents),
            "topologies": dict(sorted(topology_counts.items())),
        },
        "documents": documents,
    }
    atomic_json_write(OUTPUT_PATH, payload)
    print(f"Scanned {len(documents):,} OCR transcripts")
    print(f"Found explicit conductor counts in {payload['metadata']['documentsWithConductorCounts']:,} documents")
    print(f"Found explicit remote-sense evidence in {payload['metadata']['documentsWithRemoteSense']:,} documents")
    print("Topologies:")
    for name, count in sorted(topology_counts.items()):
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
