"""Word counts and assembled samples for the candidate authors (BOM-13).

Applies the counting rule in ``docs/candidates.md`` ("Counting rule for the JSP sources",
rules 1-10) to every fetched source in ``data/candidates/sources.json``:

- Joseph Smith Papers sources are split by hand at word level, using JSP's own
  ``<span class="josephswriting">`` markup, and the three books (Revelation Book 1,
  Letterbook 1, Journal 1832-1834) are cut into their table-of-contents entries first.
- Internet Archive sources are counted as raw OCR tokens.

Writes:

- ``data/candidates/units.csv``: one row per counted unit (source, entry, author, sample, period,
  words, decision). Titles and counts only, no text, so it is public.
- ``data/candidates/word_counts.json``: totals per candidate, sample and period, with the
  section 3 floor flag, stamped with the config hash.
- ``data/private/candidates/samples/<candidate>__<sample>__<period>.txt``: the assembled text of
  each JSP sample (private: JSP transcripts are copyrighted).

Usage::

    python -m ingest.candidate_words
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from ingest import jsp
from ingest.candidates import MANIFEST, PRIVATE_DIR, PUBLIC_DIR, load_manifest
from metadata import config

SELECTIONS = Path("data/candidates/selections.json")
SIGNED = Path("data/candidates/signed_items.json")  # rules 11-16, from ingest.signed_items
UNITS_OUT = Path("data/candidates/units.csv")
COUNTS_OUT = Path("data/candidates/word_counts.json")
SAMPLES_DIR = PRIVATE_DIR / "samples"
SALE_DATE = "1830-03-26"  # Book of Mormon on sale; rule 7, as for Revelation Book 1
BOOKS = ("js-1828-1829-revelations", "js-letterbook-1", "js-journal-1832-1834")
# Rule 5: Letterbook 1 entries that are the same document as a source with its own id.
LETTERBOOK_OWN_ID = {
    "History, circa Summer 1832": "js-1832-history",
    "Letter to Oliver Cowdery • 22 October 1829": "js-1829-10-22-letter-cowdery",
    "Letter to William W. Phelps • 27 November 1832": "js-1832-11-27-letter-phelps",
    "Letter to Noah C. Saxton • 4 January 1833": "js-1833-01-04-letter-saxton",
    "Letter to William W. Phelps • 11 January 1833": "js-1833-01-11-letter-phelps",
    "Letter from Oliver Cowdery • 6 November 1829": "oc-1829-11-06-letter",
    "Letter from Oliver Cowdery • 28 December 1829": "oc-1829-12-28-letter",
}
# Rule 5: not letters, history or revelation.
LETTERBOOK_NOT_PROSE = ("Index", "“Explanation of the Plat", "Plan of the House of the Lord")


def _period(date: str | None) -> str:
    return "pre1830" if date and date < SALE_DATE else "post1830"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z]+", "-", name.lower()).strip("-")


def _letter_author(title: str) -> str | None:
    """JSP's attribution from an entry title (rule 3)."""
    if title.startswith("Letter to "):
        return "Joseph Smith"
    m = re.match(r"Letter(?:, (.+?) to | from (.+?) •)", title)
    if m:
        return (m.group(1) or m.group(2)).strip()
    return None


def _records(sid: str) -> list[dict]:
    path = PRIVATE_DIR / f"{sid}.jsonl"
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def _toc(sid: str) -> list[dict]:
    first = json.loads((PRIVATE_DIR / "raw" / sid / "0001.json").read_text(encoding="utf-8"))
    return first.get("tableOfContents", [])


