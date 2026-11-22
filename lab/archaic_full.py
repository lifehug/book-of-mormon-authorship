"""BOM-118 full run: Skousen's archaic word uses and phrases, by cited-verse frame, whole library.

Follows the pilot (``lab.archaic``). Each item has a frame (the construction of its cited verse)
in ``lab.archaic_full.items``. Every eligible library work 1740-1830 is scanned for every frame
(no model; offsets only, on local disk under ``data/corpus/lab/archaic/``), and so are the
Bible-style control books and Joseph Smith's own texts. A per-item known-answer check (the cited
1830 paragraph, and plainly ordinary uses chosen by hand) is queued first; then every frame hit,
up to ``frame_cap`` per item per decade, is put to a hosted model through ``lab.judge``: sense A
(claimed) or B. Every such answer is **simulated judging by an AI model**. Every A answer is then
checked by a person (own words after 1740 / quotation or reprint / not the claimed sense), and
only hand-confirmed uses count. The test card is
``data/private/lab/owner/2026-11-21-archaic-vocabulary-full/card.md``. Passages, prompts and
replies quote text and stay private; the public result holds ids and counts.

Usage::

    python -m lab.archaic_full frametest    # frames on the pilot's sample: empty / swamped / ok
    python -m lab.archaic_full scan         # every eligible work + controls (resumable, parts)
    python -m lab.archaic_full jobs --check-only   # the per-item check alone (no scan needed)
    python -m lab.archaic_full jobs         # one jobs file per stage (needs ordinary.json)
    python -m lab.archaic_full status       # answered / open per stage
    python -m lab.archaic_full handlist     # every A answer, for the hand check
    python -m lab.archaic_full handjobs     # the same answers as questions for a second AI reading
    python -m lab.archaic_full handread     # that reading's replies -> handcheck.json
    python -m lab.archaic_full score        # -> data/lab/reruns/archaic_vocabulary/full.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab import archaic, door
from lab.combinations_judge import dedup_key, group_passages
from lab.paths import FAST, REGISTRY, out
from metadata import config

PRIVATE = Path("data/private/lab/owner/2026-11-21-archaic-vocabulary-full")
PILOT = archaic.PRIVATE
SCAN = FAST / "archaic"
PUBLIC = REGISTRY / "reruns" / "archaic_vocabulary"
STAGES = ("check", "control", "library")
HAND = ("own_words", "quotation_or_reprint", "not_claimed")


def settings(cfg: dict) -> dict:
    return cfg["lab"]["archaic_full"]


def items(cfg: dict) -> dict[str, dict]:
    listed = json.loads(archaic.ITEMS.read_text())["items"]
    res = {}
    for name, (idx, frame, broad, a, b, anchor, reason) in settings(cfg)["items"].items():
        res[name] = {
            "index": idx,
            "item": listed[idx]["item"],
            "reference": listed[idx]["reference"],
            "frame": re.compile(frame, re.I) if frame else None,
            "broad": re.compile(broad, re.I),
            "a": a,
            "b": b,
            "anchor": anchor,
            "reason": reason,
        }
    return res


def decade(year: int, cfg: dict) -> int:
    last = ((settings(cfg)["year_max"] - 1) // 10) * 10
    return min((year // 10) * 10, last)


def died(author: str | None) -> int | None:
    """The death year in a catalogued author string ("Bunyan, John, 1628-1688"), if given."""
    m = re.search(r"\b1[0-9]{3}\??\s*-\s*(1[0-9]{3})\b", author or "") or re.search(
        r"\bd\.\s*(1[0-9]{3})\b", author or ""
    )
    return int(m.group(1)) if m else None


def cited(cfg: dict) -> dict[str, dict]:
    """The whole cited 1830 paragraph per item, the frame's hit nearest the anchor marked."""
    paras = [json.loads(x) for x in archaic.EDITION.read_text().splitlines() if x.strip()]
    res = {}
    for name, it in items(cfg).items():
        book, anchor = it["anchor"]
        p = next((p for p in paras if p["book"] == book and anchor in p["text"]), None)
        if p is None:
            res[name] = {"found": False}
            continue
        at = p["text"].find(anchor)
        ms = list(it["frame"].finditer(p["text"])) if it["frame"] else []
        if not ms:
            res[name] = {"found": True, "frame_matches": False, "seq": p["seq"]}
            continue
        m = min(ms, key=lambda m: abs(m.start() - at))
        passage = archaic.marked(p["text"], m.start(), m.end())
        res[name] = {"found": True, "frame_matches": True, "seq": p["seq"], "passage": passage}
    return res


