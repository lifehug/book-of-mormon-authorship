"""The curated pseudo-biblical control (BOM-54; Amendment 6, Change 1).

Amendment 3's either-label rule admits 3,672 volumes that are mostly religious prose *about*
scripture. Amendment 6 replaces it, for the confirmatory test, with a list chosen by this
procedure, fixed before any scoring:

1. ``markers``: for every eligible work (1780-1830, has text, a duplicate keeper, passes the OCR
   cutoff; newspaper pages are not works), simple KJV-style rates on the middle of its
   normalised text: "and it came to pass", -eth/-est verb forms, thee/thou/thy/thine/ye,
   chapter-and-verse numbering, and the share of the text that is verbatim KJV (8-word runs),
   which marks Bibles and scripture paraphrases.
   -> ``data/controls/pseudo_biblical/markers.parquet``
2. ``candidates``: the marker threshold is a selection procedure in Amendment 2's sense, chosen
   on known answers only -- the four works section 3 names (all editions) must clear it -- and
   the pool is every work over it with a KJV share below the cap, plus every work whose primary
   genre label is pseudo-biblical, plus the named works.
3. ``judge``: two models of different families read each candidate's title and passages from its
   beginning, middle and end against a written rule sheet (``RULES``) and answer yes or no with
   a reason; a disagreement goes to a third read that sees both. Simulated (Amendment 1).
4. ``build``: the known-answer gate (every named edition admitted, every work in the rejection
   set refused), then one entry per work (author and first title words; copies and editions
   collapse to the earliest), and the list with its SHA-256.

Usage::

    python -m metadata.pseudo_biblical markers [--workers 8]
    python -m metadata.pseudo_biblical candidates
    python -m metadata.pseudo_biblical judge [--workers 1]
    python -m metadata.pseudo_biblical build
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
VOLUMES = Path("data/ocr_quality/volumes.parquet")
DUPES = Path("data/catalog/duplicates_combined.parquet")
KJV = Path("data/kjv/kjv.jsonl")
OUT = Path("data/controls/pseudo_biblical")
MARKERS = OUT / "markers.parquet"
NOT_WORKS = {"chronicling_america"}
SAMPLE_CHARS = 120_000  # about 20,000 words from the middle of each text
KJV_GRAM = 8

_WORD = re.compile(r"[a-z]+")
_CAME_TO_PASS = re.compile(r"\band it came to pass\b")
_ETH = re.compile(r"\b[a-z]{2,}(?:eth|est)\b")
_THOU = re.compile(r"\b(?:thee|thou|thy|thine|ye)\b")
_VERSE = re.compile(r"(?m)^\s*(?:chap(?:ter)?\.?\s+[ivxlc\d]+|\d{1,3}[.\s]+[A-Z])")
# common words ending in -est/-eth that are not archaic verb forms
_ETH_STOP = {
    "best",
    "rest",
    "west",
    "test",
    "least",
    "most",
    "honest",
    "interest",
    "forest",
    "guest",
    "request",
    "harvest",
    "manifest",
    "modest",
    "earnest",
    "chest",
    "breast",
    "nest",
    "priest",
    "contest",
    "protest",
    "conquest",
    "quest",
    "behest",
    "greatest",
    "teeth",
    "beneath",
    "death",
    "breath",
    "faith",
    "smith",
    "north",
    "south",
    "seth",
    "elizabeth",
    "japheth",
    "nazareth",
    "twentieth",
    "thirtieth",
    "fortieth",
    "fiftieth",
    "sixtieth",
    "seventieth",
    "eightieth",
    "ninetieth",
}


def _kjv_grams() -> set[int]:
    words = []
    for line in KJV.read_text(encoding="utf-8").splitlines():
        words += _WORD.findall(json.loads(line)["text"].lower())
    return {hash(" ".join(words[i : i + KJV_GRAM])) for i in range(len(words) - KJV_GRAM + 1)}


_GRAMS: set[int] | None = None


def score(text: str, grams: set[int]) -> dict:
    """KJV-style marker rates per 1,000 words, and the verbatim-KJV share, of ``text``."""
    low = text.lower()
    words = _WORD.findall(low)
    n = max(1, len(words))
    eth = sum(1 for m in _ETH.finditer(low) if m.group(0) not in _ETH_STOP)
    hits = 0
    for i in range(len(words) - KJV_GRAM + 1):
        if hash(" ".join(words[i : i + KJV_GRAM])) in grams:
            hits += 1
    return {
        "words": len(words),
        "came_to_pass": 1000 * len(_CAME_TO_PASS.findall(low)) / n,
        "eth_est": 1000 * eth / n,
        "thou": 1000 * len(_THOU.findall(low)) / n,
        "verse_marks": 1000 * len(_VERSE.findall(text)) / n,
        "kjv_share": hits / max(1, len(words) - KJV_GRAM + 1),
    }


def _middle(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= SAMPLE_CHARS:
        return text
    mid = len(text) // 2
    return text[mid - SAMPLE_CHARS // 2 : mid + SAMPLE_CHARS // 2]


def _score_one(job: tuple[str, str]) -> dict:
    global _GRAMS
    if _GRAMS is None:
        _GRAMS = _kjv_grams()
    work_id, path = job
    try:
        return {"work_id": work_id, **score(_middle(Path(path)), _GRAMS)}
    except OSError:
        return {
            "work_id": work_id,
            "words": 0,
            "came_to_pass": 0.0,
            "eth_est": 0.0,
            "thou": 0.0,
            "verse_marks": 0.0,
            "kjv_share": 0.0,
        }


def eligible_rows(cfg: dict) -> list[dict]:
    lo, hi = cfg["corpus"]["date_range"]
    excluded = {r["work_id"] for r in pq.read_table(VOLUMES).to_pylist() if r["ocr_excluded"]}
    nonkeeper = {r["work_id"] for r in pq.read_table(DUPES).to_pylist() if not r["is_keeper"]}
    cols = ["work_id", "source", "year", "has_text", "text_path", "title", "author_norm"]
    return [
        r
        for r in pq.read_table(CATALOG, columns=cols).to_pylist()
        if r["has_text"]
        and r["year"]
        and lo <= r["year"] <= hi
        and r["source"] not in NOT_WORKS
        and r["work_id"] not in excluded
        and r["work_id"] not in nonkeeper
    ]


def markers(workers: int) -> int:
    from ocr_fix.normalize import norm_path

    rows = eligible_rows(load_config())
    jobs = [(r["work_id"], str(norm_path(r))) for r in rows]
    print(f"{len(jobs):,} eligible works", flush=True)
    start, out = time.time(), []
    with ProcessPoolExecutor(workers) as pool:
        for i, rec in enumerate(pool.map(_score_one, jobs, chunksize=64), 1):
            out.append(rec)
            if i % 20000 == 0:
                print(f"  {i:,}/{len(jobs):,}  {i / (time.time() - start):.0f}/s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(out).replace_schema_metadata({"config_sha256": sha256_of_config()}),
        MARKERS,
    )
    print(f"scored {len(out):,} in {time.time() - start:.0f}s -> {MARKERS}")
    return 0


CANDIDATES = OUT / "candidates.jsonl"
JUDGMENTS = OUT / "judgments.jsonl"
LIST = Path("data/controls/pseudo_biblical_curated.txt")
MARKER_KEYS = ("came_to_pass", "eth_est", "thou", "verse_marks")
KJV_CAP = 0.30  # mostly verbatim KJV: a Bible or a scripture paraphrase, not an imitation
REJECTION_SERMONS = 20
REJECTION_BIBLES = 5
_SERMONISH = re.compile(r"\b(commentary|exposition|sermon|discourse|lectures?)\b", re.I)
_BIBLE = re.compile(r"\b(bible|testament|scriptures|psalms of david)\b", re.I)

RULES = """You are checking whether a book printed 1780-1830 is a PSEUDO-BIBLICAL text: new writing
deliberately composed in imitation of the King James Bible, presented as a narrative, history,
prophecy or satire of its own.

