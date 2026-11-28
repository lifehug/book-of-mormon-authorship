"""BOM-135: does 2 Nephi 28 follow the argument order of Chapin's 1809 farewell sermon?

A reader proposed that 2 Nephi 28 (1830 chapter XII) follows the order of argument of Stephen
Chapin's *The Immoral Tendency of Error in Sentiment* (Amherst, 1809): a doctrine proved in three
parts, then seven points of "improvement". BOM-130 compared wording and meaning only; this
compares the order of the argument, against a baseline of period sermons. Every outline is
**simulated reading by an AI model** (``lab.judge``); this module writes the questions, reads the
answers and scores them, and calls no hosted model itself (points are embedded with the passage
index's local model, as ``semantic.skeleton`` does).

1. **Texts.** The target is 2 Nephi 28 (``target``, unmasked: the quotations are part of the
   argument); the whole 1830 chapter XII (``chapter_1830``) and an Alma window (``decoy``) go
   through the same code. Chapin's sermon is cut between two pinned markers (``chapin``): the
   Google front page and the dismissal council's minutes after it are not the sermon. *Scripture
   Inquiry* (1828) is the positive neighbour, capped at ``si_max_blocks`` blocks. The baseline is
   ``baseline.universalism`` seeded works from the BOM-130 topic controls of 1780-1829 and
   ``baseline.sermons`` seeded ``sermon_devotional`` works of ``year_min`` to ``year_max``, all
   kept copies of ``min_words`` to ``max_words`` words.
2. **Outlines.** Three variants, each its own job file, all reported. ``blocks``: every
   ``block_words``-word block, at most ``max_points`` points each. ``whole`` (the owner's first
   choice to decide): the whole text at once, at most ``max_points`` points, the grain of the
   reader's "3 + 7". ``anchored`` (deciding since 2026-11-27, after ``whole`` failed its check:
   a scrambled copy came out in its original order, so the model's list order is not the
   text's): the whole text with a numbered marker every ``anchor_words`` words; each point names
   the marker where the passage makes it, and the points are put in marker order. ``variants``
   says which are run and ``deciding_variant`` which one gives the answer.
3. **Alignment.** Points match when their cosine reaches the ``point_match_quantile`` quantile of
   cosines between points of different baseline texts. Texts are scored by Smith-Waterman, and
   order is tested by ``shuffles`` shuffles of the aligned span (``semantic.skeleton.compare``).
4. **Known-answer check.** A seeded baseline sermon is reworded block by block in the same order
   (simulated writing). The rewording must find that sermon first in the baseline at order p at
   most ``ka.bar_p``; the rewording with its paragraphs scrambled must not reach that p. Nothing
   is scored in a variant whose check is not passed.
5. **Verdict** (``verdict``). Chapin stands out only if first against the baseline with order p
   at most ``max_order_p``; "no" if outside the top ``no_share`` of the group; otherwise "cannot
   tell". ``p_floor`` reports the smallest p the shuffle can give an aligned span of that length
   (four points: about 0.04), so a "cannot tell" from a short span is not misread.

The card, written first, is ``data/private/lab/owner/2026-11-27-sermon-outline/card.md``;
settings are ``lab.sermon_outline``. Jobs and outlines quote or paraphrase the texts (some of
them Harvard volumes) and stay on local disk (``data/corpus/lab/sermon_outline/``); the reworded
check texts stay in the private card folder; ``data/lab/reruns/sermon_outline/`` holds ids,
ranks, p-values and counts only. Each job file is asked with ``lab.judge run``; the commands
print the exact lines.

Usage::

    python -m lab.sermon_outline jobs        # texts, outline and rewording jobs
    python -m lab.sermon_outline check-jobs  # after the rewording answers: the check's jobs
    python -m lab.sermon_outline check       # -> data/lab/reruns/sermon_outline/check.json
    python -m lab.sermon_outline run         # -> data/lab/reruns/sermon_outline/result.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
from pathlib import Path

import numpy as np

from lab import door
from lab.nephi28_sources import (
    _plain,
    edition,
    find_copies,
    keepers,
    rank_against,
    seqs,
    topic_controls,
)
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config
from semantic import skeleton

CARD = NOTES / "owner" / "2026-11-27-sermon-outline"  # private: the card and the check's texts
WORK = FAST / "sermon_outline"  # local: jobs and outlines quote or paraphrase the texts
OUT = REGISTRY / "reruns" / "sermon_outline"  # public: ids, ranks, p-values, counts
VARIANTS = ("blocks", "whole", "anchored")
TARGETS = ("target", "chapter_1830", "decoy")
NAMED = ("chapin", "scripture_inquiry")
FILES = {
    "texts": WORK / "texts.json",
    "reword": CARD / "jobs_reword.jsonl",
    "reword_answers": CARD / "answers_reword.jsonl",
    "check": CARD / "jobs_check.jsonl",
    "check_answers": CARD / "answers_check.jsonl",
    "check_texts": CARD / "check_texts.json",
    "check_result": OUT / "check.json",
    "result": OUT / "result.json",
}

OUTLINE = """Read the passage below and list, in the order the passage makes them, at most {n} \
points of its argument: what it sets out to prove, the reasons and proofs it gives, objections \
it answers, and the uses or lessons it draws from them. Write each point as one short plain \
sentence. Replace every personal name, people and place name with a role or description ("a \
prophet", "the people", "the city"). Do not copy the passage's own numbering. If the passage \
makes no argument (title page, list, table, index, or a story only), reply with the single word \
NONE.

