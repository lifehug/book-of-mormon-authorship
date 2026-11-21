"""BOM-118 pilot: ten "archaic" word uses and phrases, searched in the library and judged by sense.

Skousen (2018) lists word uses and phrases in the Book of Mormon said to have left English before
the mid-1700s. This pilot takes ten of them by a fixed rule (``lab.archaic.items``), finds each
item's pattern in a fixed sample of library works per decade 1740-1830 (raw hit counts need no
model), and asks a hosted model, through ``lab.judge``, which sense each sampled passage uses: A
(the claimed sense), B (another) or U (cannot tell), and whether it reads as a quotation or reprint
of an older text (Q) or the writer's own words (O). Every such answer is **simulated judging by
an AI model**. A known-answer check is judged first and alone (the verses Skousen cites, early
EEBO-TCP passages, and plainly ordinary uses chosen by hand); the library passages are written
out only if it passes. The test card is
``data/private/lab/owner/2026-11-20-archaic-vocabulary-pilot/card.md``. Passages, prompts and
replies quote text and stay in that private folder; the public result holds ids and counts.

Usage::

    python -m lab.archaic search       # sample, count hits, cut passages (private) and counts
    python -m lab.archaic candidates   # hits 1800-1830, to choose ordinary uses by hand
    python -m lab.archaic check-jobs   # known-answer questions (needs ordinary.json)
    python -m lab.archaic check        # the known-answer result, once answers_check.jsonl is full
    python -m lab.archaic check-jobs --attempt 2   # second attempt: whole paragraphs, no Q/O
    python -m lab.archaic check --attempt 2        # its result (answers_check2.jsonl)
    python -m lab.archaic frames       # redesign: hits of each cited-verse frame (no model)
    python -m lab.archaic jobs         # library + control questions, only if the check passed
    python -m lab.archaic score        # -> data/lab/reruns/archaic_vocabulary/pilot.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.compute as pc

from lab import door, registry
from lab.paths import LOGS, REGISTRY, out
from metadata import config

PRIVATE = Path("data/private/lab/owner/2026-11-20-archaic-vocabulary-pilot")
PUBLIC = REGISTRY / "reruns" / "archaic_vocabulary"
ITEMS = PUBLIC / "items_skousen2018_article.json"
EDITION = Path("data/bom/1830/edition_1830.jsonl")

# Where each cited verse sits in the 1830 text: (book, a few words of the verse as printed in 1830).
# The 1830 printing has no verse numbers; Skousen's references are to the modern verses.
CITED = {
    "break": ("Ether", "could break them"),
    "mar": ("Ether", "could mar them"),
    "belove": ("Alma", "so dearly beloved,"),
    "counsel": ("Alma", "counsel the Lord in all"),
    "desirous": ("1 Nephi", "desirous above all"),
    "about_to": ("Helaman", "about to flatter away"),
    "arrive_to": ("Mosiah", "arrived to the land of Zarahemla"),
    "be_aware": ("Mormon", "be aware lest"),
    "begin_to": ("Alma", "began to the creation"),
    "belief_on": ("Mosiah", "belief on the words of Alma"),
}

PROMPT = """You are helping a study of how English words were used in the past. Below is a short \
passage from a printed text (spelling may be old, and there may be scanning errors). The \
expression marked [[like this]] is a use of "{form}".

Sense A: {a}.
Sense B: {b}.

Question 1. In this passage, is the marked expression used in sense A or in sense B? Answer U if \
the passage does not let you tell.
Question 2. Does the passage look like a quotation or reprint of a much older text (answer Q), or \
like the writer's own words (answer O)?

Passage:
{passage}

Reply with one line and nothing else, in this form: SENSE=<A, B or U> SOURCE=<Q or O>"""

# Second attempt at the check (made after the first missed its bar; see the card): the whole
# paragraph, a stronger model, and no quotation question.
PROMPT2 = """You are helping a study of how English words were used in the past. Below is a \
passage from a printed text (spelling may be old, and there may be scanning errors). The \
expression marked [[like this]] is a use of "{form}".