def jsp_units(entry: dict, selections: dict) -> list[dict]:
    """Counted units for one JSP source; each carries its tokens for sample assembly."""
    sid, prov = entry["id"], entry["provenance"]
    candidate = entry["candidate"]
    units: list[dict] = []

    def add(title, link_id, author, sample, period, tokens, decision):
        units.append(
            {
                "source": sid,
                "link_id": link_id,
                "title": title,
                "author": author,
                "sample": sample,
                "period": period,
                "words": len(tokens),
                "decision": decision,
                "tokens": tokens,
            }
        )

    def split_js(title, link_id, period, toks, other_sample, decision):
        """JS's own hand -> handwritten; other hands -> other_sample (None: excluded)."""
        mine = [w for w, js in toks if js]
        rest = [w for w, js in toks if not js]
        add(title, link_id, "Joseph Smith", "handwritten", period, mine, decision)
        if other_sample:
            add(title, link_id, "Joseph Smith", other_sample, period, rest, decision)
        else:
            add(title, link_id, None, "excluded", period, rest, f"{decision}; other hands")

    if sid not in BOOKS:
        html = "\n".join(r["clear_html"] for r in sorted(_records(sid), key=lambda r: r["page"]))
        toks = jsp.transcript_words(html)
        period = "pre1830" if entry.get("pre1830") else "post1830"
        if candidate != "Joseph Smith":
            # rule 3: the hand is the copyist's; the words are the author's
            add(entry["title"], None, candidate, prov, period, [w for w, _ in toks], "rule 3")
        else:
            other = {"handwritten": None, "dictated": "dictated"}.get(prov, "scribal_copy")
            split_js(entry["title"], None, period, toks, other, f"rule 4 ({prov})")
        return units

    sections = jsp.sections(_records(sid), _toc(sid))
    if sid == "js-1828-1829-revelations":
        chosen = {e["link_id"]: e for e in selections[sid]["entries"]}
        for s in sections:
            title = s["title"] or "(before the first entry)"
            toks = jsp.transcript_words(s["html"] or "")
            pick = chosen.get(s["link_id"])
            if pick and pick["decision"] == "pre1830":
                add(title, s["link_id"], "Joseph Smith", "dictated", "pre1830",
                    [w for w, _ in toks], pick["reason"])  # fmt: skip
            elif pick and pick["decision"] == "other_author":
                add(title, s["link_id"], None, "excluded", "pre1830", [w for w, _ in toks],
                    "rule 5: counted from oc-1829-06-articles")  # fmt: skip
            else:
                add(title, s["link_id"], None, "excluded", "post1830", [w for w, _ in toks],
                    "rule 9: Revelation Book 1 after March 1830")  # fmt: skip
        return units

    for s in sections:
        title = s["title"] or "(before the first entry)"
        toks = jsp.transcript_words(s["html"] or "")
        period = _period(s["toc_date"])
        if not s["anchor_found"]:
            add(title, s["link_id"], None, "excluded", period, [], "anchor not found")
        elif sid == "js-journal-1832-1834":
            split_js(title, s["link_id"], period, toks, None, "rule 6")
        elif title in LETTERBOOK_OWN_ID:
            add(title, s["link_id"], None, "excluded", period, [w for w, _ in toks],
                f"rule 5: counted from {LETTERBOOK_OWN_ID[title]}")  # fmt: skip
        elif s["link_id"] is None or title.startswith(LETTERBOOK_NOT_PROSE):
            add(title, s["link_id"], None, "excluded", period, [w for w, _ in toks],
                "rule 5: not a letter, history or revelation")  # fmt: skip
        else:
            author = _letter_author(title)
            if author == "Joseph Smith":
                split_js(title, s["link_id"], period, toks, "scribal_copy", "rule 5")
            elif author == "Oliver Cowdery":
                add(title, s["link_id"], author, "scribal_copy", period, [w for w, _ in toks],
                    "rule 5: Cowdery's letter")  # fmt: skip
            else:
                add(title, s["link_id"], None, "excluded", period, [w for w, _ in toks],
                    f"rule 5: by {author or 'unknown'}, not a candidate")  # fmt: skip
    return units


