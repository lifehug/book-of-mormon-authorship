"""Genre pass 2: the Amendment 4 reliability sample (BOM-12).

Amendment 4 (OSF revision 6ad844dc2aba3079ce0da955) replaced Amendment 3's census of second
passes with a stratified sample, and fixed three things this module implements:

* **Size** ``corpus.genre_tagging.reliability_sample`` = 5,000. A census measured per-record
  consistency, which no decision rule reads: every use of genre (5.1 imposter pools, 5.5
  normalization, 6.5 the null) is pool-level.
* **Strata** ``reliability_strata`` = category, source, decade. Source and decade as well as
  category because a failure confined to one source or one period is not category-shaped and
  would survive an aggregate figure. Agreement is reported per stratum, not only overall.
* **A different model family** ``pass2_model_family`` = ``distinct_from_pass1``. At temperature
  zero the same model reproduces itself -- on a re-ask of 20 already-labelled records, 19 came
  back identical -- so self-agreement would measure arithmetic, not reliability.

Pass 1 was llama3.1:8b. Pass 2 is Sonnet, and a cascade follows: where Sonnet and Llama
disagree, Opus adjudicates. That split is deliberate. The registered agreement figure needs one
second model and a third cannot change whether the first two agree, so Opus adds nothing to it;
but on the disagreements it answers what an agreement rate cannot, which is who was right.
Adjudication is reported separately from the reliability figure and may not be folded into it.

Two exclusions from the sample, both for the same reason -- there is nothing to compare:

* rows with no text (they cannot be validated either, and 14.7 hours of pass 1 went on them)
* ``PARSE_FAIL`` rows (no pass-1 label for a second pass to agree or disagree with)

Usage::

    python -m metadata.genre_pass2 run --model sonnet
    python -m metadata.genre_pass2 agreement
    python -m metadata.genre_pass2 adjudicate --model opus
"""

from __future__ import annotations

import argparse
import collections
import math
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from metadata.genre import ask_model, ask_ollama, excerpt_for, prompt_for

CATALOG = Path("data/catalog/catalog.parquet")
PASS1 = Path("data/catalog/genre.parquet")
OUT = Path("data/catalog/genre_pass2.parquet")

SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("pass1", pa.string()),
        ("pass2", pa.string()),
        ("model", pa.string()),
        ("adjudicated", pa.string()),
        ("adjudicator", pa.string()),
        ("stratum_source", pa.string()),
        ("stratum_decade", pa.string()),
        ("stratum_category", pa.string()),
        ("oversampled", pa.bool_()),
    ]
)


def decade(year) -> str:
    return "unknown" if not year else f"{int(year) // 10 * 10}s"


def ambiguous(label: str | None) -> bool:
    """Over-sampled by Amendment 4: uncertain records and the two-label categories."""
    return label == "uncertain" or "," in (label or "")


def _labels(v: str | None) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


def agree(a: str | None, b: str | None) -> bool:
    """Exact set match. Reported, but it is not the headline -- see ``compare``."""
    return set(_labels(a)) == set(_labels(b))


def compare(a: str | None, b: str | None) -> str:
    """One of ``exact``, ``primary``, ``overlap``, ``contradict``.

    The measures are not chosen to flatter the result; they fall out of Amendment 3 Change 1,
    written weeks before any of these numbers existed: *"Analyses needing a single value use the
    primary; genre-matched control sets (BOM-18) match on either."* So there are two registered
    ways a label is consumed, and therefore two agreements that matter.

    ``exact``       the label sets are identical
    ``primary``     the primary labels match but the sets differ -- one model added a second
                    category the other did not. Agrees for every single-value analysis, and
                    agrees for control matching too, since those match on either
    ``overlap``     the sets intersect but the primaries differ. Disagrees for single-value
                    work, agrees for control-set membership
    ``contradict``  no shared label at all. One of the two is wrong, and this is the only
                    measure that is an error rate rather than a difference in specificity
    """
    sa, sb = _labels(a), _labels(b)
    if set(sa) == set(sb):
        return "exact"
    if not (set(sa) & set(sb)):
        return "contradict"
    return "primary" if sa and sb and sa[0] == sb[0] else "overlap"