Sense A: {a}.
Sense B: {b}.

Question. In this passage, is the marked expression used in sense A or in sense B? Answer U if \
the passage does not let you tell.

Passage:
{passage}

Reply with one line and nothing else, in this form: SENSE=<A, B or U>"""

REPLY2 = re.compile(r"\s*SENSE\s*=\s*([ABU])\s*\.?\s*")
REPLY = re.compile(r"\s*SENSE\s*=\s*([ABU])\s+SOURCE\s*=\s*([QO])\s*\.?\s*")


def items(cfg: dict) -> dict[str, dict]:
    """The pilot's items: name -> index, patterns, senses and the form shown to the judge."""
    listed = json.loads(ITEMS.read_text())["items"]
    res = {}
    for name, (idx, pat, broad, a, b) in cfg["lab"]["archaic"]["items"].items():
        res[name] = {
            "index": idx,
            "item": listed[idx]["item"],
            "reference": listed[idx]["reference"],
            "pattern": re.compile(pat, re.I),
            "broad": re.compile(broad, re.I),
            "a": a,
            "b": b,
        }
    return res


def window(text: str, start: int, end: int, words: int) -> str:
    """About ``words`` words around text[start:end], the hit marked [[ ]]."""
    half = words // 2
    left = text[max(0, start - 12 * half) : start].split()[-half:]
    right = text[end : end + 12 * half].split()[:half]
    hit = " ".join(text[start:end].split())
    return " ".join([*left, f"[[{hit}]]", *right])


def parse(reply: str, attempt: int = 1) -> tuple[str, str] | None:
    """(sense, source) from a reply; source is "-" in the second attempt, which does not ask it."""
    if attempt == 2:
        m = REPLY2.fullmatch(reply)
        return (m.group(1), "-") if m else None
    m = REPLY.fullmatch(reply)
    return (m.group(1), m.group(2)) if m else None


def marked(text: str, start: int, end: int) -> str:
    """The whole text with text[start:end] marked [[ ]], whitespace collapsed."""
    return " ".join(f"{text[:start]}[[{text[start:end]}]]{text[end:]}".split())