Reply with the points only, one per line, each line starting with "- ".

Passage:
{text}"""

ANCHORED = """Read the passage below. Numbered markers in square brackets, [1], [2], [3] and so \
on, divide it into sections. List at most {n} points of its argument: what it sets out to prove, \
the reasons and proofs it gives, objections it answers, and the uses or lessons it draws from \
them. Write each point as one short plain sentence and end it with the number of the marked \
section where the passage makes it, in square brackets, as in "- The speaker warns against \
pride. [7]". Replace every personal name, people and place name with a role or description ("a \
prophet", "the people", "the city"). Do not copy the passage's own numbering. If the passage \
makes no argument (title page, list, table, index, or a story only), reply with the single word \
NONE.

Reply with the points only, one per line, each line starting with "- ".

Passage:
{text}"""

REWORD = """Rewrite the passage below in your own words. Keep every point of its argument, in \
the same order, and about the same length; change the wording of every sentence and do not \
quote it. Write it in paragraphs of two to four sentences, with a blank line between \
paragraphs. Reply with the rewritten passage only.

Passage:
{text}"""


def settings(cfg: dict) -> dict:
    """``lab.sermon_outline``, its variant choice checked."""
    c = cfg["lab"]["sermon_outline"]
    chosen = list(c["variants"])
    if not set(chosen) <= set(VARIANTS) or c["deciding_variant"] not in chosen:
        msg = f"variants {chosen} must be among {VARIANTS} and hold deciding_variant"
        raise SystemExit(f"lab.sermon_outline: {msg}")
    return c


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def job_file(name: str) -> Path:
    return WORK / f"jobs_{name}.jsonl"


def answer_file(name: str) -> Path:
    return WORK / f"answers_{name}.jsonl"


def write_jobs(path: Path, jobs: list[dict]) -> None:
    out(path).write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))


def ask(jobs: Path, answers: Path, model: str) -> str:
    """The ``lab.judge`` line that asks a job file (simulated reading by an AI model)."""
    return f"python -m lab.judge run {jobs} {answers} --model {model}"


# ---- pinned rules (tested) ----------------------------------------------------------------


def trim(text: str, start: str, end: str) -> str:
    """The text from the first ``start`` marker through the first ``end`` marker after it, both
    kept. A missing marker is an error, never a silently uncut text."""
    i = text.find(start)
    if i < 0:
        raise ValueError(f"start marker not found: {start!r}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise ValueError(f"end marker not found after the start: {end!r}")
    return text[i : j + len(end)]


def match_threshold(cos, q: float) -> float:
    """The point-match cosine: the ``q`` quantile of the cosines between unrelated points."""
    a = np.asarray(cos, dtype=np.float64).ravel()
    if not a.size:
        raise ValueError("no cosines between unrelated points")
    return float(np.quantile(a, q))


def unrelated_cosines(vec: dict[str, np.ndarray]) -> np.ndarray:
    """Cosines between every point of one text and every point of another, each pair once."""
    keys = sorted(k for k, v in vec.items() if len(v))
    parts = [(vec[a] @ vec[b].T).ravel() for i, a in enumerate(keys) for b in keys[i + 1 :]]
    return np.concatenate(parts) if parts else np.zeros(0)


def p_floor(span: int, shuffles: int) -> float:
    """The order p expected when only the true order of an aligned span of ``span`` points
    reaches its score: (1 + shuffles / span!) / (shuffles + 1). With 1,000 shuffles, four points
    (24 orders) give about 0.043, so p cannot reach 0.01; five give about 0.009."""
    if span < 2:
        return 1.0
    return min(1.0, (1 + shuffles / math.factorial(span)) / (shuffles + 1))


def verdict(rank: int | None, p: float | None, n: int, c: dict) -> str:
    """The card's rule for a text placed ``rank`` of ``n`` (itself and the baseline): "stands
    out" only if first with order p at most ``max_order_p``; "no" if outside the top
    ``no_share``; otherwise "cannot tell". No order p (nothing aligned) counts as 1."""
    if rank is None or n < 1:
        return "not placed"
    if rank == 1 and (1.0 if p is None else p) <= c["max_order_p"]:
        return "stands out"
    if rank / n > c["no_share"]:
        return "no"
    return "cannot tell"


def ka_passed(rank: int | None, p: float | None, p_mixed: float | None, bar: float) -> bool:
    """The check: the rewording finds its sermon first at order p at most ``bar``, and the
    scrambled rewording does not reach ``bar`` (no p means nothing aligned: not reached)."""
    same = rank == 1 and p is not None and p <= bar
    mixed = p_mixed is None or p_mixed > bar
    return bool(same and mixed)


def scramble(paras: list[str], seed) -> list[str]:
    """The paragraphs in a seeded random order, never the original one (a shuffle that comes
    out unchanged is turned by one place)."""
    res = list(paras)
    if len(res) < 2:
        return res
    random.Random(seed).shuffle(res)
    if res == list(paras):
        res = res[1:] + res[:1]
    return res


def paragraphs(text: str) -> list[str]:
    """Paragraphs split at blank lines, inner white space made single."""
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if p.strip()]


def place(score: float, p: float | None, span: int, others: list[float], c: dict) -> dict:
    """A text's place against the baseline's scores (ties counted against it), the floor on its
    order p, and the card's verdict."""
    n = len(others) + 1
    rank = rank_against(score, np.asarray(others, dtype=np.float64), member=False)
    floor = p_floor(span, c["shuffles"])
    return {
        "rank": rank,
        "of": n,
        "score": round(float(score), 4),
        "order_p": None if p is None else round(float(p), 6),
        "aligned_span": span,
        "p_floor": round(floor, 6),
        "p_can_reach_bar": floor <= c["max_order_p"],
        "verdict": verdict(rank, p, n, c),
    }


