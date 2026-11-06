"""Triage of the parallels into biblical, common and specific (BOM-26; Amendment 27,
``docs/triage-plan.md``).

``items`` builds the registered selection of hits from the paraphrase search (named sources' stored
strongest pairs; the 20 leading sources' strongest parallels; a seeded random sample of all
non-Bible parallels) and the rare-phrase search (named sources' shared rare 4-grams; up to 10
phrases from each of the 20 highest-density volumes), each as a pair of passages. ``first`` asks
the hosted model to label each pair; ``second`` asks a different model, blind to the first label,
to label every first-pass SPECIFIC and a seeded 10% of the rest (the simulated review of section 9);
``report`` gives counts, Cohen's kappa and the pairs both passes call SPECIFIC.

The pairs and replies are corpus text and stay in ``data/corpus/semantic/triage/``; the report
holds ids, labels and counts only.

Usage::

    python -m semantic.triage first [--workers 2 --per-hour 500]
    python -m semantic.triage second [--workers 2 --per-hour 500]
    python -m semantic.triage report   # -> data/semantic/triage.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from semantic import skeleton as sk

WORK = Path("data/corpus/semantic/triage")
OUT = Path("data/semantic/triage.json")
FIRST_MODEL, SECOND_MODEL = "claude-sonnet-5-5", "claude-opus-5-5"
N_NAMED, N_TOP, N_RANDOM, N_PHRASES, CONTEXT = 50, 25, 250, 10, 40
SECOND_SHARE = 0.10
LABELS = ("BIBLICAL", "COMMON", "SPECIFIC")

PROMPT = """Two passages follow. Passage A is from the Book of Mormon (1830). Passage B is from \
"{title}" ({year}). A search flagged them as similar. Decide what best explains the similarity:

BIBLICAL - both draw on King James Bible wording or a biblical story or idea.
COMMON - stock phrasing or ideas common in writing of that period and kind (sermons, histories, \
travel accounts), which many authors would share.
SPECIFIC - a particular shared detail, idea or wording that neither the Bible nor common phrasing \
explains, suggesting a connection between these two texts.

Reply with exactly two lines:
LABEL: BIBLICAL or COMMON or SPECIFIC
REASON: one sentence

Passage A:
{a}

Passage B:
{b}"""


def _bom_words() -> list[str]:
    return [w for q in __import__("semantic.search", fromlist=["x"]).bom_queries(10**9)
            for w in q["text"].split()]  # fmt: skip


def _context(words: list[str], gram: str, n: int) -> str | None:
    g = gram.split()
    low = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
    for i in range(len(low) - len(g) + 1):
        if low[i : i + len(g)] == g:
            return " ".join(words[max(0, i - n) : i + len(g) + n])
    return None


def items(cfg: dict) -> list[dict]:
    """The registered selection, each with both passages' text (private)."""
    import pyarrow.parquet as pq

    from ocr_fix.normalize import norm_path
    from reuse.exact import BIBLE
    from segment.build import original_words
    from semantic.search import CANDIDATES, NAMED, NAPOLEON, bom_queries, text_passages

    cat = {r["work_id"]: r for r in pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path", "title", "year"]
    ).to_pylist()}  # fmt: skip
    queries = bom_queries(cfg["semantic"]["passage_words"])
    texts: dict[str, str] = {}

    def text_of(key: str) -> str:
        if key not in texts:
            p = CANDIDATES / NAMED[key][1] if key in NAMED else Path(norm_path(cat[key]))
            texts[key] = p.read_text(encoding="utf-8", errors="replace")
        return texts[key]

    out: list[dict] = []
    named = json.loads(Path("data/semantic/named.json").read_text())
    for group in named["groups"].values():
        for row in group["ranking"]:
            if row["id"] not in [*NAMED, NAPOLEON]:
                continue
            ps = text_passages(text_of(row["id"]), cfg)
            title = (cat.get(row["id"]) or {}).get("title") or row["title"]
            for p in row["pairs"][:N_NAMED]:
                out.append({"id": f"named:{row['id']}:{p['query']}:{p['passage']}",
                            "search": "semantic_named", "source": row["id"], "title": title,
                            "year": (cat.get(row["id"]) or {}).get("year"),
                            "a": queries[p["query"]]["text"], "b": ps[p["passage"]]})  # fmt: skip
    par = pq.read_table("data/semantic/parallels_bom.parquet").to_pylist()
    top = json.loads(Path("data/semantic/corpus_bom.json").read_text())["top_search_sources"]
    by_src: dict[str, list] = {}
    for r in par:
        by_src.setdefault(r["work_id"], []).append(r)

    def add(r: dict, search: str) -> None:
        w = r["work_id"]
        out.append({"id": f"{search}:{w}:{r['query']}:{r['passage']}", "search": search,
                    "source": w, "title": cat[w]["title"], "year": cat[w]["year"],
                    "a": queries[r["query"]]["text"],
                    "b": " ".join(text_of(w)[r["char_begin"] : r["char_end"]].split()),
                    })  # fmt: skip

    for w in top:
        for r in sorted(by_src.get(w, []), key=lambda r: r["bar"] - r["score"])[:N_TOP]:
            add(r, "semantic_top")
    rng = random.Random(derive_seed("bom26-sample", cfg))
    pool = [
        r for r in par if r["work_id"] in cat and not BIBLE.search(cat[r["work_id"]]["title"] or "")
    ]
    for r in rng.sample(pool, N_RANDOM):
        add(r, "semantic_random")
    rare = json.loads(Path("data/reuse/bom/rare.json").read_text())
    bom = _bom_words()
    for key, row in rare["named"].items():
        if key == "luke_kjv":
            continue
        for g in row["phrases"]:
            out.append({"search": "rare_named", "source": row.get("work_id") or key, "gram": g,
                        "key": key})  # fmt: skip
    for row in rare["top"][:20]:
        ph = row["phrases"]
        for g in sorted(rng.sample(ph, min(N_PHRASES, len(ph)))):
            out.append({"search": "rare_top", "source": row["work_id"], "gram": g})
    for it in out:
        if "gram" in it:
            w = it["source"]
            if w in cat:
                raw = text_of(w)
            else:  # a named source with no catalog copy: its candidate file
                raw = (CANDIDATES / NAMED[w][1]).read_text(encoding="utf-8", errors="replace")
            c = cat.get(w) or {}
            it.update({"id": f"{it['search']}:{w}:{it['gram']}",
                       "title": c.get("title"), "year": c.get("year"),
                       "a": _context(bom, it["gram"], CONTEXT),
                       "b": _context(original_words(raw, []), it["gram"], CONTEXT)})  # fmt: skip
    return [it for it in out if it["a"] and it["b"]]