def decade(year: int, cfg: dict) -> int:
    """The decade a year falls in; the last year (1830) counts with the decade before it."""
    last = ((cfg["lab"]["archaic"]["year_max"] - 1) // 10) * 10
    return min((year // 10) * 10, last)


def _eligible() -> list[dict]:
    t = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(t["kind"], "work"), pc.equal(t["has_text"], True)),
        pc.equal(t["dup_keeper"], True),
    )
    return [
        r
        for r in t.filter(keep).to_pylist()
        if not r["sealed"] and not r["ocr_excluded"] and r["year"]
    ]


def _with_text(rows: list[dict]) -> list[dict]:
    cat = door.catalog({r["work_id"] for r in rows})
    return [{**cat[r["work_id"]], **r} for r in rows if cat.get(r["work_id"], {}).get("text_path")]


def samples(cfg: dict) -> dict[str, list[dict]]:
    """The fixed library sample by decade, the early sample and the control books."""
    a = cfg["lab"]["archaic"]
    controls = [json.loads(x) for x in Path(a["controls"]).read_text().splitlines() if x.strip()]
    ctl_ids = {c["work_id"] for c in controls}
    rows = _eligible()
    by: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        if a["year_min"] <= r["year"] <= a["year_max"] and r["work_id"] not in ctl_ids:
            by[decade(r["year"], cfg)].append(r)
    res = {}
    for d in sorted(by):
        pool = _with_text(sorted(by[d], key=lambda r: r["work_id"]))
        res[f"lib:{d}"] = random.Random(f"{a['seed']}:{d}").sample(
            pool, min(a["per_decade"], len(pool))
        )
    early = _with_text(
        sorted(
            (r for r in rows if r["source"] == "tcp" and r["year"] <= a["early_year_max"]),
            key=lambda r: r["work_id"],
        )
    )
    res["early"] = random.Random(f"{a['seed']}:early").sample(
        early, min(a["early_sample"], len(early))
    )
    reg = {r["work_id"]: r for r in registry.load().to_pylist() if r["work_id"] in ctl_ids}
    res["ctl"] = _with_text(
        [
            {**reg[c["work_id"]], **c}
            for c in controls
            if c["work_id"] in reg and reg[c["work_id"]]["has_text"]
        ]
    )
    return res


def _scan(job: tuple[dict, dict, int, int]) -> dict:
    """Per item: hit counts (narrow, broad) and one hit's window each, chosen with the seed."""
    row, pats, seed, words = job
    try:
        text = door.text_of(row)
    except OSError:
        return {"work_id": row["work_id"], "unreadable": True}
    res = {"work_id": row["work_id"], "year": row["year"], "items": {}}
    for name, (pat, broad) in pats.items():
        rec = {}
        for kind, p in (("narrow", pat), ("broad", broad)):
            hits = [(m.start(), m.end()) for m in re.finditer(p, text, flags=re.I)]
            if hits:
                s, e = random.Random(f"{seed}:{name}:{kind}:{row['work_id']}").choice(hits)
                rec[kind] = {"n": len(hits), "at": s, "passage": window(text, s, e, words)}
        if rec:
            res["items"][name] = rec
    return res


def search(cfg: dict) -> dict:
    a = cfg["lab"]["archaic"]
    its = items(cfg)
    pats = {n: (i["pattern"].pattern, i["broad"].pattern) for n, i in its.items()}
    groups = samples(cfg)
    jobs = [(r, pats, a["seed"], a["window_words"]) for rows in groups.values() for r in rows]
    t0 = time.time()
    with ProcessPoolExecutor(cfg["lab"]["phrase_workers"]) as pool:
        scans = {s["work_id"]: s for s in pool.map(_scan, jobs, chunksize=16)}
    found = []
    for g, rows in groups.items():
        for r in rows:
            s = scans[r["work_id"]]
            found.append(
                {
                    "group": g,
                    "work_id": r["work_id"],
                    "year": r["year"],
                    "source": r["source"],
                    "named": r.get("named"),
                    "unreadable": s.get("unreadable", False),
                    "items": s.get("items", {}),
                }
            )
    path = out(PRIVATE / "scan.jsonl")
    path.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in found))
    print(f"{len(found):,} works scanned in {time.time() - t0:.0f} s -> {path}")
    return {g: len(rows) for g, rows in groups.items()}


def _scan_rows() -> list[dict]:
    return [json.loads(x) for x in (PRIVATE / "scan.jsonl").read_text().splitlines() if x]


def _job(jid: str, it: dict, passage: str) -> dict:
    return {
        "id": jid,
        "prompt": PROMPT.format(form=it["item"].lower(), a=it["a"], b=it["b"], passage=passage),
    }


def cited(cfg: dict) -> dict[str, str]:
    """The window around each item's pattern in its cited 1830 verse (nearest the anchor)."""
    words = cfg["lab"]["archaic"]["window_words"]
    paras = [json.loads(x) for x in EDITION.read_text().splitlines() if x.strip()]
    res = {}
    for name, it in items(cfg).items():
        book, anchor = CITED[name]
        # Any kind: Mormon 8:17 sits in a row the 1830 table labels "synopsis".
        for p in paras:
            at = p["text"].find(anchor) if p["book"] == book else -1
            if at < 0:
                continue
            ms = list(it["pattern"].finditer(p["text"]))
            if ms:
                m = min(ms, key=lambda m: abs(m.start() - at))
                res[name] = window(p["text"], m.start(), m.end(), words)
            break
    return res