# ---- frame test on the pilot's sample -------------------------------------------------------


def _count(job: tuple[dict, dict, list[int], int, int]) -> dict:
    row, pats, years, seed, words = job
    try:
        text = door.text_of(row)
    except OSError:
        return {"work_id": row["work_id"], "unreadable": True}
    res = {"work_id": row["work_id"], "n": {}, "ordinary": {}}
    for name, (frame, broad) in pats.items():
        f = len(re.findall(frame, text, flags=re.I)) if frame else 0
        bh = [(m.start(), m.end()) for m in re.finditer(broad, text, flags=re.I)]
        res["n"][name] = [f, len(bh)]
        if bh and row.get("year") and years[0] <= row["year"] <= years[1]:
            s, e = random.Random(f"{seed}:{name}:{row['work_id']}").choice(bh)
            res["ordinary"][name] = archaic.window(text, s, e, 60)
    return res


def frametest(cfg: dict) -> dict:
    a = settings(cfg)
    its = items(cfg)
    pats = {
        n: (i["frame"].pattern if i["frame"] else None, i["broad"].pattern) for n, i in its.items()
    }
    scan = [
        s for s in archaic._scan_rows() if s["group"].startswith("lib:") or s["group"] == "early"
    ]
    group = {s["work_id"]: s["group"] for s in scan}
    rows = archaic._with_text(archaic._registry_rows(set(group)))
    jobs = [(r, pats, a["ordinary_years"], a["seed"], 60) for r in rows]
    with ProcessPoolExecutor(a["workers"]) as pool:
        got = list(pool.map(_count, jobs, chunksize=16))
    cit = cited(cfg)
    res: dict = {}
    for name, it in its.items():
        lib = [g["n"][name] for g in got if "n" in g and group[g["work_id"]] != "early"]
        early = [g["n"][name] for g in got if "n" in g and group[g["work_id"]] == "early"]
        f, b = sum(x[0] for x in lib), sum(x[1] for x in lib)
        fe = sum(x[0] for x in early)
        verdict = (
            "cannot test by frame"
            if not it["frame"]
            else (
                "frame misses its cited verse"
                if not cit[name].get("frame_matches")
                else "empty"
                if f + fe == 0
                else "swamped"
                if b > a["swamp_min_broad"] and f > a["swamp_share"] * b
                else "ok"
            )
        )
        res[name] = {
            "frame_hits_sample": f,
            "broad_hits_sample": b,
            "frame_hits_early": fe,
            "works_with_frame_hit": len([x for x in lib if x[0]]),
            "verdict": verdict,
            "reason": it["reason"],
        }
    lines = []
    for g in got:
        for name, passage in g.get("ordinary", {}).items():
            lines.append((name, g["work_id"], passage))
    pick = []
    for name in its:
        pool = sorted([x for x in lines if x[0] == name], key=lambda x: x[1])
        pick += random.Random(f"{a['seed']}:ordinary:{name}").sample(pool, min(4, len(pool)))
    out(PRIVATE / "ordinary_candidates.tsv").write_text(
        "".join(f"{n}\t{w}\t{p}\n" for n, w, p in pick)
    )
    out(PRIVATE / "frametest.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


# ---- full scan ---------------------------------------------------------------------------


def _frames(cfg: dict) -> dict[str, str]:
    return {n: i["frame"].pattern for n, i in items(cfg).items() if i["frame"]}


def _scan_one(job: tuple[dict, dict]) -> dict:
    row, pats = job
    try:
        text = door.text_of(row) if "text" not in row else row["text"]
    except OSError:
        return {"work_id": row["work_id"], "unreadable": True}
    hits = {}
    low = text.lower()
    for name, pat in pats.items():
        if KEYS.get(name, "") not in low:
            continue  # no hit possible: every hit of the frame contains this word
        found = [m.start() for m in re.finditer(pat, text, flags=re.I)]
        if found:
            hits[name] = found
    return {"work_id": row["work_id"], "hits": hits}


# A lower-case string every hit of the item's frame contains: a text without it is skipped
# (speed only; the hits found are the same). Single words, so line breaks cannot hide them.
KEYS = {
    "break": "break", "mar": "mar", "belove": "beloved", "counsel": "counsel",
    "desirous": "desirous", "devour": "devour", "molten": "molten", "but": "lest",
    "call": "call", "consigned": "consigned", "course": "course", "cross": "cross",
    "depressed": "depressed", "extinct": "extinct", "flatter": "flatter", "give": "gave",
    "hail": "hail", "idleness": "idleness", "opinion": "opinion", "rebellion": "rebellion",
    "rent": "rent", "reserve": "reserve", "tell": "tell", "views": "views",
    "welfare": "welfare", "whereby": "whereby", "arrive_to": "arriv", "be_aware": "aware",
    "begin_to": "beg", "belief_on": "belief", "do_away": "away", "for_the_cause_of": "cause",
    "hurl_away": "hurl", "in_the_favor_of": "favo", "in_the_fourth_day": "month",
    "into_an_effect": "effect", "on_the_seventh_month": "month", "search_knowledge": "search",
    "somewhat_contentions": "somewhat", "strong_hold": "hold", "to_that": "that",
    "where_unto": "unto",
}  # fmt: skip


def library_rows(cfg: dict) -> list[dict]:
    a = settings(cfg)
    ctl = {json.loads(x)["work_id"] for x in Path(a["controls"]).read_text().splitlines() if x}
    rows = [
        r
        for r in archaic._eligible()
        if a["year_min"] <= r["year"] <= a["year_max"] and r["work_id"] not in ctl
    ]
    return sorted(archaic._with_text(rows), key=lambda r: r["work_id"])


def control_rows(cfg: dict) -> list[dict]:
    """The Bible-style control works (with text) and Joseph Smith's own texts (text inline)."""
    a = settings(cfg)
    ctl = [json.loads(x) for x in Path(a["controls"]).read_text().splitlines() if x.strip()]
    ids = {c["work_id"] for c in ctl}
    reg = {r["work_id"]: r for r in archaic._registry_rows(ids)}
    rows = [
        {**reg[c["work_id"]], **c, "group": "ctl"}
        for c in ctl
        if c["work_id"] in reg and reg[c["work_id"]]["has_text"]
    ]
    rows = archaic._with_text(rows)
    for pattern in a["js_texts"]:
        for f in sorted(glob.glob(pattern)):
            p = Path(f)
            if p.suffix == ".jsonl":
                pages = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
                text = "\n".join(pg.get("text") or "" for pg in pages)
            else:
                text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"(18[23]\d)", p.stem)
            rows.append(
                {
                    "work_id": f"js:{p.parent.name}/{p.stem}",
                    "group": "js",
                    "text": text,
                    "year": int(m.group(1)) if m else None,
                    "author": "Smith, Joseph",
                }
            )
    return rows


