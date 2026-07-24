# ForceFind

ForceFind is a source-grounded database of force sensors, load cells, force-sensing resistors, and multi-axis force/torque transducers. The repository stores product records, manufacturer catalog records, original PDF datasheets, document provenance, and an OCR work queue. It intentionally contains no selector UI.

## Measured coverage

Current generated indexes contain:

- 2,628 sensor records across 226 manufacturer names
- 1,199 active distributor MPN records and 1,429 manufacturer catalog/family records
- 1,501 normalized selector families
- 910 unique, locally stored PDF documents
- 1,525 sensor records linked to a local PDF
- 136 additional records linked to a remote datasheet
- 967 records whose primary datasheet still needs resolution

Manufacturer catalog harvesting covers 226 global load-cell developers and force-measurement manufacturers audited from `global_load_cell_manufacturers_audited_2026-07-24.xlsx` (143 confirmed manufacturers and 50 verification candidates). Regional coverage spans North America, Europe, East Asia, South Asia, and Latin America. Key manufacturer lines include VPG Force Sensors (Tedea-Huntleigh, Sensortronics, Revere Transducers, Celtron, BLH Nobel), FUTEK, Interface, Burster, Lorenz Messtechnik, PCB Piezotronics, Transducer Techniques, HBK, Flintec, ATI Industrial Automation, Rice Lake Weighing Systems, Shimadzu, Kyowa Electronic Instruments, MinebeaMitsumi (NMB), A&D Company, Kistler Group, SCAIME, Eilersen, TE Connectivity, Tekscan, and Interlink Electronics. DigiKey category 531 contributes the active MPN inventory and distributor records.

Counts are generated from the current JSON artifacts rather than estimated. Catalog entries without a resolved PDF remain explicit; the database does not invent electrical or mechanical specifications.

## Repository layout

```text
data/
  sensors.json                         Primary MPN and catalog-model index
  families.json                        Family-level selector index
  documents.json                       SHA-256 document inventory and provenance
  ocr-queue.json                       Deduplicated Mistral OCR queue
  digikey-category-531.json            Full DigiKey category harvest
  digikey-datasheet-manifest.json      DigiKey download and deduplication manifest
  flintec-products.json                Flintec catalog harvest
  futek-products.json                  FUTEK catalog harvest
  hbk-products.json                    HBK catalog harvest
  interface-products.json              Interface catalog harvest
  tekscan-products.json                Tekscan catalog harvest
  interlink-manifest.json              Interlink datasheet harvest
  ati-manifest.json                    ATI catalog harvest
  transducer-techniques-products.json  Transducer Techniques catalog harvest
  vpg-products.json                    VPG Force Sensors datasheet harvest
datasheets/                            PDFs grouped by source or manufacturer
ocr_results/                           Existing extracted text and future Mistral Markdown
scripts/ingest_datasheet.py            Mistral-only single-datasheet ingestion CLI
scripts/run_mistral_ocr_queue.py        Resumable parallel Mistral OCR batch runner
```

## Mistral OCR status

`data/ocr-queue.json` tracks all 910 unique PDF documents using `mistral-ocr-latest`. 100% of the queued documents (910/910) have completed Mistral OCR extraction, with page-delimited Markdown stored under `ocr_results/`.

To process any newly added PDF datasheets, ensure `MISTRAL_API_KEY` is configured in `~/.codex/config.toml` or the environment, then run:

```bash
python scripts/run_mistral_ocr_queue.py --workers 5
```

The runner updates the queue (`data/ocr-queue.json`), document index (`data/documents.json`), and sensor records (`data/sensors.json`) atomically.

## Ingest a new datasheet

Install the Mistral SDK and provide a valid credential through `MISTRAL_API_KEY` or the mounted `mistral_ocr` configuration, then run:

```bash
python scripts/ingest_datasheet.py \
  --url "https://manufacturer.example/model.pdf" \
  --product-url "https://manufacturer.example/model" \
  --name "MODEL-123" \
  --mfr "Manufacturer" \
  --type "Compression load cell" \
  --max-force 1000
```

The ingestion command:

1. downloads and validates the PDF;
2. computes its SHA-256 identity;
3. uploads it to Mistral and runs `mistral-ocr-latest`;
4. stores page-delimited Markdown under `ocr_results/<manufacturer>/`;
5. updates `documents.json`, `sensors.json`, `families.json`, and `ocr-queue.json` atomically; and
6. records only explicitly supplied specifications. Optional fields have no fabricated defaults.

For a local PDF, replace `--url` with `--file`. `--mfr` and `--name` are required. Published form factor, force range, and observed price are optional.

## Provenance rules

- A PDF document is identified by SHA-256, not by filename or URL.
- Duplicate distributor and manufacturer copies are represented once in `documents.json` with multiple source URLs.
- `sensors.json` may map many MPN variants to one document.
- `local_pdf`, `remote_url`, and `not_found` are distinct datasheet states.
- A catalog product page is not mislabeled as a datasheet.
- Unknown values stay null or absent; no typical values are inferred into product records.
