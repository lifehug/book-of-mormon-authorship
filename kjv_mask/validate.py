"""The registered check of the frozen passim settings: 200 alignments, checked (BOM-16).

Amendment 2: the alignment parameters "are validated against a hand-checked sample of 200
alignments and frozen before any Book of Mormon text is masked". Under Amendment 1 a step that
assumed a second person is done by an AI model and labelled as such, so the check here is a
**simulated hand check**: an AI reviewer reads each span beside the KJV chapter it was aligned
to and says whether the span really is drawn from that chapter, and whether its edges are right.

The sample is drawn from real control text, not the Book of Mormon: TCP Evans texts labelled
``sermon_devotional``, where scripture use is natural and unplanted. ``N_PER_CLASS`` verbatim and
as many paraphrase spans are drawn, seeded.

**Pass criterion, fixed before the sample was drawn:** at least ``PASS_PRECISION`` of the 200
spans judged genuinely KJV-derived (verbatim or paraphrase). A failure means the registered
procedure has proved unworkable, which Amendment 2 says is a further dated amendment: the
owner's, not this script's.

Usage::

    python -m kjv_mask.validate run [--model opus]
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import kjv_chapters, mask, registered_params
from metadata.config import load as load_config
from metadata.config import sha256_of_config
from metadata.genre import _TRANSIENT

OUT = Path("data/kjv_mask/validation_200.jsonl")
WORK = Path("data/corpus/kjv_mask_validate")
N_DOCS = 120
DOC_WORDS = 6000
N_PER_CLASS = 100
PASS_PRECISION = 0.90
CONTEXT = 120
REVIEW_KIND = "simulated (AI reviewer standing in for a hand check, Amendment 1)"

PROMPT = """You are checking an automatic detector of King James Bible quotation in an \
eighteenth-century American text. This review is simulated: you stand in for a human checker.

The detector says the passage between >>> and <<< is a {kind} of {ref} (KJV). \
"verbatim" means near word-for-word; "paraphrase" means clearly reworded from it.

TEXT (with context):
{before}>>>{span}<<<{after}

KJV {ref}:
{chapter}

