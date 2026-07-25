#!/usr/bin/env python3
"""Build the engineer-facing ForceFind selector bundle from catalog and model-read OCR specs."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SENSORS_PATH = Path("data/sensors.json")
FAMILIES_PATH = Path("data/families.json")
DOCUMENTS_PATH = Path("data/documents.json")
OCR_SPECS_PATH = Path("data/ocr-specifications.json")
OUTPUT_PATHS = (
    Path("selector-data.json"),
    Path("public/selector-data.json"),
    Path("data/selector-data.json"),
)


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object in {path}")
    return payload


def is_audit_placeholder(sensor: dict[str, Any]) -> bool:
    return any(
        str(source).startswith("Global Load-Cell Manufacturer Audit Excel")
        for source in sensor.get("sources", [])
    )


def first_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "" and value != "-" and value != []:
            return value
    return None


def positive_force(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def format_force(newtons: float | None) -> str | None:
    if newtons is None or newtons <= 0:
        return None
    prefixes = (
        (1_000_000_000, "GN"),
        (1_000_000, "MN"),
        (1_000, "kN"),
        (1, "N"),
        (0.001, "mN"),
        (0.000_001, "µN"),
        (0.000_000_001, "nN"),
    )
    for scale, unit in prefixes:
        if newtons >= scale:
            return f"{newtons / scale:.4g} {unit}"
    return f"{newtons / 0.000_000_001:.4g} nN"


def format_force_range(minimum: float | None, maximum: float | None) -> str | None:
    if minimum is None and maximum is None:
        return None
    if minimum is None:
        return format_force(maximum)
    if maximum is None or math.isclose(minimum, maximum):
        return format_force(minimum)
    return f"{format_force(minimum)}–{format_force(maximum)}"


def format_range(minimum: float | None, maximum: float | None, unit: str) -> str | None:
    if minimum is None and maximum is None:
        return None
    if minimum is None:
        return f"≤ {maximum:g} {unit}"
    if maximum is None or minimum == maximum:
        return f"{minimum:g} {unit}"
    return f"{minimum:g} to {maximum:g} {unit}"


def classify_category(sensor_type: str, name: str, form_factor: str | None) -> str:
    text = f"{sensor_type} {name} {form_factor or ''}".lower()
    if any(term in text for term in ("junction box", "mounting kit", "cable", "accessory", "barrier", "simulator")):
        return "Accessory"
    if any(
        term in text
        for term in (
            "amplifier",
            "indicator",
            "transmitter",
            "converter",
            "display meter",
            "digitizer",
            "conditioner",
            "loadmeter",
            "receiver",
        )
    ):
        return "Instrumentation"
    if any(term in text for term in ("weighing system", "weighing platform", "scale", "weighbridge")):
        return "Weighing system"
    if "force sensing resistor" in text or "fsr" in text:
        return "Force-sensing resistor"
    if "torque" in text and any(term in text for term in ("multi", "axis", "force/torque", "force torque")):
        return "Multi-axis force / torque"
    if "torque" in text:
        return "Torque sensor"
    if any(term in text for term in ("load cell", "load pin", "load button", "load sensor")):
        return "Load cell"
    if any(term in text for term in ("force sensor", "force transducer", "stress sensor", "force-sensing")):
        return "Force sensor"
    return "Other sensor"


def classify_technology(technology: str | None, output_signals: list[str]) -> str:
    text = f"{technology or ''} {' '.join(output_signals)}".lower()
    if any(term in text for term in ("strain", "gage", "gauge", "wheatstone", "bonded foil")):
        return "Strain gauge"
    if any(term in text for term in ("fsr", "polymer thick film", "resistive film")):
        return "Force-sensing resistor"
    if any(term in text for term in ("piezoresistive", "mems", "silicon")):
        return "Piezoresistive / MEMS"
    if "piezoelectric" in text:
        return "Piezoelectric"
    if "capacitive" in text:
        return "Capacitive"
    if "hydraulic" in text:
        return "Hydraulic"
    if "pneumatic" in text:
        return "Pneumatic"
    if "optical" in text:
        return "Optical"
    if "magnetoelastic" in text:
        return "Magnetoelastic"
    if "digital" in text:
        return "Digital / integrated electronics"
    if any(term in text for term in ("voltage", "current", "mv/v", "4-20 ma", "0-10 v")):
        return "Analog electrical"
    return "Other / unspecified"


def product_spec_index(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_target: dict[str, dict[str, Any]] = {}
    summaries: dict[str, str] = {}
    for document in payload.get("documents", []):
        ocr_path = document.get("ocrPath")
        summary_items = document.get("documentSummaries") or []
        if ocr_path and summary_items:
            summaries[ocr_path] = summary_items[0]
        for product in document.get("products", []):
            target_id = product.get("targetId")
            if target_id and not str(target_id).startswith("document::"):
                by_target[target_id] = product
    return by_target, summaries


def engineering_error(specs: dict[str, Any]) -> tuple[float | None, str | None]:
    candidates = (
        ("Accuracy", specs.get("accuracyPctFS")),
        ("Combined error", specs.get("combinedErrorPctFS")),
        ("Nonlinearity", specs.get("nonlinearityPctFS")),
    )
    for label, value in candidates:
        if isinstance(value, (int, float)):
            return float(value), label
    return None, None


def normalized_record(
    sensor: dict[str, Any],
    specs: dict[str, Any] | None,
    summary: str | None,
) -> dict[str, Any]:
    specs = specs or {}
    capacities = sorted(
        {
            number
            for value in specs.get("capacitiesN") or []
            if (number := positive_force(value)) is not None
        }
    )
    capacity_max = positive_force(
        first_value(specs.get("capacityMaxN"), sensor.get("maxForceN"))
    )
    capacity_min = positive_force(specs.get("capacityMinN"))
    if capacity_max is None and capacities:
        capacity_max = capacities[-1]
    if capacity_min is None and len(capacities) > 1:
        capacity_min = capacities[0]
    if capacity_min is not None and capacity_max is not None and capacity_min > capacity_max:
        capacity_min, capacity_max = capacity_max, capacity_min
    if not capacities and capacity_max is not None:
        capacities = [capacity_max]
    capacity_display = format_force_range(capacity_min, capacity_max)
    error_pct, error_kind = engineering_error(specs)
    output_signals = specs.get("outputSignals") or ([] if sensor.get("output") in (None, "", "-") else [sensor["output"]])
    temp_min = first_value(specs.get("operatingTempMinC"))
    temp_max = first_value(specs.get("operatingTempMaxC"))
    compensated_min = specs.get("compensatedTempMinC")
    compensated_max = specs.get("compensatedTempMaxC")
    source_scope = specs.get("sourceScope") if specs else None

    pdf_path = sensor.get("pdfPath")
    ocr_path = sensor.get("ocrPath")
    model = sensor.get("model") or sensor.get("name") or sensor["id"]
    manufacturer = sensor.get("manufacturer") or "Unknown"
    sensor_type = first_value(specs.get("sensorType"), sensor.get("sensorType"), "Force sensor")
    technology = first_value(specs.get("technology"), sensor.get("output"))
    form_factor = first_value(
        specs.get("formFactor"),
        sensor.get("actuatorType"),
        sensor.get("actuatorStyle"),
    )

    category = classify_category(str(sensor_type), str(model), form_factor)
    technology_group = classify_technology(
        None if technology is None else str(technology),
        [str(signal) for signal in output_signals],
    )

    searchable = " ".join(
        str(value)
        for value in (
            model,
            sensor.get("name"),
            manufacturer,
            sensor_type,
            technology,
            form_factor,
            specs.get("loadDirection"),
            capacity_display,
            " ".join(output_signals),
            specs.get("material"),
            specs.get("ipRating"),
            summary,
            specs.get("notes"),
        )
        if value
    ).lower()

    return {
        "id": sensor["id"],
        "recordType": sensor.get("recordType"),
        "model": model,
        "name": sensor.get("name") or model,
        "series": None if sensor.get("series") == "-" else sensor.get("series"),
        "manufacturer": manufacturer,
        "status": sensor.get("status"),
        "sensorType": sensor_type,
        "category": category,
        "technology": technology,
        "technologyGroup": technology_group,
        "formFactor": form_factor,
        "axisCount": specs.get("axisCount"),
        "loadDirection": specs.get("loadDirection"),
        "capacitiesN": capacities,
        "capacityMinN": capacity_min,
        "capacityMaxN": capacity_max,
        "capacityDisplay": capacity_display,
        "torquesNm": specs.get("torquesNm") or [],
        "torqueMinNm": specs.get("torqueMinNm"),
        "torqueMaxNm": specs.get("torqueMaxNm"),
        "torqueDisplay": specs.get("torqueDisplay"),
        "ratedOutputMvV": specs.get("ratedOutputMvV"),
        "outputSignals": output_signals,
        "accuracyPctFS": specs.get("accuracyPctFS"),
        "combinedErrorPctFS": specs.get("combinedErrorPctFS"),
        "nonlinearityPctFS": specs.get("nonlinearityPctFS"),
        "hysteresisPctFS": specs.get("hysteresisPctFS"),
        "repeatabilityPctFS": specs.get("repeatabilityPctFS"),
        "creepPctFS": specs.get("creepPctFS"),
        "creepDurationMin": specs.get("creepDurationMin"),
        "primaryErrorPctFS": error_pct,
        "primaryErrorKind": error_kind,
        "excitationRecommendedV": specs.get("excitationRecommendedV"),
        "excitationMaxV": specs.get("excitationMaxV"),
        "inputResistanceOhm": specs.get("inputResistanceOhm"),
        "outputResistanceOhm": specs.get("outputResistanceOhm"),
        "bridgeResistanceOhm": specs.get("bridgeResistanceOhm"),
        "insulationResistanceMOhm": specs.get("insulationResistanceMOhm"),
        "compensatedTempMinC": compensated_min,
        "compensatedTempMaxC": compensated_max,
        "compensatedTempDisplay": format_range(compensated_min, compensated_max, "°C"),
        "operatingTempMinC": temp_min,
        "operatingTempMaxC": temp_max,
        "operatingTempDisplay": format_range(temp_min, temp_max, "°C"),
        "safeOverloadPct": specs.get("safeOverloadPct"),
        "ultimateOverloadPct": specs.get("ultimateOverloadPct"),
        "ipRating": specs.get("ipRating"),
        "material": specs.get("material"),
        "dimensions": specs.get("dimensions"),
        "weightKg": specs.get("weightKg"),
        "cable": specs.get("cable"),
        "certifications": specs.get("certifications") or [],
        "notes": specs.get("notes"),
        "priceUSD": sensor.get("priceUSD"),
        "pdfPath": pdf_path,
        "ocrPath": ocr_path,
        "productUrl": sensor.get("productUrl"),
        "datasheetUrl": sensor.get("datasheetUrl"),
        "datasheetStatus": sensor.get("datasheetStatus"),
        "ocrStatus": sensor.get("mistralOcrStatus"),
        "documentSummary": summary,
        "sourceScope": source_scope,
        "evidenceCount": len(specs.get("evidence") or {}),
        "evidence": specs.get("evidence") or {},
        "searchText": searchable,
    }


def main() -> None:
    sensors_envelope = load(SENSORS_PATH)
    families_envelope = load(FAMILIES_PATH)
    documents_envelope = load(DOCUMENTS_PATH)
    specifications = load(OCR_SPECS_PATH)
    specs_by_target, summaries = product_spec_index(specifications)

    actual_sensors = [
        sensor for sensor in sensors_envelope.get("sensors", []) if not is_audit_placeholder(sensor)
    ]
    records = [
        normalized_record(
            sensor,
            specs_by_target.get(sensor["id"]),
            summaries.get(sensor.get("ocrPath")),
        )
        for sensor in actual_sensors
    ]
    instrumentation_count = sum(
        record["category"] == "Instrumentation" for record in records
    )
    records = [record for record in records if record["category"] != "Instrumentation"]


    manufacturers = sorted({record["manufacturer"] for record in records})
    categories = sorted({record["category"] for record in records})
    technology_groups = sorted({record["technologyGroup"] for record in records})
    form_factors = sorted({record["formFactor"] for record in records if record["formFactor"]})
    field_coverage = Counter(
        field
        for record in records
        for field in (
            "capacityMaxN",
            "technology",
            "formFactor",
            "axisCount",
            "loadDirection",
            "ratedOutputMvV",
            "primaryErrorPctFS",
            "operatingTempMinC",
            "ipRating",
            "material",
            "safeOverloadPct",
        )
        if record[field] is not None
    )

    payload = {
        "schemaVersion": 2,
        "metadata": {
            "generatedAt": datetime.now(UTC).isoformat(),
            "totalProducts": len(records),
            "excludedInstrumentationProducts": instrumentation_count,
            "totalManufacturers": len(manufacturers),
            "auditedManufacturers": sensors_envelope.get("manufacturerCount"),
            "totalFamilies": families_envelope.get("familyCount", len(families_envelope.get("families", []))),
            "totalDocuments": documents_envelope.get("documentCount", len(documents_envelope.get("documents", []))),
            "ocrFilesSemanticallyRead": specifications.get("metadata", {}).get("ocrFiles"),
            "productsWithSemanticSpecs": sum(record["id"] in specs_by_target for record in records),
            "fieldCoverage": dict(field_coverage),
        },
        "facets": {
            "manufacturers": manufacturers,
            "sensorTypes": categories,
            "technologies": technology_groups,
            "formFactors": form_factors,
        },
        "sensors": records,
    }
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    for path in OUTPUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)

    print(f"Built {len(records):,} engineer-facing product records")
    print(f"Mapped semantic specs to {payload['metadata']['productsWithSemanticSpecs']:,} records")
    print(f"Bundle size: {len(encoded) / 1024 / 1024:.2f} MiB")
    print("Field coverage:")
    for name, count in field_coverage.most_common():
        print(f"  {name}: {count:,} ({count / len(records):.1%})")


if __name__ == "__main__":
    main()