Answer YES only if the passages show sustained King James diction (thee/thou, -eth verb forms,
"and it came to pass", "behold", "verily") used as the book's own narrative voice, typically
with chapters and numbered verses, telling NEW events or prophecies (for example a war, a
political quarrel or an imagined future told "in the style of the ancient chronicles").

Answer NO for: the Bible itself or any edition, translation, paraphrase or harmony of it;
commentary, exposition or notes on scripture; sermons, lectures or tracts that quote scripture;
hymns and devotional verse; catechisms; ordinary prose that merely quotes the Bible.

Reply with exactly two lines. Line 1: YES or NO. Line 2: one sentence giving the reason."""


def _named_key(title: str) -> str | None:
    from metadata.controls import NAMED

    return next((k for k, pat in NAMED.items() if re.search(pat, title or "", re.I)), None)


def thresholds(marks: dict[str, dict], named: list[str]) -> dict[str, float]:
    """Amendment 6's selection procedure on known answers only: for each marker, the lowest value
    at which it picks out a named edition, counting a marker as picking one out where that
    edition scores at least half its highest value among the named editions."""
    out = {}
    for k in MARKER_KEYS:
        vals = [marks[w][k] for w in named if w in marks]
        top = max(vals) if vals else 0.0
        strong = [v for v in vals if top and v >= top / 2]
        out[k] = min(strong) if strong else float("inf")
    return out


def candidates() -> int:
    cfg = load_config()
    rows = {r["work_id"]: r for r in eligible_rows(cfg)}
    marks = {r["work_id"]: r for r in pq.read_table(MARKERS).to_pylist()}
    genre = {
        r["work_id"]: r["genre"] for r in pq.read_table("data/catalog/genre.parquet").to_pylist()
    }
    # named editions are taken whatever their date or flags, as in BOM-18
    cols = ["work_id", "source", "year", "has_text", "text_path", "title", "author_norm"]
    allrows = {r["work_id"]: r for r in pq.read_table(CATALOG, columns=cols).to_pylist()}
    named = [w for w, r in allrows.items() if r["has_text"] and _named_key(r["title"])]
    from ocr_fix.normalize import norm_path

    for w in named:
        if w not in marks:
            marks[w] = {"work_id": w, **score(_middle(norm_path(allrows[w])), _kjv_grams())}
    th = thresholds(marks, named)
    pool = {}
    for w, m in marks.items():
        if w not in rows:
            continue
        hit = [k for k in MARKER_KEYS if m[k] >= th[k]]
        primary = (genre.get(w) or "").split(",")[0] == "pseudo_biblical"
        if (hit and m["kjv_share"] < KJV_CAP) or primary:
            pool[w] = {"why": hit + (["primary_label"] if primary else [])}
    for w in named:
        pool[w] = {"why": ["named:" + _named_key(allrows[w]["title"])]}
    # the rejection set: works that must be refused, drawn with the root seed
    rng = random.Random(f"{cfg['seed']}:pseudo-biblical-rejection")
    sermons = sorted(
        w
        for w, r in rows.items()
        if _SERMONISH.search(r["title"] or "")
        and (genre.get(w) or "").startswith("sermon_devotional")
        and w not in pool
    )
    bibles = sorted(
        w
        for w, r in rows.items()
        if _BIBLE.search(r["title"] or "") and w in marks and marks[w]["kjv_share"] >= 0.5
    )
    reject = rng.sample(sermons, min(REJECTION_SERMONS, len(sermons))) + rng.sample(
        bibles, min(REJECTION_BIBLES, len(bibles))
    )
    for w in reject:
        pool[w] = {"why": ["rejection_set"]}
    OUT.mkdir(parents=True, exist_ok=True)
    with CANDIDATES.open("w") as fh:
        for w in sorted(pool):
            r = allrows[w]
            fh.write(
                json.dumps(
                    {
                        "work_id": w,
                        "title": r["title"],
                        "author": r["author_norm"],
                        "year": r["year"],
                        "why": pool[w]["why"],
                        "markers": {k: round(marks[w][k], 3) for k in (*MARKER_KEYS, "kjv_share")},
                    }
                )
                + "\n"
            )
    (OUT / "thresholds.json").write_text(
        json.dumps(
            {
                "thresholds": th,
                "kjv_cap": KJV_CAP,
                "named_editions": sorted(named),
                "rejection_set": sorted(reject),
                "config_sha256": sha256_of_config(),
            },
            indent=1,
        )
        + "\n"
    )
    from collections import Counter

    why = Counter(x for v in pool.values() for x in v["why"])
    print(
        f"thresholds {th}; {len(pool):,} candidates ({len(named)} named editions, "
        f"{len(reject)} in the rejection set); by reason {dict(why)}"
    )
    return 0


def passages(text: str, n: int = 3, chars: int = 1200) -> list[str]:
    """``n`` passages spread through the text, skipping the first 5% (title pages, front matter)."""
    start, end = int(len(text) * 0.05), len(text) - chars
    if end <= start:
        return [text[: chars * n]]
    return [text[start + i * (end - start) // max(1, n - 1) :][:chars] for i in range(n)]


def _ask(prompt: str, model: str) -> tuple[str, str]:
    """(YES|NO|RETRY|PARSE_FAIL, reason)."""
    from metadata.genre import _TRANSIENT, _log_parse_failure

    try:
        done = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=180,
            stdin=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        _log_parse_failure(model, f"<{type(exc).__name__}: {exc}>")
        return "RETRY", ""
    text = done.stdout.strip()
    if not text or _TRANSIENT.search(text) or done.returncode != 0:
        _log_parse_failure(model, text or f"<rc={done.returncode}>")
        return "RETRY", ""
    first, _, rest = text.partition("\n")
    verdict = re.sub(r"[^A-Z]", "", first.upper())
    if verdict not in ("YES", "NO"):
        _log_parse_failure(model, text)
        return "PARSE_FAIL", text[:300]
    return verdict, rest.strip()[:400]


def _prompt(c: dict, text: str) -> str:
    body = "\n\n".join(f"Passage {i + 1}:\n{p}" for i, p in enumerate(passages(text)))
    return f"{RULES}\n\nTitle: {c['title']}\nAuthor: {c['author']}\nYear: {c['year']}\n\n{body}"


def judge(workers: int) -> int:
    from concurrent.futures import ThreadPoolExecutor

    from ocr_fix.normalize import norm_path

    cols = ["work_id", "source", "text_path"]
    rows = {r["work_id"]: r for r in pq.read_table(CATALOG, columns=cols).to_pylist()}
    cands = [json.loads(ln) for ln in CANDIDATES.read_text().splitlines()]
    done = {}
    if JUDGMENTS.exists():
        for ln in JUDGMENTS.read_text().splitlines():
            r = json.loads(ln)
            done[r["work_id"]] = r
    todo = [
        c
        for c in cands
        if c["work_id"] not in done or done[c["work_id"]]["final"] in ("RETRY", "PARSE_FAIL")
    ]
    print(f"{len(cands):,} candidates, {len(todo):,} to judge", flush=True)

    def one(c: dict) -> dict:
        text = norm_path(rows[c["work_id"]]).read_text(encoding="utf-8", errors="replace")
        prompt = _prompt(c, text)
        a, ra = _ask(prompt, "sonnet")
        b, rb = _ask(prompt, "opus")
        rec = {
            "work_id": c["work_id"],
            "sonnet": a,
            "sonnet_reason": ra,
            "opus": b,
            "opus_reason": rb,
            "third": None,
            "third_reason": None,
        }
        if "RETRY" in (a, b):
            rec["final"] = "RETRY"
        elif a == b:
            rec["final"] = a
        else:
            third = (
                f"{prompt}\n\nTwo earlier readers disagreed.\nReader 1 said {a}: {ra}\n"
                f"Reader 2 said {b}: {rb}\nGive your own answer in the same two-line form."
            )
            rec["third"], rec["third_reason"] = _ask(third, "opus")
            rec["final"] = rec["third"]
        rec["config_sha256"] = sha256_of_config()
        return rec

    n = 0
    with ThreadPoolExecutor(workers) as pool, JUDGMENTS.open("a") as fh:
        for rec in pool.map(one, todo):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            n += 1
            if n % 25 == 0:
                print(f"  {n:,}/{len(todo):,}", flush=True)
    print(f"judged {n:,}")
    return 0


def build() -> int:
    cands = {
        c["work_id"]: c for c in (json.loads(ln) for ln in CANDIDATES.read_text().splitlines())
    }
    last = {}
    for ln in JUDGMENTS.read_text().splitlines():
        r = json.loads(ln)
        last[r["work_id"]] = r
    pending = [w for w in cands if w not in last or last[w]["final"] in ("RETRY", "PARSE_FAIL")]
    if pending:
        raise SystemExit(f"{len(pending)} candidates not yet judged; run judge again")
    th = json.loads((OUT / "thresholds.json").read_text())
    named = [w for w in th["named_editions"] if w in cands]
    missed = [w for w in named if last[w]["final"] != "YES"]
    wrongly = [w for w in th["rejection_set"] if last[w]["final"] != "NO"]
    gate = {
        "named_admitted": len(named) - len(missed),
        "named": len(named),
        "named_missed": missed,
        "rejection_refused": len(th["rejection_set"]) - len(wrongly),
        "rejection": len(th["rejection_set"]),
        "rejection_admitted": wrongly,
        "passed": not missed and not wrongly,
    }
    yes = [cands[w] for w in cands if last[w]["final"] == "YES" and w not in th["rejection_set"]]
    order = {w: i for i, w in enumerate(sorted(cands))}
    works: dict[str, dict] = {}
    for c in sorted(yes, key=lambda c: (c["year"] or 9999, order[c["work_id"]])):
        key = (
            _named_key(c["title"])
            or f"{c['author'] or ''}|{' '.join((c['title'] or '').lower().split()[:5])}"
        )
        works.setdefault(key, c)
    ids = "".join(c["work_id"] + "\n" for c in sorted(works.values(), key=lambda c: c["work_id"]))
    LIST.write_text(ids)
    summary = {
        "gate": gate,
        "judged": len(cands),
        "yes": len(yes),
        "works": len(works),
        "sha256_of_id_list": hashlib.sha256(ids.encode()).hexdigest(),
        "agreement_sonnet_opus": sum(last[w]["sonnet"] == last[w]["opus"] for w in cands)
        / len(cands),
        "config_sha256": sha256_of_config(),
    }
    (OUT / "build.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0 if gate["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("markers")
    m.add_argument("--workers", type=int, default=8)
    sub.add_parser("candidates")
    j = sub.add_parser("judge")
    j.add_argument("--workers", type=int, default=1)
    sub.add_parser("build")
    a = ap.parse_args(argv)
    if a.cmd == "markers":
        return markers(a.workers)
    if a.cmd == "candidates":
        return candidates()
    if a.cmd == "judge":
        return judge(a.workers)
    if a.cmd == "build":
        return build()
    return 1


if __name__ == "__main__":
    sys.exit(main())