def order_test(a: np.ndarray, b: np.ndarray, thr: float, seed: int, c: dict) -> dict:
    """``semantic.skeleton.compare`` with this test's scores and shuffles: A's points against
    B's, B shuffled within its aligned span; adds the span's length."""
    r = skeleton.compare((a, b, thr, seed, {"skeleton": c}))
    r["span"] = r["b_span"][1] - r["b_span"][0] if "b_span" in r else 0
    return r


def brief(r: dict, c: dict) -> dict:
    """The numbers of one comparison (no text)."""
    return {
        "score": round(float(r["score"]), 4),
        "matched": int(r["matched"]),
        "order_p": None if r["order_p"] is None else round(float(r["order_p"]), 6),
        "span": r["span"],
        "p_floor": round(p_floor(r["span"], c["shuffles"]), 6),
    }


def pair_seed(cfg: dict, *names: str) -> int:
    """The shuffle seed of one comparison, derived by name as ``semantic.skeleton`` does."""
    key = ":".join(str(x) for x in (cfg["lab"]["sermon_outline"]["shuffle_seed"], *names))
    return config.derive_seed(key, cfg)


# ---- jobs ---------------------------------------------------------------------------------


def split_id(job_id: str) -> tuple[str, str, int, int]:
    """``variant|name|i|n`` -> (variant, text name, block i, blocks n)."""
    parts = job_id.split("|")
    return parts[0], "|".join(parts[1:-2]), int(parts[-2]), int(parts[-1])


