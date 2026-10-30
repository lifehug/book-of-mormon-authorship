"""Book of Mormon text inside the corpus, kept out of every pool (4.2).

Pre-registration 4.2 seals the Book of Mormon from training, tuning, threshold setting and
feature selection until the blind run, and registers a contamination check: drop any volume
holding a Book of Mormon string of ``sealing.contamination_min_tokens`` (12) tokens or more.

The corpus holds copies of it. On 2026-10-27, six catalog rows with text are editions: three
Internet Archive scans of the 1830 printing, a HathiTrust one, a periodical's reprint, and a
modern edition whose catalogue date (1800) puts it inside the 1780-1830 window. Nothing had read
them for any sealed purpose -- they had been labelled by genre, cleaned and hashed -- but the
function-word list, the control pools and the time-locked model's training set are all drawn
from the comparison corpus, so they are listed here and every pool excludes them.

Two layers:

``titles``   rows whose catalogue title names the book (``sealed.json``), a fast first line
``contaminated(text)``  the registered check itself, on a text: True if it shares any 12-token
             string with the 1830 edition *that is not also in the KJV*. Pools run it on every
             member, which also catches extracts quoted inside other works.

Why the KJV strings are left out. Read literally, "a Book of Mormon string of 12 or more
tokens" includes the Isaiah, Matthew and Malachi chapters the Book of Mormon reproduces, and the
first run of the check on the control pools flagged 4,267 volumes -- period sermons and
histories quoting the same chapters. That would strip religious prose from every pool and from
the time-locked model's training data, which is not what the rule is for: it exists to keep the
Book of Mormon's own text out. So a 12-token string counts only if the KJV does not contain it.
A second pass showed that excluding exact KJV strings is not enough: 1,498 volumes still matched,
on biblical phrases in period variants ("plough-shares", "the sins of the world") that the Book
of Mormon also uses. So the strings come from the Book of Mormon's *original* spans only, its
text outside BOM-16's KJV masks (``data/kjv_mask/bom/spans.jsonl``), and a string never bridges
a removed span. This interpretation is registered by Amendment 6
(``sealing.contamination_excludes_kjv``, ``contamination_min_shared``).

Even then, a single shared string is not evidence: on the control pools the most any
volume shared was 9 (Books of Common Prayer, a Quaker journal), against 109,011 or more for every
copy of the book. A volume is contaminated when it shares at least ``MIN_SHARED`` distinct
strings.

Tokens follow Amendment 2's registered tokenisation (``kjv_mask.align.norm_token``).

Usage::

    python -m metadata.sealed titles      # -> data/catalog/sealed.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import _WORD, norm_token
from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
MASKS = Path("data/kjv_mask/bom/spans.jsonl")
# registered, Amendment 6. Measured 2026-10-27: no control-pool text shares
# more than 9 distinct strings with the Book of Mormon's original text (liturgy and biblical
# phrasing); the six copies of the book share 109,011 to 174,655. 20 is above the first and
# low enough to catch a quoted extract of about 30 words.
MIN_SHARED = 20
OUT = Path("data/catalog/sealed.json")
TITLE = re.compile(
    r"\bbook of morm[ao]n\b|\bgolden bible\b", re.IGNORECASE
)  # "Morman": a misspelt catalog title

_GRAMS: set[int] | None = None


def _tokens(text: str) -> list[str]:
    return [norm_token(m.group(0)) for m in _WORD.finditer(text)]


def _grams(toks: list[str], n: int) -> set[int]:
    return {hash(tuple(toks[i : i + n])) for i in range(len(toks) - n + 1)}


def _bom_grams(n: int) -> set[int]:
    global _GRAMS
    if _GRAMS is None:
        masks = {}
        for line in MASKS.read_text().splitlines():
            r = json.loads(line)
            masks[r["id"]] = r["spans"]
        grams: set[int] = set()
        for line in EDITION.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if not r["book"]:
                continue
            text, pos, parts = r["text"], 0, []
            for sp in sorted(masks.get(f"bom:{r['seq']}", []), key=lambda x: x["start"]):
                parts.append(text[pos : sp["start"]])
                pos = max(pos, sp["end"])
            parts.append(text[pos:])
            for part in parts:  # strings never bridge a removed KJV span
                grams |= _grams(_tokens(part), n)
        chapters: dict[tuple, list[str]] = {}  # verse order, so strings across verses count
        for line in KJV.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            chapters.setdefault((r["book"], r["chapter"]), []).extend(_tokens(r["text"]))
        kjv_grams = set().union(*(_grams(t, n) for t in chapters.values()))
        _GRAMS = grams - kjv_grams
    return _GRAMS


def shared_strings(text: str) -> int:
    """Distinct Book of Mormon original-text strings of 12 tokens that ``text`` contains."""
    n = load_config()["sealing"]["contamination_min_tokens"]
    grams = _bom_grams(n)
    toks = _tokens(text)
    return len({hash(tuple(toks[i : i + n])) for i in range(len(toks) - n + 1)} & grams)


def contaminated(text: str) -> bool:
    """4.2's check, with the count threshold measured on the corpus (``MIN_SHARED``).

    Hashes stand in for the tuples to keep memory small; a collision can only make the check
    stricter (a false exclusion), never let Book of Mormon text through."""
    return shared_strings(text) >= MIN_SHARED


def titles() -> int:
    rows = pq.read_table(CATALOG, columns=["work_id", "title", "year", "has_text"]).to_pylist()
    hits = [r for r in rows if TITLE.search(r["title"] or "")]
    out = {
        "rule": "catalogue title names the Book of Mormon; see metadata/sealed.py",
        "config_sha256": sha256_of_config(),
        "works": [
            {
                "work_id": r["work_id"],
                "year": r["year"],
                "has_text": r["has_text"],
                "title": (r["title"] or "")[:200],
            }
            for r in hits
        ],  # fmt: skip
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(
        f"{len(hits)} titled works sealed ({sum(r['has_text'] for r in hits)} with text) -> {OUT}"
    )
    return 0


def sealed_ids() -> set[str]:
    return {w["work_id"] for w in json.loads(OUT.read_text())["works"]}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["titles"]:
        return titles()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
