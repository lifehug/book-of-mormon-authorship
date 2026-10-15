"""Text Creation Partnership corpus: EEBO-TCP, Evans-TCP, ECCO-TCP (BOM-11).

The TCP publishes every text as its own GitHub repository under ``textcreationpartnership``,
one TEI P5 XML file each, with a master index ``Texts/TCP.csv`` (61,315 rows: EEBO ``A``/``B``
ids 1473-1700, Evans ``N`` ids for American imprints to 1800, ECCO ``K`` ids for the 18th
century). Phase I texts are CC0; later releases carry their license in the TEI header.

``catalog``
    Downloads ``TCP.csv`` and writes ``data/catalog/tcp.jsonl`` with id, collection, date,
    author, title, pages, and the raw-file URL. Small; runs anywhere.

``pull``
    Fetches each text's XML into ``data/corpus/tcp/xml/<id>.xml`` and a plain-text body into
    ``data/corpus/tcp/text/<id>.txt`` (TEI header dropped, body text only). Resumable, one
    request per ``--delay`` seconds. About 25 GB of XML; meant for the data machine.

Usage::

    python -m ingest.eebo_tcp catalog
    python -m ingest.eebo_tcp pull [--limit N] [--collection eebo|evans|ecco]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

INDEX_URL = "https://raw.githubusercontent.com/textcreationpartnership/Texts/master/TCP.csv"
RAW_URL = "https://raw.githubusercontent.com/textcreationpartnership/{id}/master/{id}.xml"
CATALOG = Path("data/catalog/tcp.jsonl")
SUMMARY = Path("data/catalog/tcp_summary.md")
CORPUS = Path("data/corpus/tcp")
USER_AGENT = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
TEI_NS = "{http://www.tei-c.org/ns/1.0}"
COLLECTION = {"A": "eebo", "B": "eebo", "N": "evans", "K": "ecco"}


def fetch(url: str, retries: int = 4) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
            print(f"retry {attempt + 1} for {url}: {exc}", file=sys.stderr)
    raise RuntimeError("unreachable")


def year_of(s: str) -> int | None:
    m = re.search(r"(\d{4})", s or "")
    return int(m.group(1)) if m else None


def catalog() -> int:
    rows = list(csv.DictReader(fetch(INDEX_URL).decode("utf-8", "replace").splitlines()))
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    recs = []
    for r in rows:
        tid = r["TCP"]
        recs.append(
            {
                "id": tid,
                "collection": COLLECTION.get(tid[:1], "other"),
                "status": r["Status"],
                "date": r["Date"],
                "year": year_of(r["Date"]),
                "author": r["Author"],
                "title": r["Title"],
                "stc": r["STC"],
                "pages": int(r["Pages"]) if r["Pages"].isdigit() else None,
                "url": RAW_URL.format(id=tid),
            }
        )
    with CATALOG.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    by_col = Counter(r["collection"] for r in recs)
    by_status = Counter(r["status"] for r in recs)
    decades = Counter((r["year"] // 10) * 10 for r in recs if r["year"])
    lines = [
        "# Text Creation Partnership index",
        "",
        f"- Texts: {len(recs):,} from {INDEX_URL}",
        f"- By collection: {dict(by_col)}",
        f"- By status in the index: {dict(by_status)} (the raw files are served for both)",
        "",
        "| Decade | Texts |",
        "| --- | --- |",
    ]
    for d in sorted(decades):
        lines.append(f"| {d}s | {decades[d]:,} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(SUMMARY.read_text())
    print(f"wrote {len(recs):,} records to {CATALOG}")
    return 0


def tei_text(xml_bytes: bytes) -> str:
    """Body text of a TEI P5 file: header dropped, block elements separated by newlines."""
    root = ET.fromstring(xml_bytes)
    body = root.find(f".//{TEI_NS}text")
    if body is None:
        return ""
    parts: list[str] = []
    block = {"p", "head", "l", "item", "lg", "div", "sp", "stage", "note", "closer", "opener"}

    def walk(el: ET.Element) -> None:
        if el.tag.replace(TEI_NS, "") in block:
            parts.append("\n")
        if el.text:
            parts.append(el.text)
        for child in el:
            walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(body)
    text = "".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def pull(limit: int | None, delay: float, collection: str | None) -> int:
    recs = [json.loads(line) for line in CATALOG.open(encoding="utf-8")]
    if collection:
        recs = [r for r in recs if r["collection"] == collection]
    xml_dir, txt_dir = CORPUS / "xml", CORPUS / "text"
    xml_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    todo = [r for r in recs if not (txt_dir / f"{r['id']}.txt").exists()]
    print(f"{len(recs):,} texts in scope; {len(recs) - len(todo):,} done; {len(todo):,} to fetch")
    failed = CORPUS / "failed.txt"
    n = 0
    for r in todo:
        try:
            data = fetch(r["url"])
        except Exception as exc:  # noqa: BLE001
            failed.open("a").write(f"{r['id']}\t{exc}\n")
            continue
        (xml_dir / f"{r['id']}.xml").write_bytes(data)
        try:
            (txt_dir / f"{r['id']}.txt").write_text(tei_text(data), encoding="utf-8")
        except ET.ParseError as exc:
            failed.open("a").write(f"{r['id']}\tparse: {exc}\n")
        n += 1
        if n % 200 == 0:
            print(f"  fetched {n:,}/{len(todo):,}", flush=True)
        if limit and n >= limit:
            print(f"stopped at --limit {limit}")
            break
        time.sleep(delay)
    print(f"fetched {n:,} texts into {CORPUS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog")
    p = sub.add_parser("pull")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--collection", choices=["eebo", "evans", "ecco"])
    a = ap.parse_args(argv)
    return catalog() if a.cmd == "catalog" else pull(a.limit, a.delay, a.collection)


if __name__ == "__main__":
    sys.exit(main())