def anchor(words: list[str], every: int) -> str:
    """The words with a marker ``[1]``, ``[2]``, ... before every ``every``-word section."""
    secs = [words[i : i + every] for i in range(0, len(words), every)]
    return " ".join(f"[{k}] " + " ".join(w) for k, w in enumerate(secs, 1))


_MARK = re.compile(r"\s*\[(\d+)(?:\s*[,;\-\u2013]\s*\d+)*\]\s*\.?\s*$")


def in_marker_order(points: list[str]) -> tuple[list[str], int]:
    """Anchored points with their markers taken off, put in marker order (ties keep the reply's
    order), and the number dropped for naming no marker. A point naming several sections
    ("[3, 4]", "[3-5]") is placed at the first, where it starts."""
    got, dropped = [], 0
    for i, pt in enumerate(points):
        m = _MARK.search(pt)
        if not m:
            dropped += 1
            continue
        got.append((int(m.group(1)), i, pt[: m.start()].strip()))
    return [t for _, _, t in sorted(got)], dropped


def outline_jobs(texts: dict[str, str], variant: str, c: dict) -> list[dict]:
    """One outline job per ``block_words`` block (``blocks``) or per whole text (``whole``), ids
    ``variant|name|i|n``. Texts go without titles; the prompt names no claim and no source."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    jobs = []
    for name, text in texts.items():
        words = text.split()
        if not words:
            continue
        if variant == "blocks":
            parts = skeleton.cut(words, c["block_words"])
        elif variant == "anchored":
            parts = [anchor(words, c["anchor_words"])]
        else:
            parts = [" ".join(words)]
        for i, part in enumerate(parts):
            form = ANCHORED if variant == "anchored" else OUTLINE
            prompt = form.format(n=c["max_points"], text=part)
            jobs.append({"id": f"{variant}|{name}|{i}|{len(parts)}", "prompt": prompt})
    return jobs


def outlines_of(jobs: list[dict], answers: list[dict], max_points: int) -> dict:
    """Each text's points in order, once every one of its jobs is answered; texts with an open
    job are counted, not scored. A reply that cannot be read is a block with no points, listed
    in ``unreadable``. Anchored replies are put in marker order; points naming no marker are
    dropped and counted in ``unanchored``."""
    order: dict[str, list[str]] = {}
    for j in jobs:
        order.setdefault(split_id(j["id"])[1], []).append(j["id"])
    reply = {a["id"]: a["reply"] for a in answers}
    points: dict[str, list[str]] = {}
    open_: dict[str, int] = {}
    unreadable: list[str] = []
    unanchored = 0
    for name, ids in order.items():
        missing = [i for i in ids if i not in reply]
        if missing:
            open_[name] = len(missing)
            continue
        got: list[str] = []
        for i in sorted(ids, key=lambda x: split_id(x)[2]):
            pts = skeleton.parse_events(reply[i], max_points)
            if pts is None:
                unreadable.append(i)
            elif split_id(i)[0] == "anchored":
                pts, lost = in_marker_order(pts)
                unanchored += lost
            got += pts or []
        points[name] = got
    return {"points": points, "open": open_, "unreadable": unreadable, "unanchored": unanchored}


def again_jobs(blocks: list[dict], c: dict) -> list[dict]:
    """``reextract_blocks`` seeded block jobs asked a second time, for the agreement figure."""
    n = min(c["reextract_blocks"], len(blocks))
    pick = random.Random(f"{c['ka']['seed']}:again").sample(blocks, n)
    return [{"id": f"again|{j['id']}", "prompt": j["prompt"]} for j in pick]


# ---- texts --------------------------------------------------------------------------------


def span_text(span: list[int]) -> str:
    """1830 paragraphs ``span`` (first and last seq), unmasked, in order."""
    ed = edition()
    return " ".join(ed[s]["text"] for s in sorted(seqs(span)))


def library_text(work_id: str, reg: dict[str, dict]) -> str | None:
    """A library volume's text; None when it has no readable file (not attempted)."""
    cat = door.catalog({work_id})
    if work_id not in cat:
        return None
    try:
        return door.text_of(cat[work_id] | reg.get(work_id, {}))
    except (OSError, TypeError):
        return None


