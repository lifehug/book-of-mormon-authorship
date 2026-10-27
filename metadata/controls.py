"""The control sets (BOM-18).

Section 3 registers four control groups: pseudo-biblical texts (Leacock, Snowden, Linning, Hunt,
and every other example found in the catalog), 1820s sermons and tracts, histories and Native
American origin texts, and a general prose baseline of fiction and periodicals. Amendment 2
requires membership to be published as an explicit list of identifiers with its SHA-256 before
the benchmark runs. Amendment 3: genre-matched control sets match a work on *either* of its two
labels.

Every set draws on the same eligible pool:

* has text, published 1780-1830 (``corpus.date_range``; TCP's earlier texts are out),
* a dedup keeper (``duplicates.parquet``; reprints count once),
* not flagged ``ocr_excluded`` by BOM-14 (``data/ocr_quality/volumes.parquet``),
* not a candidate's work, so candidates and controls stay disjoint -- except where section 3
  names a candidate's work as a control (Hunt's *The Late War*), which stays and is flagged,
* not sealed: no title naming the Book of Mormon and no 12-token string shared with it (4.2,
  ``metadata.sealed``), checked on every member's text.

Genre comes from pass 1 (``genre.parquet``); ``uncertain`` and ``PARSE_FAIL`` match nothing.

Native American origin texts are a named subset of the history set, picked by title words
(``ORIGINS``); the history set itself is genre-defined. The named pseudo-biblical works are found
by title (``NAMED``) whatever their genre label says.

Usage::

    python -m metadata.controls build      # -> data/controls/
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from metadata import sealed
from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
GENRE = Path("data/catalog/genre.parquet")
DUPES = Path("data/catalog/duplicates.parquet")
VOLUMES = Path("data/ocr_quality/volumes.parquet")
SIGS = Path("data/catalog/signatures")
OUT = Path("data/controls")

NAMED = {
    "leacock": r"first book of the american chronicles of the times",
    "snowden": r"american revolution.{0,40}(style of ancient history|scripture style)"
    r"|history of north and south america",
    "linning": r"first book of napoleon",
    "hunt": r"the late war,? between the united states and great britain",
}
ORIGINS = re.compile(
    r"\b(indians?|aborigin\w*|lost tribes|ten tribes|israelites? in america|"
    r"american antiquities|origin of the (american|indian)|hebrews)\b",
    re.IGNORECASE,
)
SETS = {
    "pseudo_biblical": {"pseudo_biblical"},
    "sermons_1820s": {"sermon_devotional"},
    "history": {"history_chronicle"},
    "general_prose": {"fiction_narrative", "newspaper_periodical"},
}


def _labels(g: str | None) -> set[str]:
    return {x.strip() for x in (g or "").split(",")} - {"", "uncertain", "PARSE_FAIL"}


def _candidate_authors() -> set[str]:
    """Surnames of the registered candidates, for keeping their works out of the pools."""
    return {"smith, joseph", "cowdery", "rigdon", "pratt, parley", "phelps", "spalding",
            "spaulding", "smith, ethan", "hunt, gilbert"}  # fmt: skip


def _is_candidate(author_norm: str) -> bool:
    return any(author_norm.startswith(a) for a in _candidate_authors())


def build() -> int:
    cfg = load_config()
    lo, hi = cfg["corpus"]["date_range"]
    cat = pq.read_table(CATALOG).to_pylist()
    genre = {r["work_id"]: r["genre"] for r in pq.read_table(GENRE).to_pylist()}
    nonkeeper = {r["work_id"] for r in pq.read_table(DUPES).to_pylist() if not r["is_keeper"]}
    excluded = set()
    if VOLUMES.exists():
        excluded = {
            r["work_id"]
            for r in pq.read_table(VOLUMES, columns=["work_id", "ocr_excluded"]).to_pylist()
            if r["ocr_excluded"]
        }
    else:
        print(f"warning: {VOLUMES} missing; OCR exclusion not applied", file=sys.stderr)
    words = {}
    for f in sorted(SIGS.glob("*.parquet")):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    seal = sealed.sealed_ids()

    drops: Counter = Counter()
    members: dict[str, list[dict]] = {k: [] for k in SETS}
    for r in cat:
        wid = r["work_id"]
        title = r["title"] or ""
        named = next((k for k, p in NAMED.items() if re.search(p, title, re.I)), None)
        labels = _labels(genre.get(wid))
        sets = [k for k, want in SETS.items() if labels & want]
        if named:
            sets = sorted(set(sets) | {"pseudo_biblical"})
        if not sets:
            continue
        reason = None
        if not r["has_text"]:
            reason = "no_text"
        elif r["year"] is None or not lo <= r["year"] <= hi:
            reason = "out_of_window"
        elif wid in nonkeeper:
            reason = "duplicate"
        elif wid in excluded:
            reason = "ocr_excluded"
        elif wid in seal:
            reason = "sealed_title"
        elif _is_candidate(r["author_norm"] or "") and not named:
            reason = "candidate_work"
        if reason:
            drops[reason] += 1
            continue
        for k in sets:
            if k == "sermons_1820s" and not 1820 <= r["year"] <= 1829:
                continue
            members[k].append(
                {
                    "work_id": wid,
                    "source": r["source"],
                    "year": r["year"],
                    "words": words.get(wid),
                    "named": named,
                    "origins": k == "history" and bool(ORIGINS.search(title)),
                    "candidate_overlap": _is_candidate(r["author_norm"] or ""),
                }
            )

    # 4.2's registered check on every member's text, after the cheap filters
    contaminated = set()
    for ms in members.values():
        for m in ms:
            if m["work_id"] in contaminated:
                continue
            path = next(r["text_path"] for r in cat if r["work_id"] == m["work_id"])
            if sealed.contaminated(Path(path).read_text(encoding="utf-8", errors="replace")):
                contaminated.add(m["work_id"])
    for k in members:
        members[k] = [m for m in members[k] if m["work_id"] not in contaminated]

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"config_sha256": sha256_of_config(), "dropped": dict(drops),
               "contaminated_12_token": sorted(contaminated), "sets": {}}  # fmt: skip
    for k, ms in members.items():
        ms.sort(key=lambda m: m["work_id"])
        ids = "".join(m["work_id"] + "\n" for m in ms)
        (OUT / f"{k}.txt").write_text(ids)
        with (OUT / f"{k}.jsonl").open("w") as fh:
            fh.writelines(json.dumps(m) + "\n" for m in ms)
        summary["sets"][k] = {
            "volumes": len(ms),
            "words": sum(m["words"] or 0 for m in ms),
            "by_source": dict(Counter(m["source"] for m in ms)),
            "named": dict(Counter(m["named"] for m in ms if m["named"])),
            "origins_subset": sum(m["origins"] for m in ms),
            "sha256_of_id_list": hashlib.sha256(ids.encode()).hexdigest(),
        }
    (OUT / "controls.json").write_text(json.dumps(summary, indent=1) + "\n")
    for k, s in summary["sets"].items():
        print(f"{k:<16} {s['volumes']:>7,} volumes {s['words']:>14,} words  {s['by_source']}")
    print(f"dropped: {dict(drops)}; contaminated (12-token): {len(contaminated)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return build() if args[:1] == ["build"] else 1


if __name__ == "__main__":
    sys.exit(main())