def scan(cfg: dict) -> dict:
    """Resumable: each part of ``part_size`` works is written once, whole, and skipped after."""
    a = settings(cfg)
    pats = _frames(cfg)
    rows = library_rows(cfg)
    parts = [rows[i : i + a["part_size"]] for i in range(0, len(rows), a["part_size"])]
    done = 0
    with ProcessPoolExecutor(a["workers"]) as pool:
        for k, part in enumerate(parts):
            path = SCAN / "parts" / f"part-{k:05d}.jsonl"
            if path.exists():
                done += 1
                continue
            got = list(pool.map(_scan_one, [(r, pats) for r in part], chunksize=8))
            meta = {r["work_id"]: r for r in part}
            lines = []
            for g in got:
                r = meta[g["work_id"]]
                g.update(year=r["year"], source=r["source"], author=r.get("author"))
                if g.get("unreadable") or g["hits"]:
                    lines.append(json.dumps(g) + "\n")
            tmp = out(path.with_suffix(".tmp"))
            tmp.write_text("".join(lines) + json.dumps({"part_done": len(part)}) + "\n")
            os.replace(tmp, path)
            done += 1
            print(f"part {k + 1}/{len(parts)} done", flush=True)
    ctl = control_rows(cfg)
    with ProcessPoolExecutor(a["workers"]) as pool:
        got = list(pool.map(_scan_one, [(r, pats) for r in ctl], chunksize=1))
    meta = {r["work_id"]: r for r in ctl}
    lines = [
        json.dumps(
            {
                **g,
                "group": meta[g["work_id"]]["group"],
                "year": meta[g["work_id"]].get("year"),
                "author": meta[g["work_id"]].get("author"),
            }
        )
        + "\n"
        for g in got
    ]
    out(SCAN / "controls.jsonl").write_text("".join(lines))
    return {"works": len(rows), "parts": len(parts), "parts_done": done, "controls": len(ctl)}


