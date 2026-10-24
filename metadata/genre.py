"""Genre tagging for the catalog (BOM-12, BOM-18).

Amendment 2 (2026-10-17) registers the method: a fixed eight-label set, assigned by a language
model with its reasoning logged, validated against a hand-labelled sample with the agreement
rate published. This implements that.

Two passes, because half the corpus does not need a model. Rules decide the cases where the
source already tells us what the work is -- every Chronicling America page is a newspaper page,
a title reading "Vol 2 Iss 49" with a full date is a periodical issue -- and a model decides
the rest. The rules are not assumed correct: the validation sample draws from both paths, so
the published agreement rate covers the easy half as well as the hard one.

Model choice was measured, not assumed. On a 60-row stratified sample, against labels made by
hand:

    haiku,  first prompt    65%   invented labels, used "other" as a dustbin
    haiku,  tuned prompt    72%   mechanically clean, still wrong on obvious cases
    sonnet, tuned prompt    87%   0.36s/item at 8 workers

Haiku's remaining errors were substantive rather than mechanical ("Poems" -> sermon_devotional,
"Daily national intelligencer" -> scientific_medical), so the speed was not worth it. Sonnet
labels the 282,566 model-path rows in about 1.2 days.

Running it locally: start the server yourself, not through ``brew services``. Ollama defaults to
``OLLAMA_NUM_PARALLEL=1``, which silently serialises every worker into one slot -- ``--workers 8``
against a default server is eight threads taking turns. Measured on the mini, llama3.1:8b:

    1 slot    1.47s/item     4.8 days
    4 slots   1.28s/item     4.2 days
    8 slots   1.16s/item     3.6 days

The gain is smaller than it looks because prefill dominates: a request is ~520 prompt tokens
against ~7 generated, and 0.73s of a 1.03s request is reading the prompt. Flash attention and a
q8_0 KV cache keep eight slots inside 16 GB. So::

    tmux new -d -s ollama "OLLAMA_NUM_PARALLEL=8 OLLAMA_KEEP_ALIVE=24h \\
        OLLAMA_FLASH_ATTENTION=true OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve"

Usage::

    python -m metadata.genre rules                 # fast pass, writes genre.parquet
    python -m metadata.genre label --limit 500     # model pass over what rules left

``--limit`` takes the first N of the work list, which is catalog order, so a small limit lands
inside one source and often inside one serial. A 64-row check came back 91% two-label and looked
like the model over-applying the comma option; all 64 were consecutive volumes of *The New annual
register*, for which "newspaper_periodical, history_chronicle" is simply correct. Sample across
sources before reading anything into a distribution.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
OUT = Path("data/catalog/genre.parquet")

# The eight labels are registered by Amendment 2; the one-line glosses are what the model sees.
DEFINITIONS = """sermon_devotional - sermons, discourses, theology, scripture, hymns, religion
pseudo_biblical - modern events written in deliberate King James style ("and it came to pass")
history_chronicle - history, biography, memoirs, travel, topography, antiquarian description
fiction_narrative - novels, tales, poetry, drama, songs, belles-lettres
newspaper_periodical - newspapers, magazines, reviews, anything issued in numbered parts
legal_political - laws, proclamations, law reports, political pamphlets, institutional proceedings
scientific_medical - medicine, natural history, technical and practical manuals
other - only if genuinely none of the above fit (catalogues, reference, directories)"""

LABELS = tuple(line.split(" - ")[0] for line in DEFINITIONS.splitlines())

# Amendment 3 (2026-10-20): three worked examples, one deliberately ambiguous. Fixed, published
# with the code, drawn from the comparison corpus only -- never the Book of Mormon or a
# candidate author's writing, which would leak the questioned text into the labeller.
EXAMPLES = """Examples:

TITLE: A discourse delivered before the Society for the Commemoration of the Landing
YEAR: 1825
ANSWER: sermon_devotional

TITLE: Philosophical Transactions of the Royal Society of London
YEAR: 1810
ANSWER: newspaper_periodical, scientific_medical

