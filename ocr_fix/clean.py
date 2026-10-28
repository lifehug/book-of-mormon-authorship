"""Rule-based OCR cleaning (BOM-14).

Three repairs, each conservative and each counted per document so its effect can be audited:

``long_s``   the long s (``ſ``) read as ``f``: ``firft``, ``faid``, ``houfes``. A lowercase,
             non-final ``f`` becomes ``s`` only when the resulting word occurs in at least
             ``LONG_S_RATIO`` times as many keyed period texts as the word as read
             (``ocr_fix.lexicon``). ``faid`` (41 texts) becomes ``said`` (6,001); ``fame``
             (2,617) never becomes ``same`` (6,245). A capital F is never touched: the long s
             had no capital form, and it was never set at the end of a word.
``hyphens``  a word broken across a line end is rejoined. The halves are joined outright when
             the joined form is a known word or either half is not; kept hyphenated when both
             halves are words and the joined form is not (``well-known``). Never across a page
             break, where a running header may sit between the halves.
``headers``  running headers, footers and bare page numbers. Where the text marks pages with
             form feeds (Harvard, HathiTrust), a line in the top or bottom ``EDGE_LINES`` of a
             page is dropped if its letters recur in that position on at least
             ``HEADER_MIN_PAGES`` pages and ``HEADER_MIN_SHARE`` of them, or if it is only a
             page number. Text with no page marks (the Internet Archive) gets the same test on
             short lines anywhere, against an estimated page count.

TCP is skipped: it is keyed by hand, not OCR'd, and its ``ſ`` is a correct transcription that
BOM-15 normalises. Nothing here edits a source file. Cleaned text goes to
``data/corpus/cleaned/<source>/`` and per-document counts to ``data/ocr_quality/cleaning.parquet``,
together with the OCR proxy metrics of the raw text (``ocr_fix.score``), computed here because
this is the one pass that reads every document; ``ocr_fix.calibrate`` turns them into an
estimated CER.

Every threshold below is an analytic choice outside the pre-registration and is listed in
Amendment 6 (``corpus.ocr_cleaning``).

Usage::

    python -m ocr_fix.clean run [--workers N] [--limit N]   # resumable
    python -m ocr_fix.clean sample N                         # print before/after for N docs
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import sha256_of_config
from ocr_fix import lexicon
from ocr_fix.score import load_lexicon, score_text

CATALOG = Path("data/catalog/catalog.parquet")
OUT_DIR = Path("data/corpus/cleaned")
STATS = Path("data/ocr_quality/cleaning.parquet")
SKIP_SOURCES = {"tcp"}
SINGLE_PAGE = {"chronicling_america"}

# registered, Amendment 6
LONG_S_RATIO = 100
EDGE_LINES = 2
HEADER_MIN_PAGES = 3
HEADER_MIN_SHARE = 0.05
SHORT_LINE = 60  # longest line treated as a header candidate in text without page marks
HEADER_MIN_LETTERS = 6  # shorter keys ("and", "dec", "vo") recur as content, not headers
CHARS_PER_PAGE = 2000  # page-count estimate for text without page marks

_TOKEN = re.compile(r"[A-Za-z]+")
_HYPHEN = re.compile(r"([A-Za-z]+)[-¬][ \t]*\n(?:[ \t]*\n)*[ \t]*([a-z][A-Za-z]*)")
# Roman numerals count as page numbers only at a page edge; elsewhere they number stanzas.
_PAGENUM = re.compile(r"^[\s\W]*(\d{1,4}|[ivxlcdm]{1,7})[\s\W]*$", re.IGNORECASE)
_DIGITS = re.compile(r"^[\s\W]*\d{1,4}[\s\W]*$")
_KEYCHARS = re.compile(r"[^a-z]")

_LEX: dict[str, int] | None = None
_WEBSTER: frozenset[str] | None = None
PROXY = ["lexicon_rate", "garbage_rate", "single_letter_rate", "mean_token_len", "nonalpha_ratio"]


def _lex() -> dict[str, int]:
    global _LEX
    if _LEX is None:
        _LEX = lexicon.load()
    return _LEX


def proxies(raw: str) -> dict[str, float]:
    """``ocr_fix.score`` metrics plus the share of tokens in the period lexicon."""
    global _WEBSTER
    if _WEBSTER is None:
        _WEBSTER = load_lexicon()
    m = score_text(raw, _WEBSTER)
    out = {k: float(m[k]) for k in PROXY}
    toks = [t.lower() for t in _TOKEN.findall(raw)]
    lex = _lex()
    out["period_lexicon_rate"] = sum(t in lex for t in toks) / len(toks) if toks else 0.0
    return out


def _fix_word(word: str, lex: dict[str, int]) -> str:
    spots = [i for i, c in enumerate(word[:-1]) if c == "f"]
    if not spots:
        return word
    low = word.lower()
    seen = lex.get(low, 0)
    best, best_n = word, 0
    # every non-final lowercase f at once, then each one alone ("fufficient" vs "fiftieth")
    cands = [spots] + ([[i] for i in spots] if len(spots) > 1 else [])
    for pos in cands:
        cand = "".join("s" if i in pos else c for i, c in enumerate(word))
        n = lex.get(cand.lower(), 0)
        if n > best_n and n >= max(1, LONG_S_RATIO * seen):
            best, best_n = cand, n
    return best


def fix_long_s(text: str, lex: dict[str, int]) -> tuple[str, int]:
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        new = _fix_word(m.group(0), lex)
        n += new != m.group(0)
        return new

    return _TOKEN.sub(sub, text), n


def rejoin_hyphens(text: str, lex: dict[str, int]) -> tuple[str, int]:
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        a, b = m.group(1), m.group(2)
        n += 1
        joined = a + b
        if joined.lower() in lex:
            return joined
        if a.lower() in lex and b.lower() in lex:
            return f"{a}-{b}"
        return joined

    return _HYPHEN.sub(sub, text), n


def _key(line: str) -> str:
    key = _KEYCHARS.sub("", line.lower())
    return key if len(key) >= HEADER_MIN_LETTERS else ""


def strip_headers(text: str) -> tuple[str, int]:
    if "\f" in text:
        return _strip_paged(text)
    return _strip_unpaged(text)


def _edges(lines: list[str]) -> list[int]:
    idx = [i for i, ln in enumerate(lines) if ln.strip()]
    return sorted(set(idx[:EDGE_LINES] + idx[-EDGE_LINES:]))


def _strip_paged(text: str) -> tuple[str, int]:
    pages = [p.split("\n") for p in text.split("\f")]
    counts: Counter = Counter()
    for lines in pages:
        counts.update({_key(lines[i]) for i in _edges(lines)} - {""})
    need = max(HEADER_MIN_PAGES, HEADER_MIN_SHARE * len(pages))
    headers = {k for k, c in counts.items() if c >= need}
    removed = 0
    for lines in pages:
        for i in _edges(lines):
            if _key(lines[i]) in headers or _PAGENUM.match(lines[i]):
                lines[i] = ""
                removed += 1
    return "\f".join("\n".join(lines) for lines in pages), removed


def _strip_unpaged(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    short = [_key(ln) for ln in lines if ln.strip() and len(ln.strip()) <= SHORT_LINE]
    counts = Counter(k for k in short if k)
    need = max(HEADER_MIN_PAGES, HEADER_MIN_SHARE * len(text) / CHARS_PER_PAGE)
    headers = {k for k, c in counts.items() if c >= need}
    removed = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s and len(s) <= SHORT_LINE and (_key(ln) in headers or _DIGITS.match(ln)):
            lines[i] = ""
            removed += 1
    return "\n".join(lines), removed


def clean(
    text: str, lex: dict[str, int] | None = None, headers: bool = True
) -> tuple[str, dict[str, int]]:
    """Headers first (they sit between hyphen halves), then hyphens, then long s.

    ``headers=False`` for single newspaper pages, which have no running header to find."""
    lex = _lex() if lex is None else lex
    text, h = strip_headers(text) if headers else (text, 0)
    text, j = rejoin_hyphens(text, lex)
    text, s = fix_long_s(text, lex)
    return text, {"header_lines": h, "hyphens": j, "long_s": s}


SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("source", pa.string()),
        ("clean_path", pa.string()),
        ("chars_in", pa.int64()),
        ("chars_out", pa.int64()),
        ("header_lines", pa.int64()),
        ("hyphens", pa.int64()),
        ("long_s", pa.int64()),
        *[(k, pa.float64()) for k in PROXY],
        ("period_lexicon_rate", pa.float64()),
    ]
)


def out_path(row: dict) -> Path:
    """Same file name as the source; Chronicling America keeps its per-title directory."""
    src = Path(row["text_path"])
    rel = Path(src.parent.name, src.name) if row["source"] == "chronicling_america" else src.name
    return OUT_DIR / row["source"] / rel


def _one(row: dict) -> dict:
    src = Path(row["text_path"])
    dst = out_path(row)
    raw = src.read_text(encoding="utf-8", errors="replace")
    text, counts = clean(raw, headers=row["source"] not in SINGLE_PAGE)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dst)
    return {
        "work_id": row["work_id"],
        "source": row["source"],
        "clean_path": str(dst),
        "chars_in": len(raw),
        "chars_out": len(text),
        **counts,
        **proxies(raw),
    }


def _todo(limit: int | None) -> tuple[list[dict], list[dict]]:
    rows = [
        r
        for r in pq.read_table(CATALOG, columns=["work_id", "source", "text_path"]).to_pylist()
        if r["text_path"] and r["source"] not in SKIP_SOURCES
    ]
    done = pq.read_table(STATS).to_pylist() if STATS.exists() else []
    have = {r["work_id"] for r in done}
    todo = [r for r in rows if r["work_id"] not in have]
    return (todo[:limit] if limit else todo), done


def _write(rows: list[dict]) -> None:
    STATS.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    tmp = STATS.with_suffix(".parquet.tmp")
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), tmp)
    tmp.replace(STATS)


def run(workers: int, limit: int | None) -> int:
    todo, done = _todo(limit)
    print(f"{len(todo):,} to clean ({len(done):,} done), {workers} workers", flush=True)
    start, n = time.time(), 0
    with ProcessPoolExecutor(workers) as pool:
        for rec in pool.map(_one, todo, chunksize=16):
            done.append(rec)
            n += 1
            if n % 20000 == 0:
                _write(done)
                rate = n / (time.time() - start)
                print(f"  {n:,}/{len(todo):,}  {rate:.0f} docs/s", flush=True)
    _write(done)
    tot = Counter()
    for r in done:
        tot.update({k: r[k] for k in ("header_lines", "hyphens", "long_s")})
    print(f"cleaned {n:,} in {time.time() - start:.0f}s; totals over {len(done):,}: {dict(tot)}")
    return 0


def sample(n: int, seed: int = 20261017) -> int:
    rows = [
        r
        for r in pq.read_table(CATALOG, columns=["work_id", "source", "text_path"]).to_pylist()
        if r["text_path"] and r["source"] not in SKIP_SOURCES
    ]
    for r in random.Random(seed).sample(rows, n):
        raw = Path(r["text_path"]).read_text(encoding="utf-8", errors="replace")
        text, counts = clean(raw, headers=r["source"] not in SINGLE_PAGE)
        print(f"== {r['work_id']}  {counts}  {len(raw):,} -> {len(text):,} chars")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--limit", type=int)
    s = sub.add_parser("sample")
    s.add_argument("n", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        return run(a.workers, a.limit)
    return sample(a.n)


if __name__ == "__main__":
    sys.exit(main())