def check_jobs(cfg: dict) -> int:
    a = cfg["lab"]["archaic"]
    its = items(cfg)
    jobs = [_job(f"cited:{n}", its[n], p) for n, p in cited(cfg).items()]
    scan = _scan_rows()
    for name, it in its.items():
        early = [
            s
            for s in scan
            if s["group"] == "early" and name in s["items"] and "narrow" in s["items"][name]
        ]
        pick = random.Random(f"{a['seed']}:early:{name}").sample(
            early, min(a["early_per_item"], len(early))
        )
        for s in pick:
            jobs.append(
                _job(f"early:{name}:{s['work_id']}", it, s["items"][name]["narrow"]["passage"])
            )
    ordinary = json.loads((PRIVATE / "ordinary.json").read_text())["chosen"]
    by = {s["work_id"]: s for s in scan}
    for name, ids in ordinary.items():
        for wid in ids:
            jobs.append(
                _job(
                    f"ordinary:{name}:{wid}", its[name], by[wid]["items"][name]["broad"]["passage"]
                )
            )
    path = out(PRIVATE / "jobs_check.jsonl")
    path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))
    print(f"{len(jobs)} known-answer questions -> {path}")
    return len(jobs)


def check_jobs2(cfg: dict) -> int:
    """Second attempt: the same questions, whole 1830 paragraphs and wider library windows."""
    a = cfg["lab"]["archaic"]
    its, words = items(cfg), a["second_window_words"]
    paras = [json.loads(x) for x in EDITION.read_text().splitlines() if x.strip()]
    first = [json.loads(x)["id"] for x in (PRIVATE / "jobs_check.jsonl").read_text().splitlines()]
    rows = {
        s["work_id"]: s
        for s in _scan_rows()
        if s["group"] in ("early",) or s["group"].startswith("lib:")
    }
    cat = {
        r["work_id"]: r
        for r in _with_text(
            [
                {**r}
                for r in _registry_rows(
                    {j.split(":", 2)[2] for j in first if not j.startswith("cited:")}
                )
            ]
        )
    }
    jobs = []
    for jid in first:
        kind, name, *rest = jid.split(":", 2)
        it = its[name]
        if kind == "cited":
            book, anchor = CITED[name]
            p = next(p for p in paras if p["book"] == book and anchor in p["text"])
            at = p["text"].find(anchor)
            m = min(it["pattern"].finditer(p["text"]), key=lambda m: abs(m.start() - at))
            passage = marked(p["text"], m.start(), m.end())
        else:
            wid = rest[0]
            which, pat = ("narrow", it["pattern"]) if kind == "early" else ("broad", it["broad"])
            at = rows[wid]["items"][name][which]["at"]
            try:
                text = door.text_of(cat[wid])
            except OSError:
                continue  # unreadable: not attempted
            m = pat.match(text, at)
            passage = window(text, m.start(), m.end(), words)
        jobs.append(
            {
                "id": jid,
                "prompt": PROMPT2.format(
                    form=it["item"].lower(), a=it["a"], b=it["b"], passage=passage
                ),
            }
        )
    path = out(PRIVATE / "jobs_check2.jsonl")
    path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))
    print(f"{len(jobs)} known-answer questions (second attempt) -> {path}")
    return len(jobs)


def _count(job: tuple[dict, dict]) -> dict:
    row, pats = job
    try:
        text = door.text_of(row)
    except OSError:
        return {"work_id": row["work_id"], "unreadable": True}
    return {
        "work_id": row["work_id"],
        "n": {k: len(re.findall(p, text, flags=re.I)) for k, p in pats.items()},
    }


