#!/usr/bin/env python3
"""
Extended harvester for Zemic, Novatech Measurements, ANYLOAD, LAUMAS, and Kistler force sensors.
Downloads official PDFs, calculates SHA-256, and atomically updates ForceFind indexes.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from harvest_and_ingest_all import ingest_datasheet, load_envelope, atomic_json_write

MANUFACTURER_TARGETS = [
    {
        "mfr": "Zemic",
        "models": [
            {"name": "H8C", "url": "https://www.zemic.nl/datasheets/H8C.pdf", "type": "Shear Beam Load Cell"},
            {"name": "L6E3", "url": "https://www.zemic.nl/datasheets/L6E3.pdf", "type": "Single Point Load Cell"},
            {"name": "H3", "url": "https://www.zemic.nl/datasheets/H3.pdf", "type": "S-Type Load Cell"},
            {"name": "BM14G", "url": "https://www.zemic.nl/datasheets/BM14G.pdf", "type": "Compression Load Cell"},
            {"name": "L6D", "url": "https://www.zemic.nl/datasheets/L6D.pdf", "type": "Single Point Load Cell"},
            {"name": "L6E", "url": "https://www.zemic.nl/datasheets/L6E.pdf", "type": "Single Point Load Cell"},
            {"name": "H9N", "url": "https://www.zemic.nl/datasheets/H9N.pdf", "type": "Double Ended Shear Beam Load Cell"},
            {"name": "BM8H", "url": "https://www.zemic.nl/datasheets/BM8H.pdf", "type": "Shear Beam Load Cell"},
            {"name": "BM11", "url": "https://www.zemic.nl/datasheets/BM11.pdf", "type": "Bending Beam Load Cell"},
        ]
    },
    {
        "mfr": "Novatech Measurements",
        "models": [
            {"name": "F204", "url": "https://www.novatechloadcells.co.uk/ds/f204.pdf", "type": "Compression Load Cell"},
            {"name": "F256", "url": "https://www.novatechloadcells.co.uk/ds/f256.pdf", "type": "Low Profile Compression Load Cell"},
            {"name": "F306", "url": "https://www.novatechloadcells.co.uk/ds/f306.pdf", "type": "Tension and Compression Load Cell"},
            {"name": "F314", "url": "https://www.novatechloadcells.co.uk/ds/f314.pdf", "type": "Submersible Load Cell"},
            {"name": "F252", "url": "https://www.novatechloadcells.co.uk/ds/f252.pdf", "type": "Button Load Cell"},
        ]
    },
    {
        "mfr": "ANYLOAD",
        "models": [
            {"name": "108JA", "url": "https://www.anyload.com/wp-content/uploads/2021/04/108JA.pdf", "type": "Single Point Load Cell"},
            {"name": "563YH", "url": "https://www.anyload.com/wp-content/uploads/2021/04/563YH.pdf", "type": "Shear Beam Load Cell"},
            {"name": "102JA", "url": "https://www.anyload.com/wp-content/uploads/2021/04/102JA.pdf", "type": "Single Point Load Cell"},
            {"name": "101NH", "url": "https://www.anyload.com/wp-content/uploads/2021/04/101NH.pdf", "type": "S-Type Load Cell"},
        ]
    },
    {
        "mfr": "LAUMAS",
        "models": [
            {"name": "CBL", "url": "https://www.laumas.com/assets/files/products/pdf/en/cbl_en.pdf", "type": "Compression Load Cell"},
            {"name": "CKL", "url": "https://www.laumas.com/assets/files/products/pdf/en/ckl_en.pdf", "type": "Compression Load Cell"},
            {"name": "FCK", "url": "https://www.laumas.com/assets/files/products/pdf/en/fck_en.pdf", "type": "Single Point Load Cell"},
            {"name": "FO", "url": "https://www.laumas.com/assets/files/products/pdf/en/fo_en.pdf", "type": "Bending Beam Load Cell"},
        ]
    },
    {
        "mfr": "Kistler",
        "models": [
            {"name": "9212", "url": "https://www.kistler.com/files/document/000-176e.pdf", "type": "Quartz Force Sensor"},
            {"name": "9311B", "url": "https://www.kistler.com/files/document/000-180e.pdf", "type": "Quartz Force Link"},
            {"name": "9011A", "url": "https://www.kistler.com/files/document/000-171e.pdf", "type": "Quartz Force Washer"},
        ]
    }
]

def run_extended_harvest():
    docs = load_envelope(Path("data/documents.json"), "documents")
    sensors = load_envelope(Path("data/sensors.json"), "sensors")
    families = load_envelope(Path("data/families.json"), "families")
    queue = load_envelope(Path("data/ocr-queue.json"), "documents")

    count = 0
    for target in MANUFACTURER_TARGETS:
        mfr = target["mfr"]
        for m in target["models"]:
            if ingest_datasheet(
                mfr=mfr,
                name=m["name"],
                pdf_url=m["url"],
                local_pdf_path=None,
                product_url=None,
                sensor_type=m["type"],
                documents_dict=docs,
                sensors_dict=sensors,
                families_dict=families,
                queue_dict=queue,
                source_tag=f"{mfr} catalog harvest",
            ):
                count += 1

    # Save
    atomic_json_write(Path("data/documents.json"), docs)
    atomic_json_write(Path("data/sensors.json"), sensors)
    atomic_json_write(Path("data/families.json"), families)
    atomic_json_write(Path("data/ocr-queue.json"), queue)

    print(f"\nExtended harvest finished: ingested {count} datasheets.")

if __name__ == "__main__":
    run_extended_harvest()