def _library_scan(cfg: dict) -> tuple[list[dict], int]:
    found, total = [], 0
    for f in sorted((SCAN / "parts").glob("part-*.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if "part_done" in r:
                total += r["part_done"]
            else:
                found.append(r)
    return found, total


def _control_scan() -> list[dict]:
    return [json.loads(x) for x in (SCAN / "controls.jsonl").read_text().splitlines() if x]


# ---- jobs --------------------------------------------------------------------------------


def _round_robin(works: list[dict], name: str, cap: int, key: str) -> list[tuple[str, int]]:
    """Up to ``cap`` (work_id, offset): each work's first hit, then second hits, in seeded order."""
    rng = random.Random(key)
    order = sorted(works, key=lambda w: w["work_id"])
    rng.shuffle(order)
    lists = [(w["work_id"], rng.sample(w["hits"][name], len(w["hits"][name]))) for w in order]
    picked, r = [], 0
    while len(picked) < cap and any(len(h) > r for _, h in lists):
        picked += [(wid, h[r]) for wid, h in lists if len(h) > r][: cap - len(picked)]
        r += 1
    return picked


def _job(jid: str, it: dict, passage: str) -> dict:
    prompt = archaic.PROMPT2.format(form=it["item"].lower(), a=it["a"], b=it["b"], passage=passage)
    return {"id": jid, "prompt": prompt}


def _windows(picks: list[tuple[str, str, int]], rows: dict, its: dict, words: int) -> list[dict]:
    """Jobs for (group, item, work_id, offset) picks; each text read once."""
    by: dict[str, list] = defaultdict(list)
    for g, name, wid, at in picks:
        by[wid].append((g, name, at))
    jobs = []
    for wid in sorted(by):
        row = rows[wid]
        try:
            text = row["text"] if "text" in row else door.text_of(row)
        except OSError:
            continue  # unreadable: not attempted
        for g, name, at in by[wid]:
            m = its[name]["frame"].match(text, at)
            if not m:
                continue
            passage = archaic.window(text, m.start(), m.end(), words)
            jobs.append(_job(f"{g}|{name}|{wid}|{at}", its[name], passage))
    return jobs


def _ordinary_window(row: dict, it: dict, shown: str, words: int) -> str | None:
    """The ``words``-word window around the broad hit whose 60-word window was shown by hand."""
    try:
        text = door.text_of(row)
    except OSError:
        return None
    for m in it["broad"].finditer(text):
        if archaic.window(text, m.start(), m.end(), 60) == shown:
            return archaic.window(text, m.start(), m.end(), words)
    return None


def check_jobs(cfg: dict) -> list[dict]:
    """The cited 1830 paragraph per framed item, and the hand-chosen ordinary uses."""
    a = settings(cfg)
    its = {n: i for n, i in items(cfg).items() if i["frame"]}
    cit = cited(cfg)
    check = [
        _job(f"cited|{n}", its[n], cit[n]["passage"]) for n in its if cit[n].get("frame_matches")
    ]
    ordinary = json.loads((PRIVATE / "ordinary.json").read_text())["chosen"]
    cands = {
        (n, w): p
        for n, w, p in (
            x.split("\t", 2) for x in (PRIVATE / "ordinary_candidates.tsv").read_text().splitlines()
        )
    }
    rows = {
        r["work_id"]: r
        for r in archaic._with_text(
            archaic._registry_rows({w for ws in ordinary.values() for w in ws})
        )
    }
    for name, wids in ordinary.items():
        for wid in wids:
            passage = _ordinary_window(rows[wid], its[name], cands[(name, wid)], a["window_words"])
            if passage:  # not found again: not attempted
                check.append(_job(f"ordinary|{name}|{wid}", its[name], passage))
    return check


def jobs(cfg: dict, only_check: bool = False) -> dict:
    a = settings(cfg)
    its = {n: i for n, i in items(cfg).items() if i["frame"]}
    check = check_jobs(cfg)
    if only_check:
        path = out(PRIVATE / "jobs_check.jsonl")
        path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in check))
        return {"check": len(check)}
    # Items that completed their check and missed it are "cannot test": not queued further.
    chk = item_check(cfg) if (PRIVATE / "answers_check.jsonl").exists() else {}
    its = {
        n: i
        for n, i in its.items()
        if not (chk.get(n, {}).get("complete") and not chk[n]["passed"])
    }
    # library: per item per decade, round-robin up to the cap
    lib, _ = _library_scan(cfg)
    picks = []
    for name in its:
        by_dec: dict[int, list] = defaultdict(list)
        for w in lib:
            if name in w.get("hits", {}):
                by_dec[decade(w["year"], cfg)].append(w)
        for d, works in sorted(by_dec.items()):
            for wid, at in _round_robin(works, name, a["frame_cap"], f"{a['seed']}:{name}:{d}"):
                picks.append((f"lib:{d}", name, wid, at))
    rows = {r["work_id"]: r for r in library_rows(cfg) if r["work_id"] in {p[2] for p in picks}}
    library = _windows(picks, rows, its, a["window_words"])
    ctl = _control_scan()
    cpicks = []
    for name in its:
        for g in ("ctl", "js"):
            works = [w for w in ctl if w["group"] == g and name in w.get("hits", {})]
            for wid, at in _round_robin(works, name, a["frame_cap"], f"{a['seed']}:{name}:{g}"):
                cpicks.append((g, name, wid, at))
    crow = {r["work_id"]: r for r in control_rows(cfg)}
    control = _windows(cpicks, crow, its, a["window_words"])
    res = {}
    for stage, js in zip(STAGES, (check, control, library), strict=True):
        path = out(PRIVATE / f"jobs_{stage}.jsonl")
        path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in js))
        res[stage] = len(js)
    return res


