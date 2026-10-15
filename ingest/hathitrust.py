"""HathiTrust public-domain volumes, 1780-1830, measured against Harvard's slice (BOM-08).

HathiTrust publishes its whole catalog monthly as a tab-separated "hathifile" (about 1.2 GB
gzipped, 26 columns, no header; see ``FIELDS``). ``catalog`` streams it, keeps English
public-domain volumes whose rights date falls in 1780-1830, and marks which of them Harvard's
Institutional Books slice already covers (by HathiTrust id prefix ``hvd.`` or by OCLC number).
The remainder is what BOM-08 would add.

Full text for public-domain volumes is not bulk-downloadable from HathiTrust without a
Research Center account; the Extracted Features dataset (page-level word counts, no running
text) is open. ``pull`` is therefore not implemented here: the summary reports how much text
HathiTrust would add, and the decision to request Research Center access is made from that.

Usage::

    python -m ingest.hathitrust catalog --hathifile /path/to/hathi_full_YYYYMMDD.txt.gz
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

FIELDS = [
    "htid", "access", "rights", "ht_bib_key", "description", "source", "source_bib_num",
    "oclc_num", "isbn", "issn", "lccn", "title", "imprint", "rights_reason_code",
    "rights_timestamp", "us_gov_doc_flag", "rights_date_used", "pub_place", "lang", "bib_fmt",
    "collection_code", "content_provider_code", "responsible_entity_code",
    "digitization_agent_code", "access_profile_code", "author",
]  # fmt: skip
KEEP = [
    "htid", "rights", "ht_bib_key", "oclc_num", "lccn", "title", "author", "imprint",
    "rights_date_used", "pub_place", "lang", "bib_fmt", "description",
]  # fmt: skip
HARVARD_CATALOG = Path("data/catalog/institutional_books.jsonl")
OUT = Path(
    "data/catalog/hathitrust.jsonl.gz"
)  # 135k rows; gzipped to stay well under GitHub limits
SUMMARY = Path("data/catalog/hathitrust_summary.md")
YEAR_MIN, YEAR_MAX = 1780, 1830
PD_RIGHTS = {"pd", "pdus", "cc-zero", "cc-by-4.0", "cc-by-3.0"}


def parse_row(line: str) -> dict:
    parts = line.rstrip("\n").split("\t")
    parts += [""] * (len(FIELDS) - len(parts))
    return dict(zip(FIELDS, parts, strict=False))


def year_of(s: str) -> int | None:
    m = re.match(r"(\d{4})", s or "")
    return int(m.group(1)) if m else None


def wanted(rec: dict) -> bool:
    if rec["lang"] != "eng" or rec["rights"] not in PD_RIGHTS:
        return False
    y = year_of(rec["rights_date_used"])
    return y is not None and YEAR_MIN <= y <= YEAR_MAX


def harvard_oclc() -> set[str]:
    out: set[str] = set()
    if not HARVARD_CATALOG.exists():
        return out
    for line in HARVARD_CATALOG.open(encoding="utf-8"):
        ids = json.loads(line).get("identifiers_src") or {}
        for v in ids.get("ocolc") or []:
            out.add(re.sub(r"\D", "", str(v)))
    return out


def catalog(hathifile: Path) -> int:
    hv_oclc = harvard_oclc()
    kept: list[dict] = []
    scanned = 0
    opener = gzip.open if hathifile.suffix == ".gz" else open
    with opener(hathifile, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            scanned += 1
            rec = parse_row(line)
            if not wanted(rec):
                continue
            row = {k: rec[k] for k in KEEP}
            row["year"] = year_of(rec["rights_date_used"])
            oclcs = {re.sub(r"\D", "", o) for o in rec["oclc_num"].split(",") if o.strip()}
            row["harvard_scan"] = rec["htid"].startswith("hvd.")
            row["harvard_oclc_match"] = bool(oclcs & hv_oclc)
            row["in_harvard"] = row["harvard_scan"] or row["harvard_oclc_match"]
            kept.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    SUMMARY.write_text(summarize(kept, scanned, hathifile.name), encoding="utf-8")
    print(SUMMARY.read_text())
    print(f"wrote {len(kept):,} records to {OUT}")
    return 0


def summarize(kept: list[dict], scanned: int, name: str) -> str:
    new = [r for r in kept if not r["in_harvard"]]
    n_scan = sum(r["harvard_scan"] for r in kept)
    n_oclc = sum(r["harvard_oclc_match"] and not r["harvard_scan"] for r in kept)
    fmt = Counter(r["bib_fmt"] for r in kept)
    new_fmt = Counter(r["bib_fmt"] for r in new)
    src = Counter(r["htid"].split(".")[0] for r in new).most_common(12)
    dec = Counter((r["year"] // 10) * 10 for r in new)
    lines = [
        f"# HathiTrust public-domain English volumes, 1780-1830 ({name})",
        "",
        f"- Catalog rows scanned: {scanned:,}; kept (eng, public domain, rights date "
        f"1780-1830): {len(kept):,}",
        f"- Already in the Harvard slice: {len(kept) - len(new):,} "
        f"({n_scan:,} are Harvard's own scans; {n_oclc:,} match a Harvard OCLC number)",
        f"- Not in Harvard: {len(new):,} volumes ({dict(new_fmt)})",
        f"- Format of all kept: {dict(fmt)}",
        "",
        "Rights date is HathiTrust's `rights_date_used`, the publication date it based the "
        "rights determination on. `bib_fmt` BK = book, SE = serial.",
        "",
        "| Contributor (htid prefix) | Volumes not in Harvard |",
        "| --- | --- |",
    ]
    lines += [f"| {k} | {v:,} |" for k, v in src]
    lines += ["", "| Decade | Volumes not in Harvard |", "| --- | --- |"]
    lines += [f"| {d}s | {dec[d]:,} |" for d in sorted(dec)]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("catalog")
    p.add_argument("--hathifile", type=Path, required=True)
    a = ap.parse_args(argv)
    return catalog(a.hathifile)


if __name__ == "__main__":
    sys.exit(main())