TITLE: Travels in Africa performed during the years 1785, 1786, and 1787
YEAR: 1802
ANSWER: history_chronicle"""
MODEL = "sonnet"
WORKERS = 8

_ISSUE = re.compile(r"\b(vol|iss|no)\b.*\d", re.I)
_FULLDATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SERMON = re.compile(r"\bsermon|discourse delivered|a sermon\b", re.I)
_LEGAL = re.compile(r"\bproclamation|act of parliament|statutes|reports of cases\b", re.I)


def rule_label(row: dict) -> str | None:
    """A genre the source already tells us, or None if a model is needed.

    Deliberately conservative: it only fires where the evidence is structural (which corpus the
    row came from, an issue number plus a full date) rather than interpretive. Anything needing
    a judgement about content goes to the model.
    """
    source = row["source"]
    title = row.get("title_norm") or ""
    genre_src = (row.get("genre_src") or "").lower()
    if source == "chronicling_america":
        return "newspaper_periodical"
    if _ISSUE.search(title) and _FULLDATE.search(row.get("date_raw") or ""):
        return "newspaper_periodical"
    if "newspaper" in genre_src or "periodical" in genre_src:
        return "newspaper_periodical"
    if _SERMON.search(title):
        return "sermon_devotional"
    if _LEGAL.search(title):
        return "legal_political"
    return None


def prompt_for(row: dict, excerpt: str) -> str:
    """The classification prompt. Multi-label, few-shot, with an uncertainty escape.

    Amendment 3 replaced Amendment 2's single-label scheme after measuring that two model
    families agreed only 72% on hard records, about a third of the disagreements being works
    that genuinely belong to two categories at once. A precedence rule was considered and
    rejected: it resolves ambiguity by discarding half the information, which would empty the
    scientific control pool of every scientific periodical.
    """
    return (
        f"You are classifying a printed work for a corpus study.\n\n"
        f"{DEFINITIONS}\n\n"
        f"{EXAMPLES}\n\n"
        f"Rules: answer with one label, or two separated by a comma when the work genuinely "
        f"belongs to both (most scientific journals are both newspaper_periodical and "
        f"scientific_medical). Put the primary category first. Use lowercase exactly as "
        f"written above, no explanation and no punctuation beyond the comma. Prefer a specific "
        f"category over 'other'. If the evidence genuinely does not support any category, "
        f"answer 'uncertain' rather than guessing.\n\n"
        f"TITLE: {row.get('title')}\nAUTHOR: {row.get('author')}\nYEAR: {row.get('year')}\n"
        f"EXCERPT: {excerpt[:500]}"
    )


def ask_ollama(prompt: str, model: str, retries: int = 2) -> str:
    """Same contract as ask_model, against a local ollama server.

    Used when the subscription models are unavailable. llama3.1:8b measured 97% on the
    ground-truth rows against Sonnet's 98%, at 1.08s/item versus 0.33s -- free and unmetered,
    which is the trade when subscription usage is the binding constraint.
    """
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 24},
        }
    ).encode()
    for _ in range(retries):
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=240) as resp:
                text = json.loads(resp.read()).get("response", "").lower()
        except Exception:  # noqa: BLE001
            continue
        text = re.sub(r"<think>.*?</think>", " ", text, flags=re.S)
        if re.search(r"\buncertain\b", text) and not any(
            re.search(rf"\b{label}\b", text) for label in LABELS
        ):
            return "uncertain"
        found: list[str] = []
        for match in re.finditer(r"\b(" + "|".join(LABELS) + r")\b", text):
            if match.group(1) not in found:
                found.append(match.group(1))
        if found:
            return ",".join(found[:2])
    return "PARSE_FAIL"


def ask_model(prompt: str, model: str = MODEL, retries: int = 2) -> str:
    """One label from the model, or ``PARSE_FAIL``.

    The reply is matched against the closed label set rather than trusted. An early version of
    this returned "poems" and "Wait, the label must be exact: scientific_medical"; constraining
    the parse removed both failure modes without touching the model.
    """
    for _ in range(retries):
        try:
            done = subprocess.run(
                ["claude", "-p", "--model", model, prompt],
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,
            )
        except Exception:  # noqa: BLE001
            continue
        text = done.stdout.strip().lower()
        if re.search(r"\buncertain\b", text) and not any(
            re.search(rf"\b{label}\b", text) for label in LABELS
        ):
            return "uncertain"
        # Keep reading order: the model is told to put the primary category first.
        found: list[str] = []
        for match in re.finditer(r"\b(" + "|".join(LABELS) + r")\b", text):
            if match.group(1) not in found:
                found.append(match.group(1))
        if found:
            return ",".join(found[:2])
    return "PARSE_FAIL"


def excerpt_for(row: dict, chars: int = 500) -> str:
    path = row.get("text_path")
    if not path:
        return ""
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")[:4000]
    except Exception:  # noqa: BLE001
        return ""
    lines = [ln.strip() for ln in raw.splitlines() if len(ln.strip()) > 40]
    return " ".join(lines[:6])[:chars]


SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("genre", pa.string()),  # primary, or "primary,secondary" (Amendment 3)
        ("genre_pass2", pa.string()),  # second pass; agreement is the confidence signal
        ("decided_by", pa.string()),  # "rule" or the model name; both go to validation
        ("model", pa.string()),
    ]
)


def run_rules() -> int:
    rows = pq.read_table(CATALOG).to_pylist()
    out = []
    for row in rows:
        label = rule_label(row)
        if label:
            out.append(
                {"work_id": row["work_id"], "genre": label, "decided_by": "rule", "model": None}
            )
    table = pa.Table.from_pylist(out, schema=SCHEMA)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), OUT)
    print(f"rules decided {len(out):,} of {len(rows):,} ({100 * len(out) / len(rows):.1f}%)")
    print(f"{len(rows) - len(out):,} rows need the model")
    return 0


def run_label(limit: int | None, model: str, workers: int) -> int:
    load_config()  # fail loudly if a registered value has been edited
    rows = pq.read_table(CATALOG).to_pylist()
    done = set()
    existing = []
    if OUT.exists():
        existing = pq.read_table(OUT).to_pylist()
        done = {r["work_id"] for r in existing}
    todo = [r for r in rows if r["work_id"] not in done and rule_label(r) is None]
    if limit:
        todo = todo[:limit]
    print(f"{len(todo):,} to label with {model} at {workers} workers")

    def one(row: dict) -> dict:
        return {
            "work_id": row["work_id"],
            "genre": (ask_ollama if ":" in model else ask_model)(
                prompt_for(row, excerpt_for(row)), model
            ),
            "decided_by": model,
            "model": model,
        }

    # Checkpoint as we go. An earlier version collected everything in memory and wrote once
    # at the end; it ran for four hours, was interrupted, and lost all of it. Every other long
    # job in this project resumes from disk and this one must too.
    start = time.time()
    done_rows: list[dict] = []
    checkpoint_every = 2000

    def flush() -> None:
        table = pa.Table.from_pylist(existing + done_rows, schema=SCHEMA)
        tmp = OUT.with_suffix(".parquet.tmp")
        pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), tmp)
        tmp.replace(OUT)  # atomic: a crash mid-write leaves the previous file intact

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for row in pool.map(one, todo):
            done_rows.append(row)
            if len(done_rows) % checkpoint_every == 0:
                flush()
                rate = (time.time() - start) / len(done_rows)
                left = (len(todo) - len(done_rows)) * rate / 3600
                print(
                    f"  {len(done_rows):,}/{len(todo):,}  {rate:.2f}s/item  ~{left:.1f}h left",
                    flush=True,
                )
    flush()
    elapsed = time.time() - start
    fails = sum(1 for r in done_rows if r["genre"] == "PARSE_FAIL")
    multi = sum(1 for r in done_rows if "," in (r["genre"] or ""))
    unc = sum(1 for r in done_rows if r["genre"] == "uncertain")
    rate = elapsed / len(done_rows) if done_rows else 0
    print(
        f"labelled {len(done_rows):,} in {elapsed:.0f}s ({rate:.2f}s/item); "
        f"{multi:,} two-label, {unc:,} uncertain, {fails:,} parse failures"
    )
    return 0


def resolve_no_text() -> int:
    """Relabel PARSE_FAIL rows that have no text as ``uncertain`` (owner decision 2026-10-24).

    This implements Amendment 3's existing option rather than adding one. The amendment says a
    record may be answered ``uncertain`` when "the evidence genuinely does not support any
    category". A row with no text on disk has no evidence at all: the prompt carries an empty
    excerpt, and the model's reply is not a wrong label but a request for the missing text --
    *"To classify the work, I need to see the excerpt."* That is the ``uncertain`` condition
    holding while the model fails to say the word, so no amendment is needed.

    Rows that **do** have text keep ``PARSE_FAIL``. There the evidence may well support a
    category and the model simply failed to emit one; calling those uncertain would overclaim.
    267 rows are in that state, 0.053% of the corpus that has text, and they are reported rather
    than resolved -- genre is only ever used pool-wise, so at that scale resolving them buys
    nothing (see docs/audit.md finding 1 and BOM-51's perturbation test).
    """
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    rows = pq.read_table(OUT).to_pylist()
    changed = kept = 0
    for r in rows:
        if r["genre"] != "PARSE_FAIL":
            continue
        if cat.get(r["work_id"], {}).get("has_text"):
            kept += 1
        else:
            r["genre"] = "uncertain"
            r["decided_by"] = "rule:no_text"
            changed += 1
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    tmp = OUT.with_suffix(".parquet.tmp")
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), tmp)
    tmp.replace(OUT)
    print(f"relabelled {changed:,} no-text PARSE_FAIL rows to uncertain")
    print(f"kept {kept:,} PARSE_FAIL rows that have text, for reporting")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rules")
    sub.add_parser("resolve-no-text")
    lab = sub.add_parser("label")
    lab.add_argument("--limit", type=int)
    lab.add_argument("--model", default=MODEL)
    lab.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args(argv)
    if args.cmd == "rules":
        return run_rules()
    if args.cmd == "resolve-no-text":
        return resolve_no_text()
    if args.cmd == "label":
        return run_label(args.limit, args.model, args.workers)
    return 1


if __name__ == "__main__":
    sys.exit(main())
