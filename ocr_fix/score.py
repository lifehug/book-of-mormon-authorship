"""OCR quality scoring (BOM-14).

What this does and does not measure. Pre-registration 4.3 excludes volumes whose *character
error rate* exceeds ``corpus.ocr_max_cer`` (0.10), taken "from the source's quality score, or
from our own sample-based estimate where none exists". NYS Historic Newspapers and Advantage
Preservation publish no quality score, and CER cannot be computed without hand-corrected pages,
which BOM-14 still owes. So this module computes a **proxy**, not CER, and nothing here applies
the 0.10 cutoff. Mapping proxy to CER needs the hand-corrected sample; until then a page is
ranked, not excluded.

The proxy is calibrated rather than invented. Chronicling America gives 158,960 pages of
same-era American newspaper OCR from the same kind of microfilm, scored by the same code, so a
new title is judged against what 1820s newspaper OCR actually looks like. Any bias in the
lexicon applies equally to both sides of that comparison, which is why a relative reading is
sound even though the absolute rate is not.

Metrics per page, all on the raw text as delivered:

``lexicon_rate``        alphabetic tokens found in ``data/lexicon/english_words.txt``
``garbage_rate``        tokens that cannot be words: no vowel and longer than two
                        characters, or letters mixed with digits
``single_letter_rate``  lone letters other than a/i/o, counted *separately* and
                        deliberately kept out of ``garbage_rate``
``mean_token_len``      OCR noise shortens tokens; a collapsed column lengthens them
``nonalpha_ratio``      share of non-alphanumeric, non-space characters

Why single letters are their own metric. The first run folded them into ``garbage_rate`` and
made the Wayne Sentinel look six times worse than Chronicling America (0.309 against 0.047),
which would have down-weighted the most important newspaper in the study. Decomposing it
showed 36.3% of Sentinel tokens are lone letters against 4.8% in the reference, while the
genuine garbling signal -- vowelless tokens -- was 0.009 against 0.008, indistinguishable.
NYSHN's Veridian text view fragments words into single characters; that is a property of how
the page is delivered, not of how well it was read. A metric that cannot separate the two will
reject a source for its HTML.

Usage::

    python -m ocr_fix.score run data/newspapers/wayne_sentinel/text --name wayne_sentinel
    python -m ocr_fix.score baseline --sample 5000      # Chronicling America reference
    python -m ocr_fix.score report                      # every scored source side by side
"""

from __future__ import annotations

import argparse
import random
import re
import statistics
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import sha256_of_config

LEXICON = Path("data/lexicon/english_words.txt")
OUT_DIR = Path("data/ocr_quality")
CHRONAM = Path("data/corpus/chronicling_america/text")

# Two tokenizers on purpose. _TOKEN is letters-only and feeds the word metrics; _WIDE keeps
# digits so letter-digit salad ("m0rm0n") can be counted at all. An earlier version used only
# _TOKEN, which split such tokens into letter runs before the mixed-token test ever saw them,
# so that branch was dead and scored 0.000 on every source -- a zero that looked like evidence.
_TOKEN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_WIDE = re.compile(r"[A-Za-z0-9']+")
_ALNUM_MIX = re.compile(r"(?=[A-Za-z0-9']*[A-Za-z])(?=[A-Za-z0-9']*\d)")
_VOWEL = re.compile(r"[aeiouy]")
_WORDISH = re.compile(r"[A-Za-z0-9]")

SCHEMA = pa.schema(
    [
        ("page_id", pa.string()),
        ("source", pa.string()),
        ("chars", pa.int64()),
        ("tokens", pa.int64()),
        ("lexicon_rate", pa.float64()),
        ("garbage_rate", pa.float64()),
        ("single_letter_rate", pa.float64()),
        ("mean_token_len", pa.float64()),
        ("nonalpha_ratio", pa.float64()),
        ("empty", pa.bool_()),
    ]
)


def load_lexicon() -> frozenset[str]:
    """The committed word list, so a score does not depend on the host's dictionary."""
    if not LEXICON.exists():
        raise SystemExit(
            f"{LEXICON} is missing. It is committed; see data/lexicon/SOURCES.md to rebuild."
        )
    return frozenset(LEXICON.read_text(encoding="utf-8").split())


def score_text(text: str, lex: frozenset[str]) -> dict:
    """Proxy metrics for one page. An empty page scores zero and is flagged, not dropped."""
    chars = len(text)
    raw = _TOKEN.findall(text)
    if not raw:
        return {
            "chars": chars,
            "tokens": 0,
            "lexicon_rate": 0.0,
            "garbage_rate": 0.0,
            "single_letter_rate": 0.0,
            "mean_token_len": 0.0,
            "nonalpha_ratio": 0.0,
            "empty": True,
        }
    lower = [t.lower() for t in raw]
    wide = _WIDE.findall(text)
    hits = sum(1 for t in lower if t in lex)
    vowelless = sum(1 for t in lower if len(t) > 2 and not _VOWEL.search(t))
    mixed = sum(1 for t in wide if _ALNUM_MIX.match(t))
    garbage = (vowelless + mixed) / len(wide) if wide else 0.0
    singles = sum(1 for t in lower if len(t) == 1 and t not in {"a", "i", "o"})
    wordish = sum(1 for c in text if _WORDISH.match(c))
    spaces = sum(1 for c in text if c.isspace())
    other = chars - wordish - spaces
    return {
        "chars": chars,
        "tokens": len(raw),
        "lexicon_rate": hits / len(raw),
        "garbage_rate": garbage,
        "single_letter_rate": singles / len(raw),
        "mean_token_len": statistics.fmean(len(t) for t in raw),
        "nonalpha_ratio": other / chars if chars else 0.0,
        "empty": False,
    }