def frames(cfg: dict) -> dict:
    """Redesign estimate: hits of each item's cited-verse frame in the same sample (no model)."""
    a = cfg["lab"]["archaic"]
    pats = {k: v for k, v in a["frames"].items() if v}
    scan = [s for s in _scan_rows() if s["group"].startswith("lib:") or s["group"] == "ctl"]
    rows = _with_text(_registry_rows({s["work_id"] for s in scan}))
    with ProcessPoolExecutor(cfg["lab"]["phrase_workers"]) as pool:
        got = {g["work_id"]: g for g in pool.map(_count, [(r, pats) for r in rows], chunksize=16)}
    res: dict = {}
    for name in a["frames"]:
        cells = {}
        for g in sorted({s["group"] for s in scan}):
            ws = [got.get(s["work_id"], {"unreadable": True}) for s in scan if s["group"] == g]
            hits = [w["n"][name] for w in ws if "n" in w and name in w["n"]]
            cells[g] = {
                "works": len(ws),
                "unreadable": len([w for w in ws if "n" not in w]),
                "works_with_hit": len([h for h in hits if h]),
                "hits": sum(hits),
            }
            cells[g]["judged_capped"] = min(cells[g]["hits"], a["frame_cap"])
        res[name] = (
            {"pattern": a["frames"][name], "cells": cells}
            if a["frames"][name]
            else {"pattern": None}
        )
    out(PRIVATE / "frames.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def _registry_rows(ids: set[str]) -> list[dict]:
    return [r for r in registry.load().to_pylist() if r["work_id"] in ids]


def ordinary_candidates(cfg: dict, per: int = 12) -> None:
    """Broad-pattern hits from the ordinary years, for choosing plainly ordinary uses by hand."""
    a = cfg["lab"]["archaic"]
    lo, hi = a["ordinary_years"]
    scan = [s for s in _scan_rows() if s["group"].startswith("lib:") and lo <= s["year"] <= hi]
    lines = []
    for name in items(cfg):
        pool = [s for s in scan if "broad" in s["items"].get(name, {})]
        for s in random.Random(f"{a['seed']}:ordinary:{name}").sample(pool, min(per, len(pool))):
            lines.append(f"{name}\t{s['work_id']}\t{s['items'][name]['broad']['passage']}")
    path = out(PRIVATE / "ordinary_candidates.tsv")
    path.write_text("\n".join(lines) + "\n")
    print(f"{len(lines)} candidates -> {path}")


def _answers(path: Path, attempt: int = 1) -> dict[str, tuple[str, str] | None]:
    """Parsed replies by id (None = unparsed, logged once with its raw text, never counted)."""
    if not path.exists():
        return {}
    log = LOGS / "archaic_unparsed.jsonl"
    seen = (
        {json.loads(x)["id"] for x in log.read_text().splitlines() if x} if log.exists() else set()
    )
    res = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            res[r["id"]] = parse(r["reply"], attempt)
            if res[r["id"]] is None and r["id"] not in seen:
                with out(log).open("a") as fh:
                    fh.write(json.dumps({"id": r["id"], "reply": r["reply"]}) + "\n")
    return res


def check_result(cfg: dict, attempt: int = 1) -> dict:
    a = cfg["lab"]["archaic"]
    tag = "" if attempt == 1 else "2"
    jobs = [
        json.loads(x)["id"] for x in (PRIVATE / f"jobs_check{tag}.jsonl").read_text().splitlines()
    ]
    ans = _answers(PRIVATE / f"answers_check{tag}.jsonl", attempt)
    res: dict = {}
    for kind in ("cited", "early", "ordinary"):
        ids = [j for j in jobs if j.startswith(kind + ":")]
        got = [ans[j] for j in ids if ans.get(j)]
        res[kind] = {
            "questions": len(ids),
            "answered": len([j for j in ids if j in ans]),
            "parsed": len(got),
            **Counter(s for s, _ in got),
            "verdicts": {j: "".join(ans[j]).rstrip("-") if ans.get(j) else None for j in ids},
        }
    c, o = res["cited"], res["ordinary"]
    res["cited_bar"], res["ordinary_a_max"] = a["cited_bar"], a["ordinary_a_max"]
    complete = all(
        res[k]["answered"] == res[k]["questions"]
        for k in res
        if k in ("cited", "early", "ordinary")
    )
    res["complete"] = complete
    res["passed"] = (
        complete
        and c.get("A", 0) >= a["cited_bar"]
        and (o.get("A", 0) <= a["ordinary_a_max"] * o["questions"])
    )
    return res


def library_jobs(cfg: dict) -> int:
    a = cfg["lab"]["archaic"]
    chk = check_result(cfg)
    if not chk["passed"]:
        raise SystemExit(
            f"the known-answer check has not passed: {chk['cited']}, "
            f"{chk['ordinary']}; library passages are not judged"
        )
    its, scan, jobs = items(cfg), _scan_rows(), []
    for name, it in its.items():
        for g in sorted({s["group"] for s in scan if s["group"].startswith(("lib:", "ctl"))}):
            pool = sorted(
                (s for s in scan if s["group"] == g and "narrow" in s["items"].get(name, {})),
                key=lambda s: s["work_id"],
            )
            for s in random.Random(f"{a['seed']}:{g}:{name}").sample(
                pool, min(a["passages"], len(pool))
            ):
                jobs.append(
                    _job(f"{g}:{name}:{s['work_id']}", it, s["items"][name]["narrow"]["passage"])
                )
    n_check = len((PRIVATE / "jobs_check.jsonl").read_text().splitlines())
    if len(jobs) + n_check > a["max_calls"]:
        raise SystemExit(f"{len(jobs) + n_check} calls would pass the cap of {a['max_calls']}")
    path = out(PRIVATE / "jobs_library.jsonl")
    path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))
    print(f"{len(jobs)} library and control questions -> {path}")
    return len(jobs)


