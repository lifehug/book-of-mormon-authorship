"""HathiTrust public-domain volumes, 1780-1830, measured against Harvard's slice (BOM-08).

HathiTrust publishes its whole catalog monthly as a tab-separated "hathifile" (about 1.2 GB
gzipped, 26 columns, no header; see ``FIELDS``). ``catalog`` streams it, keeps English
public-domain volumes whose rights date falls in 1780-1830, and marks which of them Harvard's
Institutional Books slice already covers (by HathiTrust id prefix ``hvd.`` or by OCLC number).
The remainder is what BOM-08 would add.

Full text is bulk-available only through HathiTrust's dataset request (docs/hathitrust-request.md);
scripted downloads from babel.hathitrust.org are blocked. Two open routes are implemented:

``ef``
    rsync HathiTrust Research Center Extracted Features 2.5 (per-page token counts and
    part-of-speech tags, no running text) for a list of volume ids, from the public rsync
    module ``data.analytics.hathitrust.org::features``. Paths follow HTRC's stubbytree
    layout; needs Homebrew rsync on macOS.

``map-ia``
    For volumes digitized by the Internet Archive (htid contains an ark id), look up the
    Archive item by ``identifier-ark`` and write ``data/catalog/hathitrust_ia_map.jsonl`` plus
    an id list that ``ingest.internet_archive pull --ids`` can take, so their text comes from
    the Archive directly.

Usage::

    python -m ingest.hathitrust catalog --hathifile /path/to/hathi_full_YYYYMMDD.txt.gz
    python -m ingest.hathitrust map-ia
    python -m ingest.hathitrust ef [--ids FILE] [--limit N]
    python -m ingest.hathitrust text [--workers N]

``text``
    The rsync dataset (ticket GS-17502) delivers one zip of per-page OCR files per volume
    under ``data/corpus/hathitrust/<ns>/pairtree_root/...``. This joins each volume's pages,
    in page order, into one file ``data/corpus/hathitrust_text/<ns>.<cleaned id>.txt`` so the
    catalog can point at it like any other source. The zips are read, never moved or
    deleted; the text is derived and rebuilds from them. Resumable: a volume whose text file
    exists is skipped.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
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


EF_MODULE = "data.analytics.hathitrust.org::features"
EF_DIR = Path("data/corpus/hathitrust_ef")
IDS_NOT_IN_HARVARD = Path("data/catalog/hathitrust_ids_not_in_harvard.txt")
IA_MAP = Path("data/catalog/hathitrust_ia_map.jsonl")
IA_IDS = Path("data/catalog/hathitrust_ia_ids.txt")


def stubbytree_path(htid: str) -> str:
    """Extracted Features 2.x path for a volume id, per HTRC's "stubbytree" rule
    (htrc-feature-reader ``id_to_stubbytree``): ``<ns>/<every 3rd char of the cleaned id>/
    <ns>.<cleaned id>.json.bz2``, where cleaning maps ``:`` to ``+``, ``/`` to ``=``, ``.``
    to ``,``."""
    ns, ident = htid.split(".", 1)
    clean = ident.replace(":", "+").replace("/", "=").replace(".", ",")
    return f"{ns}/{clean[::3]}/{ns}.{clean}.json.bz2"


RSYNC_DIR = Path("data/corpus/hathitrust")
TEXT_DIR = Path("data/corpus/hathitrust_text")


def clean_id(htid: str) -> str:
    """``uc2.ark:/13960/t1zc7t220`` -> ``uc2.ark+=13960=t1zc7t220``: HathiTrust's pairtree
    cleaning (``:`` to ``+``, ``/`` to ``=``, ``.`` to ``,``) applied after the namespace, which
    makes the id a safe file name."""
    ns, ident = htid.split(".", 1)
    return f"{ns}." + ident.replace(":", "+").replace("/", "=").replace(".", ",")


def zip_path(htid: str, root: Path = RSYNC_DIR) -> Path:
    """Where the rsync dataset puts a volume's zip: the cleaned id cut into two-character
    pairtree directories, then a directory and a zip named for the cleaned id."""
    ns, clean = clean_id(htid).split(".", 1)
    pairs = [clean[i : i + 2] for i in range(0, len(clean), 2)]
    return root / ns / "pairtree_root" / Path(*pairs) / clean / f"{clean}.zip"


def text_of(zpath: Path) -> str:
    """A volume's pages joined in page order (the page files are zero-padded sequence numbers)."""
    with zipfile.ZipFile(zpath) as zf:
        names = sorted(n for n in zf.namelist() if n.endswith(".txt"))
        return "\n".join(zf.read(n).decode("utf-8", errors="replace") for n in names)


def _extract_one(htid: str) -> str:
    out = TEXT_DIR / f"{clean_id(htid)}.txt"
    if out.exists():
        return "skipped"
    zpath = zip_path(htid)
    if not zpath.exists():
        return "no_zip"
    tmp = out.with_suffix(".txt.tmp")
    tmp.write_text(text_of(zpath), encoding="utf-8")
    tmp.rename(out)
    return "written"