def genre_of(row: dict) -> str:
    return (row.get("genre") or "").split(",")[0]


def draw_baseline(cfg: dict, reg: dict[str, dict], exclude: set[str]) -> list[dict]:
    """The seeded baseline: ``universalism`` works from the BOM-130 topic controls of 1780-1829
    and ``sermons`` sermon_devotional works of ``year_min`` to ``year_max``, every one a kept,
    readable copy of ``min_words`` to ``max_words`` words."""
    from lab.ntwording import draw, eligible

    b = settings(cfg)["baseline"]
    late = set(topic_controls(cfg["lab"]["nephi28_sources"], reg)["late"])
    rows = eligible(cfg, lambda r: b["min_words"] <= (r["words"] or 0) <= b["max_words"])
    pool = [r for r in rows if r["work_id"] in late]
    uni = draw(pool, b["universalism"], f"{b['seed']}:universalism", exclude)
    taken = exclude | {r["work_id"] for r in uni}
    lo, hi = b["year_min"], b["year_max"]
    pool = [r for r in rows if genre_of(r) == "sermon_devotional" and lo <= r["year"] <= hi]
    serm = draw(pool, b["sermons"], f"{b['seed']}:sermons", taken)
    res = [{**r, "group": "universalism"} for r in uni]
    return res + [{**r, "group": "sermons"} for r in serm]


def gather(cfg: dict) -> dict[str, dict]:
    """Every text of the test: the targets, Chapin, Scripture Inquiry and the drawn baseline.
    Each entry holds its text (None when unreadable: not attempted) and its word count."""
    c = settings(cfg)
    ch = c["chapin"]
    raw = Path(ch["path"]).read_text(encoding="utf-8", errors="replace")
    texts: dict[str, dict] = {
        "target": {"kind": "target", "text": span_text(c["target"])},
        "chapter_1830": {"kind": "target", "text": span_text(c["chapter_1830"])},
        "decoy": {"kind": "target", "text": span_text(c["decoy"])},
        "chapin": {"kind": "named", "text": trim(raw, ch["start_marker"], ch["end_marker"])},
    }
    reg = keepers()
    si = library_text(c["scripture_inquiry"], reg)
    cap = c["si_max_blocks"] * c["block_words"]
    texts["scripture_inquiry"] = {
        "kind": "named",
        "work_id": c["scripture_inquiry"],
        "text": " ".join(si.split()[:cap]) if si else None,
    }
    named = find_copies(cfg["lab"]["nephi28_sources"]["named"])
    exclude = set().union(*named.values()) | {c["scripture_inquiry"]}
    for r in draw_baseline(cfg, reg, exclude):
        texts[r["work_id"]] = {
            "kind": "baseline",
            "work_id": r["work_id"],
            "group": r["group"],
            "year": r["year"],
            "text": library_text(r["work_id"], reg),
        }
    for v in texts.values():
        v["words"] = len(v["text"].split()) if v["text"] else 0
        v["status"] = "read" if v["text"] else "unreadable: not attempted"
    return texts


def stored_texts() -> dict:
    if not FILES["texts"].exists():
        raise SystemExit("no texts yet: run `python -m lab.sermon_outline jobs` first")
    return json.loads(FILES["texts"].read_text())


def ka_sermon() -> str:
    """The check's sermon, as the rewording jobs name it."""
    jobs = load(FILES["reword"])
    if not jobs:
        raise SystemExit("no rewording jobs yet: run `python -m lab.sermon_outline jobs` first")
    return split_id(jobs[0]["id"])[1]