def score(cfg: dict) -> dict:
    a = cfg["lab"]["archaic"]
    its, scan = items(cfg), _scan_rows()
    second = (PRIVATE / "jobs_check2.jsonl").exists()
    res: dict = {
        "known_answer_second_attempt": check_result(cfg, 2) if second else None,
        "known_answer": check_result(cfg),
        "settings": {k: v for k, v in a.items() if k != "items"},
        "judging": "simulated judging by an AI "
        "model (lab.judge, model " + cfg["lab"]["judge"]["model"] + ")",
    }
    res["items"] = {
        n: {
            "index": i["index"],
            "item": i["item"],
            "reference": i["reference"],
            "pattern": i["pattern"].pattern,
        }
        for n, i in its.items()
    }
    groups = sorted({s["group"] for s in scan})
    res["coverage"] = {
        g: {
            "works": len([s for s in scan if s["group"] == g]),
            "unreadable": len([s for s in scan if s["group"] == g and s["unreadable"]]),
        }
        for g in groups
    }
    jobs_path = PRIVATE / "jobs_library.jsonl"
    jobs = (
        [json.loads(x)["id"] for x in jobs_path.read_text().splitlines()]
        if (jobs_path.exists())
        else []
    )
    ans = _answers(PRIVATE / "answers_library.jsonl")
    hand = (
        json.loads((PRIVATE / "handcheck.json").read_text())
        if (PRIVATE / "handcheck.json").exists()
        else {}
    )
    per: dict = {}
    for name in its:
        cells = {}
        for g in groups:
            if g == "early":
                continue
            rows = [s for s in scan if s["group"] == g]
            hit = [s for s in rows if "narrow" in s["items"].get(name, {})]
            ids = [j for j in jobs if j.startswith(f"{g}:{name}:")]
            v = [ans[j] for j in ids if ans.get(j)]
            ao = [j for j in ids if ans.get(j) == ("A", "O")]
            cells[g] = {
                "works": len(rows),
                "works_with_hit": len(hit),
                "raw_hits": sum(s["items"][name]["narrow"]["n"] for s in hit),
                "broad_hits": sum(
                    s["items"].get(name, {}).get("broad", {}).get("n", 0) for s in rows
                ),
                "judged": len(ids),
                "answered": len([j for j in ids if j in ans]),
                "parsed": len(v),
                **{f"sense_{k}": n for k, n in Counter(x for x, _ in v).items()},
                "A_and_O": len(ao),
                "A_and_Q": len([j for j in ids if ans.get(j) == ("A", "Q")]),
                "A_and_O_ids": [j.split(":", 2)[2] for j in ao],
                "hand_agrees": len([j for j in ao if hand.get(j) == "agree"]),
                "hand_checked": len([j for j in ao if j in hand]),
            }
        lib = [g for g in cells if g.startswith("lib:") and int(g[4:]) >= 1750]
        live = [g for g in lib if cells[g]["hand_agrees"]]
        per[name] = {
            "cells": cells,
            "latest_decade_A_and_O_hand_agreed": max((int(g[4:]) for g in live), default=None),
            "first_look": "not judged: the known-answer check missed its bar"
            if not res["known_answer"]["passed"]
            else "found in the writer's own words after 1750"
            if live
            else "not found in the sample",
        }
    res["by_item"] = per
    if (PRIVATE / "frames.json").exists():  # counts only: the redesign's frame hits (no model)
        res["redesign_frame_hits"] = json.loads((PRIVATE / "frames.json").read_text())
    if not res["known_answer"]["passed"]:
        res["stopped"] = (
            "the known-answer check missed its bar; no library or control passage was judged. "
            "Raw hit counts (no model) are reported."
        )
    calls = (
        len(jobs)
        + res["known_answer"]["cited"]["questions"]
        + res["known_answer"]["early"]["questions"]
        + res["known_answer"]["ordinary"]["questions"]
        + (
            sum(
                res["known_answer_second_attempt"][k]["questions"]
                for k in ("cited", "early", "ordinary")
            )
            if second
            else 0
        )
    )
    decades = len([g for g in groups if g.startswith("lib:")])
    per_item = (
        decades * a["passages"] + a["passages"] + 1 + a["early_per_item"] + a["ordinary_per_item"]
    )
    res["cost"] = {
        "pilot_calls": calls,
        "full_items": a["full_items"],
        "full_calls_per_item_at_most": per_item,
        "full_calls_at_most": per_item * a["full_items"],
        "nights_at_calls_per_night": round(per_item * a["full_items"] / a["calls_per_night"], 2),
    }
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "cmd", choices=["search", "candidates", "check-jobs", "jobs", "check", "frames", "score"]
    )
    ap.add_argument("--attempt", type=int, choices=[1, 2], default=1, help="check-jobs, check")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "search":
        print(search(cfg))
    elif a.cmd == "candidates":
        ordinary_candidates(cfg)
    elif a.cmd == "check-jobs":
        check_jobs2(cfg) if a.attempt == 2 else check_jobs(cfg)
    elif a.cmd == "check":
        r = check_result(cfg, a.attempt)
        print(json.dumps({k: v for k, v in r.items()}, indent=1))
    elif a.cmd == "frames":
        print(
            json.dumps(
                {
                    n: {g: c["hits"] for g, c in v.get("cells", {}).items()}
                    for n, v in frames(cfg).items()
                }
            )
        )
    elif a.cmd == "jobs":
        library_jobs(cfg)
    else:
        res = score(cfg)
        res["config_sha256"] = config.sha256_of_config()
        res["commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        out(PUBLIC / "pilot.json").write_text(json.dumps(res, indent=1) + "\n")
        print(
            json.dumps(
                {
                    n: {g: (c["works_with_hit"], c["A_and_O"]) for g, c in v["cells"].items()}
                    for n, v in res["by_item"].items()
                },
                indent=1,
            )
        )
        print(json.dumps(res["cost"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