def ia_unit(entry: dict) -> dict | None:
    base = PRIVATE_DIR if entry["private"] else PUBLIC_DIR
    path = base / f"{entry['id']}.txt"
    if not path.exists():
        return None
    words = len(path.read_text(encoding="utf-8", errors="replace").split())
    period = "pre1830" if entry.get("pre1830") else "post1830"
    if entry.get("edition_of"):
        author, sample, decision = (
            None,
            "excluded",
            f"rules 10, 14: edition of {entry['edition_of']}",
        )
    elif entry["provenance"] == "edited":
        author, sample, decision = (
            None,
            "excluded",
            "rule 10: whole run; signed items counted apart",
        )
    else:
        author, sample, decision = entry["candidate"], entry["provenance"], "rule 10: raw OCR"
    return {
        "source": entry["id"],
        "link_id": None,
        "title": entry["title"],
        "author": author,
        "sample": sample,
        "period": period,
        "words": words,
        "decision": decision,
        "tokens": None,
    }


def signed_units(entry: dict, items: list[dict]) -> list[dict]:
    """Checked, admitted signed items of a periodical run (rules 11-16), as raw OCR tokens."""
    mine = [i for i in items if i["source"] == entry["id"] and i.get("checked") and i["admit"]]
    if not mine:
        return []
    lines = (PUBLIC_DIR / f"{entry['id']}.txt").read_text(encoding="utf-8", errors="replace")
    lines = lines.splitlines()
    out = []
    for i in mine:
        text = "\n".join(lines[i["start"] - 1 : i["end"]])
        out.append(
            {
                "source": entry["id"],
                "link_id": f"lines {i['start']}-{i['end']}",
                "title": i.get("note") or i.get("opening") or "",
                "author": i["signer"],
                "sample": "printed_by_author",
                "period": "pre1830" if entry.get("pre1830") else "post1830",
                "words": len(text.split()),
                "decision": "rule 11: signed item",
                "tokens": None,
            }
        )
    return out


def build(root: Path = Path(".")) -> tuple[list[dict], dict]:
    entries = load_manifest(root / MANIFEST)
    selections = json.loads((root / SELECTIONS).read_text(encoding="utf-8"))
    units: list[dict] = []
    for e in entries:
        if e["kind"] == "jsp_page" and (PRIVATE_DIR / f"{e['id']}.jsonl").exists():
            units.extend(jsp_units(e, selections))
        elif e["kind"] == "ia_djvu":
            u = ia_unit(e)
            if u:
                units.append(u)
            if e["provenance"] == "edited" and (root / SIGNED).exists():
                units.extend(signed_units(e, json.loads((root / SIGNED).read_text("utf-8"))))
    cfg = config.load()
    floor = cfg["candidates"]["min_masked_words"]
    totals: dict[tuple, int] = defaultdict(int)
    for u in units:
        if u["author"] and u["words"]:
            totals[u["author"], u["sample"], u["period"]] += u["words"]
    rows = [
        {
            "candidate": c,
            "sample": s,
            "period": p,
            "raw_words": n,
            # rule 8: below the floor before masking stays below after; above is provisional
            "flag": "unreliable sample" if n < floor else "provisional until BOM-16 masking",
        }
        for (c, s, p), n in sorted(totals.items())
    ]
    summary = {
        "config_sha256": config.sha256_of_config(),
        "rule": "docs/candidates.md, 'Counting rule for the JSP sources' (BOM-13)",
        "min_masked_words": floor,
        "rows": rows,
    }
    return units, summary


def write(units: list[dict], summary: dict) -> None:
    fields = ["source", "link_id", "title", "author", "sample", "period", "words", "decision"]
    with UNITS_OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[*fields, "config_sha256"])
        w.writeheader()
        for u in units:
            w.writerow({**{k: u[k] for k in fields}, "config_sha256": summary["config_sha256"]})
    COUNTS_OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", "utf-8")
    samples: dict[tuple, list[str]] = defaultdict(list)
    for u in units:
        if u["author"] and u["tokens"]:
            samples[u["author"], u["sample"], u["period"]].append(
                f"## {u['source']} | {u['title']}\n" + " ".join(u["tokens"])
            )
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for (c, s, p), parts in samples.items():
        out = SAMPLES_DIR / f"{_slug(c)}__{s}__{p}.txt"
        out.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    units, summary = build()
    write(units, summary)
    for r in summary["rows"]:
        print(
            f"{r['candidate']:18s} {r['sample']:18s} {r['period']:9s}",
            f"{r['raw_words']:>9,d}  {r['flag']}",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