def text_summary(texts: dict) -> dict:
    """Each text's kind, id, group, year, words and status (no text)."""
    keep = ("kind", "work_id", "group", "year", "words", "status")
    return {k: {f: v[f] for f in keep if f in v} for k, v in texts.items()}


def build_jobs(cfg: dict) -> dict:
    """The texts, the outline jobs of every variant, the re-asked blocks, and the rewording
    jobs of the check's sermon."""
    c = settings(cfg)
    texts = gather(cfg)
    out(FILES["texts"]).write_text(json.dumps(texts, ensure_ascii=False) + "\n")
    readable = {k: v["text"] for k, v in texts.items() if v["text"]}
    counts: dict[str, int] = {}
    asks = []
    for v in c["variants"]:
        js = outline_jobs(readable, v, c)
        write_jobs(job_file(v), js)
        counts[v] = len(js)
        asks.append(ask(job_file(v), answer_file(v), c["model"]))
        if v == "blocks":
            again = again_jobs(js, c)
            write_jobs(job_file("again"), again)
            counts["again"] = len(again)
            asks.append(ask(job_file("again"), answer_file("again"), c["model"]))
    base = sorted(k for k, v in texts.items() if v["kind"] == "baseline" and v["text"])
    drawn = sum(v["kind"] == "baseline" for v in texts.values())
    if not base:
        raise SystemExit("no readable baseline sermon was drawn")
    x = random.Random(f"{c['ka']['seed']}:sermon").choice(base)
    blocks = skeleton.cut(readable[x].split(), c["block_words"])
    reword = [
        {"id": f"reword|{x}|{i}|{len(blocks)}", "prompt": REWORD.format(text=b)}
        for i, b in enumerate(blocks)
    ]
    write_jobs(FILES["reword"], reword)
    counts["reword"] = len(reword)
    asks.append(ask(FILES["reword"], FILES["reword_answers"], c["model"]))
    return {
        "texts": {k: v["words"] for k, v in texts.items() if v["kind"] != "baseline"},
        "baseline": {"drawn": drawn, "read": len(base)},
        "ka_sermon": x,
        "jobs": counts,
        "ask": asks,
    }


def check_jobs(cfg: dict) -> dict:
    """From the rewording answers: the reworded sermon in order and with its paragraphs
    scrambled (seeded), each written as outline jobs of every variant."""
    c = settings(cfg)
    jobs = sorted(load(FILES["reword"]), key=lambda j: split_id(j["id"])[2])
    ans = {a["id"]: a["reply"] for a in load(FILES["reword_answers"])}
    open_ = [j["id"] for j in jobs if j["id"] not in ans]
    if not jobs or open_:
        raise SystemExit(f"{len(open_)} rewording jobs open (or none written): ask them first")
    same = "\n\n".join(ans[j["id"]].strip() for j in jobs)
    paras = paragraphs(same)
    if len(paras) < 2:
        raise SystemExit("the rewording came back as one paragraph: nothing to scramble")
    mixed = "\n\n".join(scramble(paras, f"{c['ka']['seed']}:scramble"))
    x = split_id(jobs[0]["id"])[1]
    record = {"sermon": x, "same": same, "mixed": mixed, "paragraphs": len(paras)}
    out(FILES["check_texts"]).write_text(json.dumps(record, ensure_ascii=False) + "\n")
    js: list[dict] = []
    for v in c["variants"]:
        js += outline_jobs({"ka_same": same, "ka_mixed": mixed}, v, c)
    write_jobs(FILES["check"], js)
    ask_line = ask(FILES["check"], FILES["check_answers"], c["model"])
    return {"sermon": x, "paragraphs": len(paras), "check_jobs": len(js), "ask": ask_line}


# ---- scoring ------------------------------------------------------------------------------