# ---- answers, hand check, score ------------------------------------------------------------


def answers(stage: str) -> dict[str, str | None]:
    return {
        k: (v[0] if v else None)
        for k, v in archaic._answers(PRIVATE / f"answers_{stage}.jsonl", 2).items()
    }


def status() -> dict:
    res = {}
    for stage in STAGES:
        p = PRIVATE / f"jobs_{stage}.jsonl"
        n = len(p.read_text().splitlines()) if p.exists() else 0
        res[stage] = {"questions": n, "answered": len(answers(stage))}
    return res


def item_check(cfg: dict) -> dict[str, dict]:
    ans = answers("check")
    ids = [json.loads(x)["id"] for x in (PRIVATE / "jobs_check.jsonl").read_text().splitlines()]
    res = {}
    for name, it in items(cfg).items():
        if not it["frame"]:
            continue
        c = ans.get(f"cited|{name}")
        ords = [ans.get(j) for j in ids if j.startswith(f"ordinary|{name}|")]
        done = f"cited|{name}" in ans and None not in ords
        res[name] = {
            "cited": c,
            "ordinary": ords,
            "complete": done,
            "passed": done and c == "A" and "A" not in ords,
        }
    return res


def handlist(cfg: dict) -> int:
    """Every A answer from the library and controls, with its passage, for a person to mark."""
    hand = _hand()
    lines = [
        "id\titem\tyear\tolder_author\tverdict (own_words / quotation_or_reprint / "
        "not_claimed)\tpassage"
    ]
    meta = _meta(cfg)
    for stage in ("control", "library"):
        prompts = {
            j["id"]: j["prompt"]
            for j in map(json.loads, (PRIVATE / f"jobs_{stage}.jsonl").read_text().splitlines())
        }
        for jid, v in answers(stage).items():
            if v != "A" or jid in hand:
                continue
            g, name, wid, _ = jid.split("|")
            m = meta.get(wid, {})
            passage = prompts[jid].split("Passage:\n", 1)[1].split("\n\nReply", 1)[0]
            lines.append(
                f"{jid}\t{name}\t{m.get('year')}\t{m.get('older', False)}\t\t"
                f"{' '.join(passage.split())}"
            )
    out(PRIVATE / "handcheck_todo.tsv").write_text("\n".join(lines) + "\n")
    print(
        f"{len(lines) - 1} A answers to check -> {PRIVATE / 'handcheck_todo.tsv'}; record "
        f"verdicts in {PRIVATE / 'handcheck.json'} as {{id: one of {HAND}}}"
    )
    return len(lines) - 1