Answer with one JSON object and nothing else:
{{"derived": "verbatim" | "paraphrase" | "not_kjv", "edges": "good" | "too_long" | "too_short", \
"note": "<at most 15 words>"}}
"derived" is your own judgement of the marked passage against this chapter. "edges" says \
whether the marked passage starts and ends where the borrowing does."""


def _docs(cfg: dict) -> list[dict]:
    rng = random.Random(f"{cfg['seed']}:kjv_validate")
    genre = {
        r["work_id"]: r["genre"]
        for r in pq.read_table(
            "data/catalog/genre.parquet", columns=["work_id", "genre"]
        ).to_pylist()
        if r["work_id"].startswith("tcp:")
    }
    cat = pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "genre_src", "text_path"]
    ).to_pylist()
    paths = sorted(
        r["text_path"]
        for r in cat
        if r["genre_src"] == "evans"
        and r["text_path"]
        and (genre.get(r["work_id"]) or "").split(",")[0] == "sermon_devotional"
    )
    rng.shuffle(paths)
    docs = []
    for p in paths:
        words = Path(p).read_text(encoding="utf-8", errors="replace").split()
        if len(words) < DOC_WORDS:
            continue
        start = rng.randrange(0, len(words) - DOC_WORDS + 1)
        docs.append({"id": f"val:{len(docs)}", "source": p,
                     "text": " ".join(words[start : start + DOC_WORDS])})  # fmt: skip
        if len(docs) >= N_DOCS:
            break
    return docs


def _ask(prompt: str, model: str) -> dict | None:
    try:
        done = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True, text=True, timeout=240, stdin=subprocess.DEVNULL,
        )  # fmt: skip
    except Exception:  # noqa: BLE001
        return None
    text = done.stdout.strip()
    if done.returncode != 0 or not text or _TRANSIENT.search(text.lower()):
        return None
    try:
        return json.loads(text[text.index("{") : text.rindex("}") + 1])
    except ValueError:
        return {"derived": "PARSE_FAIL", "edges": "PARSE_FAIL", "note": text[:200]}


def run(model: str, workers: int) -> int:
    cfg = load_config()
    params = registered_params()
    if params["min_match"] is None:
        raise SystemExit("kjv_mask.passim.min_match is not chosen yet (kjv_mask.evaluate grid)")
    docs = _docs(cfg)
    spans = mask(docs, WORK, params)
    texts = {d["id"]: d for d in docs}
    pool = {"verbatim": [], "paraphrase": []}
    for doc, ss in spans.items():
        for s in ss:
            pool[s.kind].append((doc, s))
    rng = random.Random(f"{cfg['seed']}:kjv_validate_sample")
    sample = []
    for items in pool.values():
        items.sort(key=lambda x: (x[0], x[1].start))
        sample += rng.sample(items, min(N_PER_CLASS, len(items)))
    print(f"spans found: { {k: len(v) for k, v in pool.items()} }; sampled {len(sample)}")
    chapters = {c["id"]: c["text"] for c in kjv_chapters()}
    done = {}
    if OUT.exists():
        for ln in OUT.read_text().splitlines():
            r = json.loads(ln)
            if r.get("review") and r["review"].get("derived") not in (None, "PARSE_FAIL"):
                done[(r["doc"], r["start"])] = r

    def one(item: tuple) -> dict:
        doc, s = item
        if (doc, s.start) in done:
            return done[(doc, s.start)]
        t = texts[doc]["text"]
        rec = {"doc": doc, "source": texts[doc]["source"], **s.__dict__,
               "span": t[s.start : s.end], "before": t[max(0, s.start - CONTEXT) : s.start],
               "after": t[s.end : s.end + CONTEXT], "reviewer": model,
               "review_kind": REVIEW_KIND}  # fmt: skip
        rec["review"] = _ask(
            PROMPT.format(kind=s.kind, ref=s.ref.removeprefix("kjv:"), before=rec["before"],
                          span=rec["span"], after=rec["after"], chapter=chapters[s.ref]),
            model,
        )  # fmt: skip
        return rec

    with ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(one, sample))
    stamp = sha256_of_config()
    OUT.write_text("".join(json.dumps({**r, "config_sha256": stamp}) + "\n" for r in rows))
    return report()


def report() -> int:
    rows = [json.loads(ln) for ln in OUT.read_text().splitlines()]
    ok = [r for r in rows if r.get("review") and r["review"].get("derived") != "PARSE_FAIL"]
    if len(ok) < len(rows):
        print(f"{len(rows) - len(ok)} reviews missing or unparsed; rerun to retry them")
    derived = sum(1 for r in ok if r["review"]["derived"] in ("verbatim", "paraphrase"))
    print(f"simulated hand check: {derived}/{len(ok)} judged KJV-derived "
          f"({derived / max(1, len(ok)):.1%}); pass criterion {PASS_PRECISION:.0%}")  # fmt: skip
    for kind in ("verbatim", "paraphrase"):
        sub = [r for r in ok if r["kind"] == kind]
        if not sub:
            continue
        d = sum(1 for r in sub if r["review"]["derived"] in ("verbatim", "paraphrase"))
        same = sum(1 for r in sub if r["review"]["derived"] == kind)
        edges = sum(1 for r in sub if r["review"]["edges"] == "good")
        print(f"  {kind:<10} n={len(sub)}  derived {d / len(sub):.1%}  same class "
              f"{same / len(sub):.1%}  edges good {edges / len(sub):.1%}")  # fmt: skip
    passed = len(ok) == len(rows) and derived / max(1, len(ok)) >= PASS_PRECISION
    print("PASS" if passed else "NOT PASSED (or incomplete)")
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--model", default="opus")
    r.add_argument("--workers", type=int, default=4)
    sub.add_parser("report")
    a = ap.parse_args(argv)
    return run(a.model, a.workers) if a.cmd == "run" else report()


if __name__ == "__main__":
    sys.exit(main())