def prepare(cfg: dict, variant: str, texts: dict) -> dict:
    """A variant's outlines read and embedded, and its point-match threshold from the baseline;
    only the counts while a job is still open."""
    c = settings(cfg)
    got = outlines_of(load(job_file(variant)), load(answer_file(variant)), c["max_points"])
    base = sorted(k for k, v in texts.items() if v["kind"] == "baseline" and v["text"])
    prep = {
        "variant": variant,
        "open": got["open"],
        "unreadable": got["unreadable"],
        "unanchored": got["unanchored"],
        "base": base,
    }
    if got["open"]:
        return prep
    vec = {k: skeleton.embed(p, cfg) for k, p in got["points"].items()}
    prep["base"] = [k for k in base if k in vec]
    cos = unrelated_cosines({k: vec[k] for k in prep["base"]})
    prep["vec"] = vec
    prep["points"] = {k: len(p) for k, p in got["points"].items()}
    prep["unrelated_cosines"] = int(cos.size)
    prep["threshold"] = match_threshold(cos, c["point_match_quantile"])
    return prep


def check_variant(cfg: dict, prep: dict, x: str) -> dict:
    """The known-answer check in one variant: the rewording against the whole baseline, and the
    scrambled rewording against its own sermon."""
    c = settings(cfg)
    v = prep["variant"]
    jobs = [j for j in load(FILES["check"]) if split_id(j["id"])[0] == v]
    got = outlines_of(jobs, load(FILES["check_answers"]), c["max_points"])
    if prep["open"] or got["open"] or not jobs:
        return {
            "status": "not attempted",
            "open": {**prep["open"], **got["open"]},
            "check_jobs": len(jobs),
            "passed": False,
        }
    kv = {k: skeleton.embed(p, cfg) for k, p in got["points"].items()}
    thr, vec, base = prep["threshold"], prep["vec"], prep["base"]
    same = {}
    for k in base:
        same[k] = order_test(kv["ka_same"], vec[k], thr, pair_seed(cfg, v, "ka_same", k), c)
    others = [same[k]["score"] for k in base if k != x]
    rank = rank_against(same[x]["score"], np.asarray(others, dtype=np.float64), member=False)
    mixed = order_test(kv["ka_mixed"], vec[x], thr, pair_seed(cfg, v, "ka_mixed", x), c)
    bar = c["ka"]["bar_p"]
    return {
        "status": "scored",
        "threshold": round(thr, 6),
        "same": {"rank": rank, "of": len(base), **brief(same[x], c)},
        "scrambled": brief(mixed, c),
        "bar_p": bar,
        "unreadable_outlines": len(got["unreadable"]),
        "unanchored_points": got["unanchored"],
        "passed": ka_passed(rank, same[x]["order_p"], mixed["order_p"], bar),
    }


def reliability(cfg: dict, prep: dict) -> dict:
    """The re-asked blocks against their first reading: the share of the shorter outline's
    points the two align (as the skeleton's extractor check)."""
    c = settings(cfg)
    first = {a["id"]: a["reply"] for a in load(answer_file("blocks"))}
    again = {a["id"]: a["reply"] for a in load(answer_file("again"))}
    jobs = load(job_file("again"))
    shares: list[float] = []
    for j in jobs:
        orig = j["id"].split("|", 1)[1]
        if j["id"] not in again or orig not in first:
            continue
        a = skeleton.parse_events(first[orig], c["max_points"]) or []
        b = skeleton.parse_events(again[j["id"]], c["max_points"]) or []
        if not a or not b:
            shares.append(float(len(a) == len(b)))
            continue
        match = (skeleton.embed(a, cfg) @ skeleton.embed(b, cfg).T) >= prep["threshold"]
        al = skeleton.sw_align(match, {"skeleton": c})
        shares.append(al["matched"] / min(len(a), len(b)))
    return {
        "blocks": len(jobs),
        "compared": len(shares),
        "median_agreement": round(float(np.median(shares)), 4) if shares else None,
    }