def extract_text(workers: int) -> int:
    ids = [ln.strip() for ln in (RSYNC_DIR / "present.txt").read_text().splitlines() if ln.strip()]
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    counts: Counter = Counter()
    with ProcessPoolExecutor(workers) as pool:
        for i, result in enumerate(pool.map(_extract_one, ids, chunksize=64), 1):
            counts[result] += 1
            if i % 5000 == 0:
                print(f"  {i:,}/{len(ids):,}  {dict(counts)}", flush=True)
    print(f"{len(ids):,} volumes: {dict(counts)} -> {TEXT_DIR}")
    return 1 if counts["no_zip"] else 0


def ef(ids_file: Path, limit: int | None) -> int:
    import subprocess

    ids = [line.strip() for line in ids_file.open(encoding="utf-8") if line.strip()]
    if limit:
        ids = ids[:limit]
    EF_DIR.mkdir(parents=True, exist_ok=True)
    listing = EF_DIR / "files_from.txt"
    listing.write_text("\n".join(stubbytree_path(h) for h in ids) + "\n", encoding="utf-8")
    # Needs real rsync (brew install rsync); macOS's openrsync lacks --ignore-missing-args
    # and mishandles --files-from against this server.
    rsync = "/opt/homebrew/bin/rsync" if Path("/opt/homebrew/bin/rsync").exists() else "rsync"
    cmd = [
        rsync, "-a", "--files-from", str(listing), "--ignore-missing-args", "--timeout=120",
        "--info=progress2", EF_MODULE + "/", str(EF_DIR) + "/",
    ]  # fmt: skip
    print(" ".join(cmd))
    rc = subprocess.run(cmd, check=False).returncode
    got = sum(1 for _ in EF_DIR.rglob("*.json.bz2"))
    print(f"rsync exit {rc}; {got:,} feature files on disk under {EF_DIR}")
    return rc


def map_ia(batch: int = 40, delay: float = 1.0) -> int:
    import time
    import urllib.parse
    import urllib.request

    want = {line.strip() for line in IDS_NOT_IN_HARVARD.open(encoding="utf-8") if line.strip()}
    arks = {}
    with gzip.open(OUT, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["htid"] in want and "ark:/" in r["htid"]:
                arks["ark:/" + r["htid"].split("ark:/", 1)[1]] = r["htid"]
    done: dict[str, dict] = {}
    if IA_MAP.exists():
        for line in IA_MAP.open(encoding="utf-8"):
            r = json.loads(line)
            done[r["ark"]] = r
    todo = [a for a in arks if a not in done]
    print(f"{len(arks):,} ark ids; {len(done):,} mapped; {len(todo):,} to look up")
    ua = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
    with IA_MAP.open("a", encoding="utf-8") as out:
        for i in range(0, len(todo), batch):
            chunk = todo[i : i + batch]
            q = " OR ".join(f'identifier-ark:"{a}"' for a in chunk)
            url = (
                "https://archive.org/advancedsearch.php?"
                + urllib.parse.urlencode({"q": q, "rows": batch, "output": "json"}, doseq=True)
                + "&fl[]=identifier&fl[]=identifier-ark&fl[]=title&fl[]=year"
            )
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        docs = json.load(resp)["response"]["docs"]
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == 3:
                        raise
                    print("retry:", exc, file=sys.stderr)
                    time.sleep(10 * (attempt + 1))
            found = {}
            for d in docs:
                a = d.get("identifier-ark")
                a = a[0] if isinstance(a, list) else a
                if a in arks:
                    found[a] = d
            for a in chunk:
                d = found.get(a)
                rec = {
                    "ark": a,
                    "htid": arks[a],
                    "ia_identifier": d.get("identifier") if d else None,
                    "title": (d.get("title") if d else None),
                    "year": (d.get("year") if d else None),
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                done[a] = rec
            if (i // batch) % 50 == 0:
                print(f"  {min(i + batch, len(todo)):,}/{len(todo):,}", flush=True)
            time.sleep(delay)
    ids = sorted({r["ia_identifier"] for r in done.values() if r["ia_identifier"]})
    IA_IDS.write_text("\n".join(ids) + "\n", encoding="utf-8")
    missing = sum(1 for r in done.values() if not r["ia_identifier"])
    print(f"mapped {len(ids):,} to Internet Archive items; {missing:,} arks not found -> {IA_IDS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("catalog")
    p.add_argument("--hathifile", type=Path, required=True)
    sub.add_parser("map-ia")
    e = sub.add_parser("ef")
    e.add_argument("--ids", type=Path, default=IDS_NOT_IN_HARVARD)
    e.add_argument("--limit", type=int)
    t = sub.add_parser("text")
    t.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    if a.cmd == "catalog":
        return catalog(a.hathifile)
    if a.cmd == "map-ia":
        return map_ia()
    if a.cmd == "text":
        return extract_text(a.workers)
    return ef(a.ids, a.limit)


if __name__ == "__main__":
    sys.exit(main())