PROMPT_HAND = """A passage from a book printed between 1740 and 1830 is below. It uses \
"{form}". A first reader judged that it is used in this sense: {a}. (The other sense is: {b}.)

Decide which one of these is true of that use in the passage:
OWN - the claimed sense, in the writer's own words, written after 1740.
QUOTE - the claimed sense, but the words are quoted, reprinted or closely paraphrased from an \
older text (the King James Bible, or any writer before 1740), or the passage is itself a reprint \
of an older work.
NOT - not the claimed sense after all, or too garbled to tell.

Passage:
{passage}

Reply with one word on the first line: OWN, QUOTE or NOT. Then one short line of reason."""
_HAND_WORD = {"OWN": "own_words", "QUOTE": "quotation_or_reprint", "NOT": "not_claimed"}


def handjobs(cfg: dict) -> int:
    """Every A answer as a question for a second reading by a different model (lab.judge)."""
    its = items(cfg)
    js = []
    for stage in ("control", "library"):
        prompts = {
            j["id"]: j["prompt"]
            for j in map(json.loads, (PRIVATE / f"jobs_{stage}.jsonl").read_text().splitlines())
        }
        for jid, v in answers(stage).items():
            if v != "A":
                continue
            it = its[jid.split("|")[1]]
            passage = prompts[jid].split("Passage:\n", 1)[1].split("\n\nReply", 1)[0]
            js.append(
                {
                    "id": jid,
                    "prompt": PROMPT_HAND.format(
                        form=it["item"].lower(), a=it["a"], b=it["b"], passage=passage
                    ),
                }
            )
    out(PRIVATE / "jobs_hand.jsonl").write_text(
        "".join(json.dumps(j, ensure_ascii=False) + "\n" for j in js)
    )
    print(f"{len(js)} questions -> {PRIVATE / 'jobs_hand.jsonl'}")
    return len(js)