def _iter_texts(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.txt") if p.is_file())


def run(root: Path, name: str, limit: int | None = None) -> int:
    lex = load_lexicon()
    files = _iter_texts(root)
    if limit:
        files = files[:limit]
    if not files:
        print(f"no .txt under {root}", file=sys.stderr)
        return 1
    rows = []
    for i, p in enumerate(files, 1):
        row = score_text(p.read_text(encoding="utf-8", errors="replace"), lex)
        row["page_id"] = p.stem
        row["source"] = name
        rows.append(row)
        if i % 500 == 0:
            print(f"  {i:,}/{len(files):,}", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.parquet"
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), out)
    summarize(name, rows)
    print(f"\nwrote {len(rows):,} rows to {out}")
    return 0


def baseline(sample: int, seed: int = 20261017) -> int:
    """Score a random sample of Chronicling America as the same-era reference."""
    if not CHRONAM.exists():
        print(f"{CHRONAM} not on this machine", file=sys.stderr)
        return 1
    files = _iter_texts(CHRONAM)
    rng = random.Random(seed)
    picked = rng.sample(files, min(sample, len(files)))
    lex = load_lexicon()
    rows = []
    for p in picked:
        row = score_text(p.read_text(encoding="utf-8", errors="replace"), lex)
        row["page_id"] = p.stem
        row["source"] = "chronicling_america"
        rows.append(row)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "chronicling_america.parquet"
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), out)
    summarize(f"chronicling_america (random {len(rows):,} of {len(files):,}, seed {seed})", rows)
    print(f"\nwrote {len(rows):,} rows to {out}")
    return 0


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def summarize(name: str, rows: list[dict]) -> None:
    live = [r for r in rows if not r["empty"]]
    lex = [r["lexicon_rate"] for r in live]
    gar = [r["garbage_rate"] for r in live]
    sgl = [r["single_letter_rate"] for r in live]
    print(f"\n{name}: {len(rows):,} pages, {len(rows) - len(live):,} with no text")
    if not live:
        return
    print(
        f"  lexicon_rate   median {statistics.median(lex):.3f}   "
        f"p10 {_pct(lex, 0.10):.3f}  p90 {_pct(lex, 0.90):.3f}"
    )
    print(
        f"  garbage_rate   median {statistics.median(gar):.3f}   "
        f"p10 {_pct(gar, 0.10):.3f}  p90 {_pct(gar, 0.90):.3f}"
    )
    print(
        f"  single_letters median {statistics.median(sgl):.3f}   "
        f"(delivery artifact, not OCR error -- kept out of garbage_rate)"
    )
    print(f"  mean tokens/page {statistics.fmean(r['tokens'] for r in live):,.0f}")


def report() -> int:
    """Every scored source side by side, so a new title is read against the reference."""
    # only page-score tables; the BOM-14 cleaning and ground-truth tables share the directory
    files = [f for f in sorted(OUT_DIR.glob("*.parquet")) if "empty" in pq.read_schema(f).names]
    if not files:
        print(f"nothing scored yet under {OUT_DIR}", file=sys.stderr)
        return 1
    print(
        f"{'source':<24}{'pages':>9}{'empty':>7}{'lex med':>9}"
        f"{'lex p10':>9}{'garb med':>10}{'1-letter':>10}"
    )
    for f in files:
        rows = pq.read_table(f).to_pylist()
        live = [r for r in rows if not r["empty"]]
        lex = [r["lexicon_rate"] for r in live]
        gar = [r["garbage_rate"] for r in live]
        sgl = [r["single_letter_rate"] for r in live]
        print(
            f"{f.stem:<24}{len(rows):>9,}{len(rows) - len(live):>7,}"
            f"{statistics.median(lex) if live else 0:>9.3f}"
            f"{_pct(lex, 0.10):>9.3f}{statistics.median(gar) if live else 0:>10.3f}"
            f"{statistics.median(sgl) if live else 0:>10.3f}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("root", type=Path)
    r.add_argument("--name", required=True)
    r.add_argument("--limit", type=int)
    b = sub.add_parser("baseline")
    b.add_argument("--sample", type=int, default=5000)
    sub.add_parser("report")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        return run(a.root, a.name, a.limit)
    if a.cmd == "baseline":
        return baseline(a.sample)
    if a.cmd == "report":
        return report()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