def build_sample(cfg: dict) -> list[dict]:
    """Draw the stratified reliability sample. Seeded, so it is reproducible."""
    g = cfg["corpus"]["genre_tagging"]
    want = g["reliability_sample"]
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    rows = [
        r
        for r in pq.read_table(PASS1).to_pylist()
        if cat.get(r["work_id"], {}).get("has_text") and r["genre"] != "PARSE_FAIL"
    ]
    rng = random.Random(cfg["seed"])

    over = [r for r in rows if ambiguous(r["genre"])]
    rest = [r for r in rows if not ambiguous(r["genre"])]
    picked = rng.sample(over, min(len(over), want // 3))
    chosen = {r["work_id"] for r in picked}

    # Spread the remainder over source x decade x category cells, smallest cells first, so the
    # published per-stratum table has entries for the rare cells instead of only the big ones.
    cells: dict[tuple, list] = {}
    for r in rest:
        c = cat[r["work_id"]]
        cells.setdefault((c["source"], decade(c["year"]), r["genre"]), []).append(r)

    # Two sweeps. The first gives every cell an equal share, smallest cells first, so rare
    # source/decade/category combinations reach the published table. The second fills whatever
    # the first left short from the largest cells, uncapped -- an earlier version capped the
    # top-up at the same per-cell share and finished 424 records below the registered 5,000.
    remaining = want - len(picked)
    per = max(1, remaining // max(1, len(cells)))
    for order, cap in (
        (sorted(cells, key=lambda k: len(cells[k])), per),
        (sorted(cells, key=lambda k: -len(cells[k])), None),
    ):
        for key in order:
            if remaining <= 0:
                break
            pool = [r for r in cells[key] if r["work_id"] not in chosen]
            take = min(cap, len(pool), remaining) if cap else min(len(pool), remaining)
            for r in rng.sample(pool, take):
                picked.append(r)
                chosen.add(r["work_id"])
            remaining -= take
    if len(picked) < want:
        print(f"warning: sample is {len(picked):,}, short of {want:,}", file=sys.stderr)

    out = []
    for r in picked:
        c = cat[r["work_id"]]
        out.append(
            {
                "work_id": r["work_id"],
                "pass1": r["genre"],
                "pass2": None,
                "model": None,
                "adjudicated": None,
                "adjudicator": None,
                "stratum_source": c["source"],
                "stratum_decade": decade(c["year"]),
                "stratum_category": r["genre"],
                "oversampled": ambiguous(r["genre"]),
            }
        )
    return out


def _needs_work(value: str | None) -> bool:
    """True when a row still needs asking. RETRY is a transient outage, not an answer."""
    return not value or value == "RETRY"


_LAST_COMMIT = [0.0]


def _git_checkpoint(every_seconds: float = 900) -> None:
    """Commit the output periodically so a disk failure cannot cost the whole run.

    Time-based rather than per-checkpoint: pass 1 wrote 141 checkpoints and committing each
    would have buried the history. Failures here are ignored -- a labelling run must not die
    because git is busy.
    """
    now = time.time()
    if now - _LAST_COMMIT[0] < every_seconds:
        return
    _LAST_COMMIT[0] = now
    try:
        subprocess.run(["git", "add", str(OUT)], check=False, capture_output=True, timeout=60)
        subprocess.run(
            ["git", "commit", "-q", "-m", f"BOM-12: pass 2 checkpoint ({OUT.name})"],
            check=False,
            capture_output=True,
            timeout=60,
        )
    except Exception:  # noqa: BLE001
        pass


def _write(rows: list[dict]) -> None:
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    tmp = OUT.with_suffix(".parquet.tmp")
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), tmp)
    tmp.replace(OUT)
    _git_checkpoint()


def _label(
    rows: list[dict],
    field: str,
    who: str,
    model: str,
    workers: int,
    todo: list[dict] | None = None,
) -> int:
    """Fill ``field`` on ``todo`` (default: every empty row), checkpointing every 250.

    ``rows`` is always the complete set and is what gets written. An earlier version let the
    caller pass a subset when ``--limit`` was given, and ``_write`` then persisted only that
    subset -- a 4-row smoke test silently destroyed 4,996 rows of the drawn sample.
    """
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    todo = todo if todo is not None else [r for r in rows if _needs_work(r[field])]
    if not todo:
        print("nothing to do")
        return 0
    print(f"{len(todo):,} to label with {model}")
    ask = ask_ollama if ":" in model else ask_model
    by_id = {r["work_id"]: r for r in rows}
    start = time.time()

    def one(r: dict) -> tuple[str, str]:
        row = cat[r["work_id"]]
        return r["work_id"], ask(prompt_for(row, excerpt_for(row)), model)

    n = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for wid, label in pool.map(one, todo):
            by_id[wid][field] = label
            by_id[wid][who] = model
            n += 1
            if n % 250 == 0:
                _write(rows)
                rate = (time.time() - start) / n
                left = (len(todo) - n) * rate / 60
                print(f"  {n:,}/{len(todo):,}  {rate:.2f}s/item  ~{left:.0f}m left", flush=True)
    _write(rows)
    print(f"labelled {n:,} in {time.time() - start:.0f}s -> {OUT}")
    return 0


def run(model: str, workers: int, limit: int | None, retry_failed: bool = False) -> int:
    cfg = load_config()
    if OUT.exists():
        rows = pq.read_table(OUT).to_pylist()
        done = sum(1 for r in rows if r["pass2"] and not _needs_work(r["pass2"]))
        print(f"resuming: {done:,} of {len(rows):,} done")
    else:
        rows = build_sample(cfg)
        n_over = sum(r["oversampled"] for r in rows)
        print(f"sample of {len(rows):,}, {n_over:,} oversampled (ambiguous or uncertain)")
        _write(rows)
    if retry_failed:
        n = sum(1 for r in rows if r["pass2"] == "PARSE_FAIL")
        for r in rows:
            if r["pass2"] == "PARSE_FAIL":
                r["pass2"] = None
        print(f"retrying {n:,} PARSE_FAIL rows")
    todo = [r for r in rows if _needs_work(r["pass2"])]
    return _label(rows, "pass2", "model", model, workers, todo[:limit] if limit else todo)


def adjudicate(model: str, workers: int, limit: int | None) -> int:
    """Opus on the disagreements only. Reported apart from the reliability figure."""
    rows = pq.read_table(OUT).to_pylist()
    disputed = [r for r in rows if r["pass2"] and not agree(r["pass1"], r["pass2"])]
    print(f"{len(disputed):,} disagreements of {sum(1 for r in rows if r['pass2']):,} labelled")
    return _label(
        rows, "adjudicated", "adjudicator", model, workers, disputed[:limit] if limit else disputed
    )


def _ci(k: int, n: int) -> str:
    if not n:
        return "-"
    p = k / n
    return f"{p:6.1%} +/-{1.96 * math.sqrt(p * (1 - p) / n):.1%}"


def report() -> int:
    """Agreement per registered use, per stratum. Local computation; no model calls."""
    rows = [r for r in pq.read_table(OUT).to_pylist() if r["pass2"] and r["pass2"] != "PARSE_FAIL"]
    if not rows:
        print("nothing labelled yet", file=sys.stderr)
        return 1

    def summarise(b: list[dict]) -> str:
        if not b:
            return "-"
        k = collections.Counter(compare(r["pass1"], r["pass2"]) for r in b)
        n = len(b)
        single = (k["exact"] + k["primary"]) / n  # single-value analyses: primary governs
        either = (k["exact"] + k["primary"] + k["overlap"]) / n  # control sets: either governs
        return f"{single:6.1%} {either:6.1%} {k['exact'] / n:6.1%} {k['contradict'] / n:6.1%}"

    hdr = f"{'':<44}{'n':>6}  {'single':>6} {'either':>6} {'exact':>6} {'CONTRA':>6}"
    print(f"\n{len(rows):,} records compared (PARSE_FAIL excluded)\n")
    print(hdr)
    print(f"{'ALL':<44}{len(rows):>6,}  {summarise(rows)}")
    for dim in ("stratum_source", "stratum_decade", "stratum_category"):
        print(f"\nby {dim.replace('stratum_', '')}:")
        buckets: dict[str, list] = collections.defaultdict(list)
        for r in rows:
            buckets[r[dim]].append(r)
        for key in sorted(buckets, key=lambda k: -len(buckets[k]))[:10]:
            b = buckets[key]
            print(f"  {str(key)[:40]:<42}{len(b):>6,}  {summarise(b)}")
    print("\nby sampling:")
    for name, b in (
        ("oversampled (ambiguous/uncertain)", [r for r in rows if r["oversampled"]]),
        ("ordinary", [r for r in rows if not r["oversampled"]]),
    ):
        print(f"  {name:<42}{len(b):>6,}  {summarise(b)}")
    contra = [r for r in rows if compare(r["pass1"], r["pass2"]) == "contradict"]
    print(f"\ncontradictions: {len(contra):,} -- the only set worth adjudicating")
    for r in contra[:6]:
        print(f"    {r['pass1'][:38]:<40} vs  {r['pass2'][:38]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", default="sonnet")
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--limit", type=int)
    r.add_argument("--retry-failed", action="store_true")
    a = sub.add_parser("adjudicate")
    a.add_argument("--model", default="opus")
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--limit", type=int)
    sub.add_parser("agreement")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        return run(args.model, args.workers, args.limit, args.retry_failed)
    if args.cmd == "adjudicate":
        return adjudicate(args.model, args.workers, args.limit)
    if args.cmd == "agreement":
        return report()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