def parse_hand(reply: str) -> str | None:
    m = re.match(r"\W*(OWN|QUOTE|NOT)\b", reply.strip())
    return _HAND_WORD[m.group(1)] if m else None


def handread() -> dict:
    """Second-reading replies -> handcheck.json. A verdict already there (a person's) is kept."""
    hand = _hand()
    p = PRIVATE / "answers_hand.jsonl"
    new = unparsed = 0
    for line in p.read_text().splitlines() if p.exists() else []:
        r = json.loads(line)
        v = parse_hand(r["reply"])
        if v is None:
            unparsed += 1
        elif r["id"] not in hand:
            hand[r["id"]] = v
            new += 1
    out(PRIVATE / "handcheck.json").write_text(json.dumps(hand, indent=1, sort_keys=True) + "\n")
    res = {"verdicts": len(hand), "added": new, "unparsed": unparsed}
    print(json.dumps(res))
    return res


def _hand() -> dict[str, str]:
    """Verdicts by id: the second model's (handcheck.json), with the assistant's own reading of
    the deciding passages (handcheck_assistant.json) laid over them."""
    res: dict[str, str] = {}
    for name in ("handcheck.json", "handcheck_assistant.json"):
        p = PRIVATE / name
        if p.exists():
            res.update(json.loads(p.read_text()))
    return res


def _passage_keys(n: int) -> dict[str, list[str]]:
    """For every claimed-sense answer, the words each side of the marked use (reprint rule)."""
    p = PRIVATE / "jobs_hand.jsonl"
    res = {}
    for line in p.read_text().splitlines() if p.exists() else []:
        j = json.loads(line)
        passage = j["prompt"].split("Passage:\n", 1)[1].split("\n\nReply", 1)[0]
        left, _, rest = passage.partition("[[")
        res[j["id"]] = dedup_key(left, rest.partition("]]")[2], n)
    return res


def _meta(cfg: dict) -> dict[str, dict]:
    a = settings(cfg)
    lib, _ = _library_scan(cfg)
    res = {}
    for w in lib + _control_scan():
        d = died(w.get("author"))
        res[w["work_id"]] = {
            "year": w.get("year"),
            "older": d is not None and d < a["old_author_died_before"],
        }
    return res


