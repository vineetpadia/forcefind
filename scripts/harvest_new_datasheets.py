#!/usr/bin/env python3
"""
Comprehensive Harvester for ForceFind.
Harvests force sensor and load cell datasheets for Thames Side Sensors, LAUMAS,
Strainsert, Sherborne Sensors, SENSY, Pavone Sistemi, Utilcell, Novatech Measurements, Zemic, etc.
Atomic update of documents.json, sensors.json, families.json, ocr-queue.json, and coverage-gaps.json.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from urllib.parse import quote, urljoin
from datetime import UTC, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent))
import harvest_and_ingest_all
from harvest_and_ingest_all import ingest_datasheet, load_envelope, atomic_json_write, slug

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def custom_fetch_and_save_pdf(url: str, destination: Path) -> bytes | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 1000:
        data = destination.read_bytes()
        if b"%PDF" in data[:2048]:
            return data
    quoted_url = quote(url, safe=":/?&=#%")
    request = urllib.request.Request(quoted_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, context=ctx, timeout=15) as response:
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

harvest_and_ingest_all.fetch_and_save_pdf = custom_fetch_and_save_pdf

def get_xml_locs(url: str) -> list[str]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            return re.findall(r'<loc>([^<]+)</loc>', content)
    except Exception as e:
        print(f"Failed to fetch XML {url}: {e}")
        return []

def harvest_thames_side(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Thames Side Sensors ================")
    count = 0
    
    def check_dlid(dlid):
        url = f"https://www.thames-side.com/cgi-bin/showpage.fcgi?dlid={dlid};extmode=dlredir"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                final_url = resp.geturl()
                if final_url.lower().endswith('.pdf'):
                    data = resp.read(2048)
                    if b'%PDF' in data[:2048]:
                        fname = final_url.split('/')[-1]
                        return dlid, fname, final_url
        except Exception:
            pass
        return None

    pdf_dict = {}
    with ThreadPoolExecutor(max_workers=15) as ex:
        results = ex.map(check_dlid, range(1, 300))
        for res in results:
            if res:
                dlid, fname, url = res
                flow = fname.lower()
                if any(x in flow for x in ['certif', 'policy', 'privacy', 'term', 'warranty', 'iso', 'manual', 'drawing', 'guide', 'wiring', 'note', 'study', 'case']):
                    continue
                if any(x in flow for x in ['data_sheet', 'datasheet', 'datenblatt']):
                    pdf_dict[fname] = url

    print(f"Found {len(pdf_dict)} candidate Thames Side datasheet PDFs")

    for fname, pdf_url in sorted(pdf_dict.items()):
        clean_name = fname.replace('%20', '_').replace('.pdf', '')
        m = re.search(r'(T\d+[A-Z\-\_]*|350[A-Za-z]*|VC3500|650|Matrix_II)', clean_name, re.I)
        model_name = m.group(1).replace('_', ' ').strip() if m else clean_name.replace('Thames_Side_', '').replace('_Data_Sheet', '')

        flow = fname.lower()
        if any(lang in flow for lang in ['german', 'deutsch', 'spanish', 'french', 'francais', 'es-la']):
            continue

        if ingest_datasheet(
            mfr="Thames Side Sensors",
            name=f"Model {model_name}",
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url="https://www.thames-side.com/products/load-cells/",
            sensor_type="Load Cell / Force Sensor",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Thames Side catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Thames Side datasheets.")
    return count

def harvest_laumas(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: LAUMAS ================")
    count = 0
    locs = get_xml_locs("https://www.laumas.com/sitemap_en.xml")
    prod_locs = [u for u in locs if '/en/product/' in u]
    print(f"Found {len(prod_locs)} LAUMAS product pages in sitemap.")

    def scrape_laumas(prod_url):
        try:
            req = urllib.request.Request(prod_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                idfs = re.findall(r'downloadfile\.php\?iDF=(\d+)', html)
                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
                model_name = title_match.group(1).strip() if title_match else prod_url.split('/')[-2]
                model_name = re.sub(r'<[^>]+>', '', model_name).strip()
                return model_name, prod_url, list(set(idfs))
        except Exception:
            return None

    prods_with_files = []
    with ThreadPoolExecutor(max_workers=15) as ex:
        results = ex.map(scrape_laumas, prod_locs)
        for res in results:
            if res:
                prods_with_files.append(res)

    print(f"Scraped {len(prods_with_files)} LAUMAS product pages with downloads.")

    for model_name, prod_url, idfs in prods_with_files:
        for idf in idfs:
            dl_url = f"https://www.laumas.com/include/downloadfile.php?iDF={idf}"
            try:
                rreq = urllib.request.Request(dl_url, headers=HEADERS)
                with urllib.request.urlopen(rreq, context=ctx, timeout=5) as rresp:
                    disp = rresp.headers.get('Content-Disposition', '')
                    match = re.search(r'filename=["\']?([^"\';]+)["\']?', disp)
                    fname = match.group(1) if match else ""
                    if fname.endswith('_EN.pdf') or fname.endswith('_en.pdf'):
                        sensor_model = fname.replace('_EN.pdf', '').replace('_en.pdf', '')
                        if ingest_datasheet(
                            mfr="LAUMAS",
                            name=sensor_model,
                            pdf_url=dl_url,
                            local_pdf_path=None,
                            product_url=prod_url,
                            sensor_type="Load Cell / Force Transducer",
                            documents_dict=docs,
                            sensors_dict=sensors,
                            families_dict=families,
                            queue_dict=queue,
                            source_tag="LAUMAS catalog harvest"
                        ):
                            count += 1
                            break
            except Exception:
                pass

    print(f"Ingested {count} LAUMAS datasheets.")
    return count

def harvest_strainsert(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Strainsert ================")
    count = 0
    urls = get_xml_locs("https://www.strainsert.com/products-sitemap.xml")
    print(f"Found {len(urls)} Strainsert product pages.")

    def scrape_strainsert(page_url):
        try:
            req = urllib.request.Request(page_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                pdfs = re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, re.I)
                valid = []
                for p in set(pdfs):
                    plow = p.lower()
                    if any(x in plow for x in ['certif', 'policy', 'privacy', 'term', 'warranty', 'iso', 'manual', 'guide', 'application', 'overview', 'values', 'size']):
                        continue
                    if 'wp-content/uploads' in plow:
                        valid.append(p)
                return page_url, valid
        except Exception:
            return page_url, []

    ds_map = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for page_url, pdfs in ex.map(scrape_strainsert, urls):
            for pdf in pdfs:
                ds_map[pdf] = page_url

    print(f"Found {len(ds_map)} Strainsert PDF datasheets.")

    for pdf_url, ppage in ds_map.items():
        fname = pdf_url.split('/')[-1].replace('.pdf', '')
        name = fname.upper().replace('_', ' ').replace('-', ' ')
        if ingest_datasheet(
            mfr="Strainsert",
            name=name,
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=ppage,
            sensor_type="Force Sensor / Load Cell",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Strainsert catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Strainsert datasheets.")
    return count

def harvest_sherborne(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Sherborne Sensors ================")
    count = 0
    urls = get_xml_locs("https://www.sherbornesensors.com/product-sitemap.xml")
    load_cell_urls = [u for u in urls if 'load-cell' in u.lower() or 'ss' in u.lower() or 'u2000' in u.lower() or 'u4000' in u.lower()]
    print(f"Found {len(load_cell_urls)} Sherborne load cell product pages.")

    def scrape_sherborne(page_url):
        try:
            req = urllib.request.Request(page_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                pdfs = re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, re.I)
                valid = []
                for p in set(pdfs):
                    plow = p.lower()
                    if any(x in plow for x in ['certif', 'policy', 'privacy', 'term', 'warranty', 'iso']):
                        continue
                    if 'wp-content/uploads' in plow:
                        valid.append(p)
                return page_url, valid
        except Exception:
            return page_url, []

    for page_url in load_cell_urls:
        purl, pdfs = scrape_sherborne(page_url)
        for pdf_url in pdfs:
            fname = pdf_url.split('/')[-1].replace('.pdf', '')
            name = fname.replace('Sherborne-Sensors-', '').replace('-Load-Cell', '').replace('_', ' ').replace('-', ' ')
            if ingest_datasheet(
                mfr="Sherborne Sensors",
                name=name,
                pdf_url=pdf_url,
                local_pdf_path=None,
                product_url=page_url,
                sensor_type="Precision Load Cell",
                documents_dict=docs,
                sensors_dict=sensors,
                families_dict=families,
                queue_dict=queue,
                source_tag="Sherborne Sensors catalog harvest"
            ):
                count += 1

    print(f"Ingested {count} Sherborne Sensors datasheets.")
    return count

def harvest_sensy(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: SENSY ================")
    count = 0
    locs = get_xml_locs("https://www.sensy.com/sitemap.xml")
    prod_locs = [u for u in locs if '/en/load-cells' in u or '/en/custom-made' in u or '/en/force' in u or '/en/products' in u]
    print(f"Found {len(prod_locs)} SENSY product category pages.")

    def scrape_sensy(url):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                pdfs = re.findall(r'href=["\']([^"\']+\.pdf)["\']', html, re.I)
                valid = []
                for p in set(pdfs):
                    full_p = urljoin(url, p)
                    plow = full_p.lower()
                    if any(x in plow for x in ['certif', 'policy', 'privacy', 'term', 'warranty', 'iso', 'manual', 'general', 'guide']):
                        continue
                    if 'sensy.com' in plow and 'en.pdf' in plow:
                        valid.append(full_p)
                return url, valid
        except Exception:
            return url, []

    ds_map = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for purl, pdfs in ex.map(scrape_sensy, prod_locs):
            for pdf in pdfs:
                ds_map[pdf] = purl

    print(f"Found {len(ds_map)} SENSY PDF datasheets.")

    for pdf_url, ppage in ds_map.items():
        fname = pdf_url.split('/')[-1].replace('.pdf', '')
        name = fname.replace('FP_', '').replace('_EN', '').replace('_', ' ')
        if ingest_datasheet(
            mfr="SENSY",
            name=f"Model {name}",
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=ppage,
            sensor_type="Load Cell / Force Sensor",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="SENSY catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} SENSY datasheets.")
    return count

def harvest_pavone(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Pavone Sistemi ================")
    count = 0
    locs = get_xml_locs("https://www.pavonesistemi.com/sitemap.xml")
    prod_locs = [u for u in locs if 'load-cells-' in u or 'load-cell-' in u]
    print(f"Found {len(prod_locs)} Pavone Sistemi product pages.")

    for purl in prod_locs:
        slug_name = purl.split('/')[-1]
        pdf_url = f"https://www.pavonesistemi.com/pdf/{slug_name}"
        model_name = slug_name.replace('load-cells-', '').replace('load-cell-', '').replace('-', ' ').upper()
        if ingest_datasheet(
            mfr="Pavone Sistemi",
            name=f"Model {model_name}",
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=purl,
            sensor_type="Load Cell / Weighing Sensor",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Pavone Sistemi catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Pavone Sistemi datasheets.")
    return count

def harvest_utilcell(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Utilcell ================")
    count = 0
    main_url = "https://www.utilcell.com/en/load-cells/"
    try:
        req = urllib.request.Request(main_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            links = set(re.findall(r'href=["\'](https://www\.utilcell\.com/en/load-cells/load-cell-[^"\']+)["\']', html))
    except Exception as e:
        print(f"Failed to fetch Utilcell main page: {e}")
        return 0

    print(f"Found {len(links)} Utilcell product pages.")

    def scrape_utilcell(purl):
        try:
            req = urllib.request.Request(purl, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                chtml = resp.read().decode('utf-8', errors='ignore')
                pdfs = re.findall(r'href=["\'](https://www\.utilcell\.com/dokumenty/[^"\']+\.pdf)["\']', chtml, re.I)
                ds_pdfs = [p for p in set(pdfs) if any(k in p.lower() for k in ['-en-de.pdf', '-en.pdf', 'en-es.pdf'])]
                return purl, ds_pdfs
        except Exception:
            return purl, []

    ds_map = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for purl, pdfs in ex.map(scrape_utilcell, list(links)):
            for pdf in pdfs:
                ds_map[pdf] = purl

    print(f"Found {len(ds_map)} Utilcell PDF datasheets.")

    for pdf_url, ppage in ds_map.items():
        fname = pdf_url.split('/')[-1].replace('.pdf', '')
        model_name = fname.replace('-2020-en-de', '').replace('-en', '').upper()
        if ingest_datasheet(
            mfr="Utilcell",
            name=f"Model {model_name}",
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=ppage,
            sensor_type="Load Cell",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Utilcell catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Utilcell datasheets.")
    return count

def harvest_novatech(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Novatech Measurements ================")
    count = 0
    main_url = "https://novatechloadcells.co.uk/products/"
    try:
        req = urllib.request.Request(main_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            links = set(re.findall(r'href=["\'](https://novatechloadcells\.co\.uk/products/[^/"\']+/?)["\']', html))
    except Exception as e:
        print(f"Failed to fetch Novatech main page: {e}")
        return 0

    prod_links = [l for l in links if any(k in l for k in ['loadcell', 'sensor', 'transducer', 'loadstud', 'loadmeter', 'load-washer'])]
    print(f"Found {len(prod_links)} Novatech product links.")

    existing_models = {s.get("model") for s in sensors.get("sensors", []) if s.get("manufacturer") == "Novatech Measurements"}

    def scrape_novatech(purl):
        model_slug = purl.rstrip('/').split('/')[-1]
        name = f"Model {model_slug.replace('-loadcell', '').replace('-sensor', '').replace('-', ' ').upper()}"
        if name in existing_models:
            return None
        try:
            req = urllib.request.Request(purl, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
                chtml = resp.read().decode('utf-8', errors='ignore')
                m = re.search(r'class="[^"]*postid-(\d+)[^"]*"', chtml)
                if m:
                    pid = m.group(1)
                    pdf_url = f"https://novatechloadcells.co.uk/product-pdf/{pid}"
                    return model_slug, purl, pdf_url
        except Exception:
            pass
        return None

    novatech_map = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = ex.map(scrape_novatech, prod_links)
        for res in results:
            if res:
                mslug, purl, pdf_url = res
                novatech_map[mslug] = (purl, pdf_url)

    print(f"Found {len(novatech_map)} new Novatech PDF datasheets.")

    for mslug, (ppage, pdf_url) in novatech_map.items():
        name = mslug.replace('-loadcell', '').replace('-sensor', '').replace('-', ' ').upper()
        if ingest_datasheet(
            mfr="Novatech Measurements",
            name=f"Model {name}",
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=ppage,
            sensor_type="Load Cell / Force Transducer",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Novatech Measurements catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Novatech Measurements datasheets.")
    return count

def harvest_zemic(docs, sensors, families, queue) -> int:
    print("\n================ Harvest: Zemic ================")
    count = 0
    sitemap_url = "https://www.zemicusa.com/wp-sitemap-posts-upcp_product-1.xml"
    locs = get_xml_locs(sitemap_url)
    print(f"Found {len(locs)} Zemic USA product pages.")

    existing_models = {s.get("model") for s in sensors.get("sensors", []) if s.get("manufacturer") == "Zemic"}

    def scrape_zemic(purl):
        model_slug = purl.rstrip('/').split('/')[-1]
        m = re.match(r'^([a-zA-Z0-9]+)', model_slug)
        name = m.group(1).upper() if m else model_slug.upper()
        if name in existing_models:
            return None
        try:
            req = urllib.request.Request(purl, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
                chtml = resp.read().decode('utf-8', errors='ignore')
                pdfs = re.findall(r'href=["\'](http://www\.zemicusa\.com/wp-content/uploads/[^"\']+\.pdf)["\']', chtml, re.I)
                valid_pdfs = [p for p in set(pdfs) if 'strain-gages' not in p.lower()]
                if valid_pdfs:
                    return name, purl, valid_pdfs[0]
        except Exception:
            pass
        return None

    zemic_map = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = ex.map(scrape_zemic, locs)
        for res in results:
            if res:
                name, purl, pdf_url = res
                zemic_map[name] = (purl, pdf_url)

    print(f"Found {len(zemic_map)} new Zemic PDF datasheets.")

    for name, (ppage, pdf_url) in zemic_map.items():
        if ingest_datasheet(
            mfr="Zemic",
            name=name,
            pdf_url=pdf_url,
            local_pdf_path=None,
            product_url=ppage,
            sensor_type="Load Cell",
            documents_dict=docs,
            sensors_dict=sensors,
            families_dict=families,
            queue_dict=queue,
            source_tag="Zemic catalog harvest"
        ):
            count += 1

    print(f"Ingested {count} Zemic datasheets.")
    return count

def run_all_harvests():
    docs_path = Path("data/documents.json")
    sensors_path = Path("data/sensors.json")
    families_path = Path("data/families.json")
    queue_path = Path("data/ocr-queue.json")
    gaps_path = Path("data/coverage-gaps.json")

    docs = load_envelope(docs_path, "documents")
    sensors = load_envelope(sensors_path, "sensors")
    families = load_envelope(families_path, "families")
    queue = load_envelope(queue_path, "documents")

    total_new = 0
    total_new += harvest_thames_side(docs, sensors, families, queue)
    total_new += harvest_laumas(docs, sensors, families, queue)
    total_new += harvest_strainsert(docs, sensors, families, queue)
    total_new += harvest_sherborne(docs, sensors, families, queue)
    total_new += harvest_sensy(docs, sensors, families, queue)
    total_new += harvest_pavone(docs, sensors, families, queue)
    total_new += harvest_utilcell(docs, sensors, families, queue)
    total_new += harvest_novatech(docs, sensors, families, queue)
    total_new += harvest_zemic(docs, sensors, families, queue)

    now = datetime.now(UTC).isoformat()
    docs["generatedAt"] = now
    docs["documentCount"] = len(docs["documents"])
    docs["uniqueSha256Count"] = len({item["sha256"] for item in docs["documents"]})
    atomic_json_write(docs_path, docs)

    sensors["generatedAt"] = now
    sensors["recordCount"] = len(sensors["sensors"])
    sensors["manufacturerCount"] = len({s.get("manufacturer") for s in sensors["sensors"]})
    atomic_json_write(sensors_path, sensors)

    families["generatedAt"] = now
    families["familyCount"] = len(families["families"])
    atomic_json_write(families_path, families)

    queue["generatedAt"] = now
    atomic_json_write(queue_path, queue)

    all_mfrs = sorted(list({s.get("manufacturer") for s in sensors["sensors"] if s.get("manufacturer")}))

    priority_uncovered = [
        "Rice Lake Weighing Systems",
        "Minebea Intec",
        "ANYLOAD",
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
        "Applied Measurements",
        "Kulite",
        "X-SENSORS",
        "XSENSOR",
        "Pressure Profile Systems"
    ]

    gaps_data = {
        "generatedAt": now,
        "coveredManufacturers": all_mfrs,
        "coveredManufacturerCount": len(all_mfrs),
        "priorityUncoveredManufacturers": [m for m in priority_uncovered if m not in all_mfrs],
        "method": "Current data/sensors.json names compared with official manufacturer catalog and datasheet portals; list remains open-ended."
    }
    atomic_json_write(gaps_path, gaps_data)

    print("\n================ Harvest Complete ================")
    print(f"New datasheets ingested: {total_new}")
    print(f"Total Sensors: {len(sensors['sensors'])}")
    print(f"Total Unique PDFs: {docs['uniqueSha256Count']}")
    print(f"Total Covered Manufacturers: {len(all_mfrs)}")

if __name__ == "__main__":
    run_all_harvests()