def parse(reply: str) -> tuple[str, str] | None:
    m = re.search(r"LABEL:\s*(BIBLICAL|COMMON|SPECIFIC)", reply, re.I)
    r = re.search(r"REASON:\s*(.+)", reply)
    return (m.group(1).upper(), r.group(1).strip() if r else "") if m else None


def _run(todo: list[dict], model: str, path: Path, workers: int) -> int:
    done = (
        {json.loads(ln)["id"] for ln in path.read_text().splitlines()} if path.exists() else set()
    )
    todo = [it for it in todo if it["id"] not in done]
    lock = threading.Lock()
    print(f"{len(todo):,} to label with {model} ({len(done):,} done)", flush=True)

    def one(it: dict) -> None:
        reply = sk._claude(PROMPT.format(title=it["title"], year=it["year"], a=it["a"], b=it["b"]),
                           model)  # fmt: skip
        got = parse(reply) if reply else None
        if got is None:  # transient or unparsed: not recorded; a rerun picks it up
            return
        with lock, path.open("a") as f:
            f.write(json.dumps({"id": it["id"], "label": got[0], "reason": got[1],
                                "model": model}) + "\n")  # fmt: skip

    with ThreadPoolExecutor(workers) as ex:
        for k, _ in enumerate(ex.map(one, todo), 1):
            if k % 50 == 0:
                print(f"  {k:,}/{len(todo):,}", flush=True)
    return 0


def _items(cfg: dict) -> list[dict]:
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / "items.jsonl"
    if not path.exists():
        path.write_text("".join(json.dumps(it) + "\n" for it in items(cfg)))
    return [json.loads(ln) for ln in path.read_text().splitlines()]


def _labels(name: str) -> dict[str, dict]:
    p = WORK / f"{name}.jsonl"
    return (
        {(r := json.loads(ln))["id"]: r for ln in p.read_text().splitlines()} if p.exists() else {}
    )


def first(workers: int) -> int:
    return _run(_items(load_config()), FIRST_MODEL, WORK / "first.jsonl", workers)


def second(workers: int) -> int:
    cfg = load_config()
    its = _items(cfg)
    f1 = _labels("first")
    rng = random.Random(derive_seed("bom26-second", cfg))
    pick = [it for it in its if it["id"] in f1 and (f1[it["id"]]["label"] == "SPECIFIC"
                                                   or rng.random() < SECOND_SHARE)]  # fmt: skip
    return _run(pick, SECOND_MODEL, WORK / "second.jsonl", workers)


def report() -> int:
    its = {it["id"]: it for it in _items(load_config())}
    f1, f2 = _labels("first"), _labels("second")
    by = Counter((its[i]["search"], r["label"]) for i, r in f1.items())
    both = [i for i in f2 if i in f1]
    agree = sum(f1[i]["label"] == f2[i]["label"] for i in both)
    po = agree / len(both) if both else None
    p1, p2 = Counter(f1[i]["label"] for i in both), Counter(f2[i]["label"] for i in both)
    pe = sum(p1[k] * p2[k] for k in LABELS) / len(both) ** 2 if both else None
    kappa = (po - pe) / (1 - pe) if both and pe < 1 else None
    specific = sorted(i for i in both if f1[i]["label"] == f2[i]["label"] == "SPECIFIC")
    doc = {**stamp(), "items": len(its), "first_labelled": len(f1), "second_labelled": len(both),
           "first_by_search": {f"{s}|{lab}": n for (s, lab), n in sorted(by.items())},
           "confusion": {f"{a}|{b}": n for (a, b), n in sorted(
               Counter((f1[i]["label"], f2[i]["label"]) for i in both).items())},
           "agreement": po, "kappa": kappa,
           "specific_both": [{"id": i, "search": its[i]["search"], "source": its[i]["source"],
                              "title": (its[i]["title"] or "")[:100]}
                             for i in specific]}  # fmt: skip
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(
        json.dumps({k: v for k, v in doc.items() if k not in ("specific_both",)}, indent=1)[:1500]
    )
    print(f"-> {OUT}; {len(specific)} pairs SPECIFIC in both passes")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["first", "second", "report"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--per-hour", type=float, default=500)
    a = ap.parse_args(argv)
    sk._PACE["per_hour"] = a.per_hour
    return {"first": lambda: first(a.workers), "second": lambda: second(a.workers),
            "report": report}[a.cmd]()  # fmt: skip


if __name__ == "__main__":
    sys.exit(main())