def score(cfg: dict) -> dict:
    a = settings(cfg)
    its = items(cfg)
    lib, scanned = _library_scan(cfg)
    ctl = _control_scan()
    meta = _meta(cfg)
    chk = item_check(cfg)
    hand = _hand()
    ans = {**answers("library"), **answers("control")}
    keys = _passage_keys(a["dedup_words"])
    mine = PRIVATE / "handcheck_assistant.json"
    jobs_ids = []
    for stage in ("control", "library"):
        p = PRIVATE / f"jobs_{stage}.jsonl"
        jobs_ids += [json.loads(x)["id"] for x in p.read_text().splitlines()] if p.exists() else []
    res: dict = {
        "judging": f"simulated judging by an AI model (lab.judge, model {a['model']}); every A "
        f"answer checked before it counts. Checked by: {a['checked_by']}",
        "settings": {k: v for k, v in a.items() if k != "items"},
        "library_works_scanned": scanned,
        "library_works_unreadable": len([w for w in lib if w.get("unreadable")]),
        "control_texts": dict(Counter(w["group"] for w in ctl)),
        "verdicts_changed_by_the_assistants_reading": len(json.loads(mine.read_text()))
        if mine.exists()
        else 0,
        "items": {},
    }
    for name, it in its.items():
        row: dict = {"index": it["index"], "item": it["item"], "reference": it["reference"]}
        if not it["frame"]:
            row.update(verdict="cannot test", why=it["reason"])
            res["items"][name] = row
            continue
        hits = Counter()
        for w in lib:
            if name in w.get("hits", {}):
                hits[decade(w["year"], cfg)] += len(w["hits"][name])
        ids = [j for j in jobs_ids if j.split("|")[1] == name]
        cells: dict = {}
        for j in ids:
            g, _, wid, _ = j.split("|")
            c = cells.setdefault(g, Counter())
            c["judged"] += 1
            v = ans.get(j)
            c["answered"] += j in ans
            if v:
                c[f"sense_{v}"] += 1
            if v == "A":
                h = hand.get(j)
                c[f"hand_{h or 'pending'}"] += 1
                if h == "own_words" and meta.get(wid, {}).get("older"):
                    c["own_words_but_older_author"] += 1
        own = sorted(
            {
                j.split("|")[2]
                for j in ids
                if j.startswith("lib:")
                and ans.get(j) == "A"
                and hand.get(j) == "own_words"
                and not meta.get(j.split("|")[2], {}).get("older")
            }
        )
        own_ids = [
            j
            for j in ids
            if j.startswith("lib:")
            and ans.get(j) == "A"
            and hand.get(j) == "own_words"
            and not meta.get(j.split("|")[2], {}).get("older")
        ]
        passages = group_passages([(j, keys.get(j, [j])) for j in own_ids], a["dedup_overlap"])
        pending = sum(c.get("hand_pending", 0) for g, c in cells.items() if g.startswith("lib:"))
        decs = [
            int(j.split("|")[0][4:])
            for j in ids
            if j.startswith("lib:") and ans.get(j) == "A" and hand.get(j) == "own_words"
        ]
        k = chk.get(name, {})
        if not k.get("complete"):
            verdict = "check not complete"
        elif not k.get("passed"):
            verdict = "cannot test (the judge missed this item's check)"
        elif any(ans.get(j) is None for j in ids if j.startswith("lib:")) or pending:
            verdict = "pending (judging or hand check open)"
        elif len(passages) >= a["persists_min"]:
            verdict = "persists"
        elif passages:
            verdict = "attested once"
        else:
            verdict = "not found"
        row.update(
            verdict=verdict,
            check=k,
            frame_hits_by_decade=dict(sorted(hits.items())),
            judged_by_group={g: dict(c) for g, c in sorted(cells.items())},
            own_words_works=own,
            own_words_passages=len(passages),
            latest_decade=max(decs, default=None),
        )
        res["items"][name] = row
    res["tally"] = dict(Counter(r["verdict"] for r in res["items"].values()))
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "cmd",
        choices=[
            "frametest",
            "scan",
            "jobs",
            "status",
            "handlist",
            "handjobs",
            "handread",
            "score",
        ],
    )
    ap.add_argument("--check-only", action="store_true", help="jobs: write the check stage only")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "frametest":
        for n, r in frametest(cfg).items():
            print(
                f"{n:22s} {r['verdict']:30s} frame {r['frame_hits_sample']:5d} in "
                f"{r['works_with_frame_hit']:4d} works; early {r['frame_hits_early']:4d}; "
                f"broad {r['broad_hits_sample']:7d}"
            )
    elif a.cmd == "scan":
        print(scan(cfg))
    elif a.cmd == "jobs":
        print(jobs(cfg, a.check_only))
    elif a.cmd == "status":
        print(json.dumps(status(), indent=1))
    elif a.cmd == "handlist":
        handlist(cfg)
    elif a.cmd == "handjobs":
        handjobs(cfg)
    elif a.cmd == "handread":
        handread()
    else:
        res = score(cfg)
        res["config_sha256"] = config.sha256_of_config()
        res["commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        out(PUBLIC / "full.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res["tally"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