def run_variant(cfg: dict, prep: dict, x: str, texts: dict) -> dict:
    """One variant: its check, then every target against Chapin, Scripture Inquiry and the
    baseline (nothing is scored if the check is not passed)."""
    c = settings(cfg)
    chk = check_variant(cfg, prep, x)
    res: dict = {
        "check": chk,
        "open": prep["open"],
        "unreadable_outlines": len(prep["unreadable"]),
        "unanchored_points": prep["unanchored"],
    }
    if not chk["passed"]:
        res["stopped"] = "the known-answer check is not passed or not complete; nothing scored"
        return res
    v, vec, thr, base = prep["variant"], prep["vec"], prep["threshold"], prep["base"]
    res["threshold"] = round(thr, 6)
    res["unrelated_cosines"] = prep["unrelated_cosines"]
    res["baseline"] = len(base)
    res["points"] = prep["points"]
    res["targets"] = {}
    for t in TARGETS:
        rows = {k: order_test(vec[t], vec[k], thr, pair_seed(cfg, v, t, k), c) for k in base}
        scores = [rows[k]["score"] for k in base]
        named: dict = {}
        for k in NAMED:
            if k not in vec:
                named[k] = "no text: not attempted"
                continue
            r = order_test(vec[t], vec[k], thr, pair_seed(cfg, v, t, k), c)
            named[k] = place(r["score"], r["order_p"], r["span"], scores, c)
            named[k]["matched"] = int(r["matched"])
        top = [k for _, k in sorted((-rows[w]["score"], w) for w in base)[:10]]
        top_rows = [{"work_id": k, "group": texts[k]["group"], **brief(rows[k], c)} for k in top]
        at_bar = sum((rows[k]["order_p"] or 1.0) <= c["max_order_p"] for k in base)
        res["targets"][t] = {
            "named": named,
            "baseline_top": top_rows,
            "baseline_median_score": round(float(np.median(scores)), 4) if scores else None,
            "baseline_at_bar": at_bar,
        }
    ch = res["targets"]["decoy"]["named"]["chapin"]
    res["decoy_puts_chapin_first"] = isinstance(ch, dict) and ch["rank"] == 1
    tc = res["targets"]["target"]["named"]["chapin"]
    res["verdict"] = tc["verdict"] if isinstance(tc, dict) else "not placed"
    return res


def check(cfg: dict) -> dict:
    """The known-answer check of every variant, and the re-asked blocks' agreement."""
    c = settings(cfg)
    texts, x = stored_texts(), ka_sermon()
    res: dict = {
        "rewording": f"simulated writing by an AI model (lab.judge, model {c['model']})",
        "sermon": x,
        "variants": {},
    }
    for v in c["variants"]:
        prep = prepare(cfg, v, texts)
        res["variants"][v] = check_variant(cfg, prep, x)
        if v == "blocks" and "threshold" in prep:
            res["reliability"] = reliability(cfg, prep)
    return res


def run(cfg: dict) -> dict:
    """Every variant scored; the answer is the deciding variant's verdict for Chapin."""
    c = settings(cfg)
    texts, x = stored_texts(), ka_sermon()
    res: dict = {
        "outlines": f"simulated reading by an AI model (lab.judge, model {c['model']})",
        "rewording": "simulated writing by an AI model, for the known-answer check only",
        "settings": c,
        "texts": text_summary(texts),
        "check_sermon": x,
        "variants_run": list(c["variants"]),
        "deciding_variant": c["deciding_variant"],
        "variants": {},
    }
    for v in c["variants"]:
        prep = prepare(cfg, v, texts)
        res["variants"][v] = run_variant(cfg, prep, x, texts)
        if v == "blocks" and "threshold" in prep:
            res["reliability"] = reliability(cfg, prep)
    d = res["variants"][c["deciding_variant"]]
    res["answer"] = d.get("verdict", "no answer: " + d.get("stopped", "not attempted"))
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["jobs", "check-jobs", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd in ("jobs", "check-jobs"):
        res = build_jobs(cfg) if a.cmd == "jobs" else check_jobs(cfg)
        print(json.dumps(res, indent=1))
        return 0
    res = check(cfg) if a.cmd == "check" else run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    path = FILES["check_result"] if a.cmd == "check" else FILES["result"]
    out(path).write_text(json.dumps(res, indent=1, default=_plain) + "\n")
    if a.cmd == "check":
        print(json.dumps({v: r["passed"] for v, r in res["variants"].items()}))
    else:
        print(json.dumps({"answer": res["answer"], "deciding_variant": res["deciding_variant"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
