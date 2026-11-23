"""BOM-109, third design: where three worlds disagree, with a reader checked as the score uses it.

The second design (``lab.threeworlds2``) asked a model judge whose each marker mention is and what
the passage says of it; its own check missed on 2026-11-22: on made-up passages "what" was 109 of
150 (every miss in a frame where the thing was not the book's people's and the key was arguable),
and two readings of 98 real mentions by one model in two formats agreed on "whose" 0.755 (bar
0.8), mostly the book's people (S) against the author's own world (A) in essays. This design
keeps the second design's machinery (texts, markers, samples, stated values, worlds, siding) and
changes, post hoc where it follows that result:

- the reader is graded on the decisions the score uses: whose as S against not-S; what and
  place only where the key's whose is S; the full six-way and five-way figures are reported
  beside them;
- the key accepts every fair answer of a frame (a future frame: neither or brought);
- a sharper written rule, with worked examples, for the S/A line in essays and histories, and
  fresh made-up passages (new seed, new frames aimed at that line), none of the second design's;
- two independent readers of the real mentions: the main model and a second model, same prompt,
  same format; agreement on S against not-S with a raw and a chance-corrected (kappa) bar;
- Kirchhoff 1943's trait list keyed (``lab.threeworlds3_features``; two traits added) and Roys's
  *Chumayel* (1933) as a Mesoamerican native reference;
- step 1, their way first: the published checklists as their authors read them (Dale and Dale
  via BOM-112, Roper via BOM-113, Coe's short list, Vogel's motifs via amendment 1), reported
  feature by feature beside the attributed reading.

All model reading is **simulated judging by an AI model** (``lab.judge``). Card:
``data/private/lab/owner/2026-11-23-three-worlds-third/card.md``; settings ``lab.three_worlds3``
over ``lab.three_worlds2``. Results hold names, references and numbers; jobs quote passages and
are private.

Usage::

    python -m lab.threeworlds3 texts        # every text incl. Roys; words, hits, samples (10 min)
    python -m lab.threeworlds3 jobs         # judge jobs, check first (private); sizes (5 min)
    python -m lab.threeworlds3 dev          # the check's grading on hand-made answers (seconds)
    python -m lab.threeworlds3 judge-check  # score the judge's check; exit 1 if missed, 2 if open
    python -m lab.threeworlds3 queue        # judge-check, then (only if passed) the long files
    python -m lab.threeworlds3 check        # judge check, world values and the known texts
    python -m lab.threeworlds3 run          # the checks, then (only if passed) the book, Part B
    python -m lab.threeworlds3 manchester   # Manchester reading (b), only if the checks passed
    python -m lab.threeworlds3 replication  # step 1: the published checklists beside ours (1 min)
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from lab import threeworlds2 as tw
from lab import threeworlds3_features as feat3
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "three_worlds3"
CARD = NOTES / "owner" / "2026-11-23-three-worlds-third"
CARD2 = tw.CARD
NE, MS, AM, CT = feat3.WORLDS
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-109 third design)"
CHECK_FILES = ("check", "check_opus")
DALE_RESULT = REGISTRY / "setting" / "dale_checklist" / "result.json"
ROPER_RESULT = REGISTRY / "setting" / "anachronisms" / "result.json"
ROPER_JUDGED = REGISTRY / "setting" / "anachronisms" / "judged.json"
VOGEL_REPORT = tw.OUT / "replication_vogel.json"


# ------------------------------------------------------------------------------ settings


def settings3(cfg: dict) -> dict:
    return cfg["lab"]["three_worlds3"]


def cfg3(cfg: dict) -> dict:
    """The config the second design's functions read (``lab.three_worlds2``), with this design's
    values laid over it and its added texts appended."""
    c = copy.deepcopy(cfg)
    s3 = settings3(cfg)
    merged = {**c["lab"]["three_worlds2"]}
    for k, v in s3.items():
        if k != "texts_add":
            merged[k] = v
    merged["texts"] = {**merged["texts"], **s3["texts_add"]}
    c["lab"]["three_worlds2"] = merged
    return c


@contextlib.contextmanager
def features3():
    """The second design's functions read this design's feature table while inside."""
    saved = (tw.feat, tw.MARKERS, {k: list(v) for k, v in tw._BY_FIRST.items()})
    tw.feat = feat3
    tw.MARKERS = tw.compile_markers()
    tw._BY_FIRST.clear()
    for fid, rows in tw.MARKERS.items():
        for w, c in rows:
            tw._BY_FIRST[w[0]].append((fid, w, c))
    try:
        yield
    finally:
        tw.feat, tw.MARKERS = saved[0], saved[1]
        tw._BY_FIRST.clear()
        tw._BY_FIRST.update(saved[2])


# ------------------------------------------------------------------------------ texts


def roys_text(rel: str, cfg: dict) -> str | None:
    """Roys's translation only: from his chapter I heading to Appendix A (his introduction,
    notes and appendices are an outsider's commentary)."""
    s = settings3(cfg)
    try:
        raw = (FAST / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    a = raw.find(s["roys_start"])
    b = raw.find("\n" + s["roys_end"], a + 1)
    if a < 0 or b < 0:
        return None
    return raw[a:b].strip() or None


def segments_of(t: dict, cfg: dict) -> list[tuple[str | None, str]] | None:
    if t["source"].startswith("roys:"):
        one = roys_text(t["source"][5:], cfg)
        return None if one is None else [(None, one)]
    return tw.segments_of(t, cfg)


def collect(c3: dict) -> tuple[list[dict], dict[str, dict]]:
    """Every text (rule-drawn works with the second design's subject answers, whose question is
    unchanged) and its sampled mentions, under this design's features."""
    texts = tw.all_texts(c3, tw.subject_answers())
    tw._named(c3)
    ments: dict[str, dict] = {}
    for t in texts:
        segs = segments_of(t, c3)
        if segs is not None:
            ments[t["name"]] = tw.mentions_of(t["name"], segs, c3)
    return texts, ments


# ------------------------------------------------------------------------------ the prompt

PROMPT = """You are helping a study read old books. Your answer is recorded as simulated judging \
by an AI model.

The book is about: {subject}.
Feature: {label}.
In the passage below, the words in double brackets [[like this]] are the mention to judge.

Passage:
{passage}

Answer three questions about the bracketed mention only.
1. WHOSE is it in this passage?
   S = the people the book is about (as named above)
   O = other people in the story (strangers, invaders, conquerors, neighbours, traders)
   A = the author's, translator's or reader's own world
   F = a figure of speech, or words quoted from another book
   P = a prophecy, a promise, a wish, or something in the future
   N = nobody: the passage does not give it to any people
   The line between S and A. Many books are essays or histories in which the author speaks in \
his own voice about the people. That voice alone does not make a mention A.
   - Answer S whenever the passage says whether the people the book is about had, made, used, \
lacked or received the thing, even when the author is arguing, reporting evidence (remains, \
ruins, travellers' reports), giving his opinion, or comparing with his own country.
   - Answer A only when the bracketed thing belongs to the author's or reader's own country or \
time (a comparison, an explanation, a note) and the passage does not say whether the people had \
it.
   Worked examples (made-up people and things, not from the study):
   "From the relics in their graves it is plain that the old Tarsenians wore [[bracelets]] of \
shell." -> S, H
   "The Tarsenians knew nothing of [[glass]], as their own songs confess." -> S, L
   "Their halls were as long as the [[churches]] of our own towns." -> A, X
   "They had [[looms]] much like those of our own weavers." -> S, H
2. WHAT does the passage say about it?
   H = they have, make or use it
   L = they lack it (the passage says or argues that they had none, or did not know it)
   B = it was brought to them from outside (by others, from another land), even if they then \
used it
   X = the passage says none of these
   W = the bracketed word does not mean the feature here (another sense of the word)
3. WHERE is the scene?
   M = in the land where the book's main story takes place
   E = somewhere else (another land, or before a journey to the main land)
   U = cannot tell

Reply with one line and nothing else: the three letters separated by commas, for example S,H,M"""


def prompt3(label: str, subject: str, text: str) -> str:
    return PROMPT.format(subject=subject, label=label, passage=text)


# ------------------------------------------------------------------------------ the check

SYN_THINGS = [
    ("horses", "horses"), ("wheat_barley", "barley"), ("obsidian", "obsidian knives"),
    ("turkeys", "turkeys"), ("coins", "silver coins"), ("mounds", "burial mounds"),
    ("elephants", "elephants"), ("cotton", "cotton mantles"), ("canoes", "canoes"),
    ("brass_bronze", "brass vessels"),
]  # fmt: skip
SYN_PEOPLE = ["the Quenari", "the people of Belzor", "the Senuwa", "the children of Ishmar",
              "the Ardani"]  # fmt: skip
SYN_OUTSIDERS = ["the traders of the northern coast", "the bearded sailors",
                 "the soldiers of Captain Ortelo"]  # fmt: skip
# frame: (template, key) ; key: whose (accepted letters; the first is the primary key), what and
# where (accepted letters). What and where are graded only when whose is S. Fair answers in a
# frame are all accepted; the binary grading (S or not) makes O, A, F, P, N equivalent there.
SYN_FRAMES: dict[str, tuple[str, dict[str, str]]] = {
    "n_have": ("Among {P} every household owned [[{T}]], and the elders counted their wealth by "
               "them.", {"whose": "S", "what": "H", "where": "MU"}),
    "n_lack": ("{P} never possessed [[{T}]]; their old men said that no such thing had been seen "
               "in their country since the beginning.", {"whose": "S", "what": "L",
                                                         "where": "MU"}),
    "n_outsiders": ("When {O} came ashore in the country of {P}, they had [[{T}]] with them, and "
                    "the people fled at the sight.", {"whose": "O", "what": "HB",
                                                      "where": "MU"}),
    "n_brought": ("{O} traded [[{T}]] to {P}, who had never known them before; within a "
                  "generation every village of {P} used them.", {"whose": "S", "what": "B",
                                                                 "where": "MU"}),
    "n_elsewhere": ("Before {P} crossed the ocean to this land, while they still lived in the old "
                    "country, they kept [[{T}]] in great numbers.", {"whose": "S", "what": "H",
                                                                      "where": "E"}),
    "n_future": ("A seer of {P} warned that in a later age men from across the ocean would bring "
                 "[[{T}]] among them.", {"whose": "PO", "what": "XB", "where": "MU"}),
    "n_figure": ("The singer compared the stars to [[{T}]] scattered across a dark plain, as the "
                 "old saying goes.", {"whose": "F", "what": "X", "where": "MU"}),
    "n_quoted": ("The scribe of {P} read out a chronicle of a distant empire, which says: 'its "
                 "king gathered [[{T}]] beyond counting.'", {"whose": "FO", "what": "XH",
                                                             "where": "MUE"}),
    "e_have": ("Digging in the old works of {P} has brought up so many [[{T}]] that no one can "
               "doubt they were in common use among them.", {"whose": "S", "what": "H",
                                                             "where": "MU"}),
    "e_lack": ("It is certain that {P} had no [[{T}]]: none has been found in any of their works, "
               "and every traveller agrees on this.", {"whose": "S", "what": "L",
                                                       "where": "MU"}),
    "e_author_own": ("In our own country, as every reader knows, [[{T}]] are to be seen in every "
                     "county; the writer mentions this only to give an idea of the size of the "
                     "market of {P}, which was larger than any of ours.",
                     {"whose": "A", "what": "XH", "where": "MUE"}),
    "e_compare_have": ("Travellers who saw the country before its ruin describe [[{T}]] in the "
                       "hands of {P}, and the writer judges them hardly inferior to ours.",
                       {"whose": "S", "what": "H", "where": "MU"}),
    "e_gloss_lack": ("The writer has looked in vain for any word of theirs answering to our "
                     "[[{T}]]; {P}, it seems, never had the thing itself.",
                     {"whose": "S", "what": "L", "where": "MU"}),
}  # fmt: skip


def synthetic(cfg: dict) -> list[dict]:
    """The made-up passages: ``synthetic_things`` things in every frame; people by seed."""
    s3 = settings3(cfg)
    rng = random.Random(f"{s3['check_seed']}-synthetic")
    things = SYN_THINGS[: s3["synthetic_things"]]
    rows = []
    for fid, thing in things:
        for frame, (tpl, key) in SYN_FRAMES.items():
            p = rng.choice(SYN_PEOPLE)
            o = rng.choice(SYN_OUTSIDERS)
            text = tpl.format(P=p, O=o, T=thing)
            rows.append({"id": f"syn3|{fid}|{frame}", "feature": fid, "frame": frame,
                         "subject": p, "passage": text[0].upper() + text[1:],
                         "key": dict(key)})  # fmt: skip
    return rows


def pooled(t: dict, c3: dict) -> bool:
    """A reference or rule-drawn text whose row enters its world's pooled profile (the rows
    reported apart, contemporary Indians among them, do not)."""
    return bool(t["row"]) and t["row"] in tw.settings(c3)["rows_pooled"].get(t["world"], [])


def real_draw(texts: list[dict], ments: dict[str, dict], cfg: dict) -> list[str]:
    """Real mentions for the two readers: drawn by ``check_seed`` from the sampled mentions the
    score reads before the book (the known texts and the pooled rows of the reference and
    rule-drawn texts; never the book), none of the second design's 100."""
    s3 = settings3(cfg)
    c3 = cfg3(cfg)
    try:
        old = set(json.loads((CARD2 / "jobs_meta.json").read_text())["real_check"])
    except OSError:
        old = set()
    pool = sorted(
        x["id"]
        for t in texts
        if t["role"] in s3["real_check_roles"]
        and (t["role"] == "known" or pooled(t, c3))
        and t["name"] in ments
        for x in ments[t["name"]]["sample"]
        if x["id"] not in old
    )
    rng = random.Random(f"{s3['check_seed']}-real")
    return sorted(rng.sample(pool, min(s3["real_check_n"], len(pool))))


def kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    """Cohen's kappa for two binary readings."""
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else round((po - pe) / (1 - pe), 4)


def _what3(letter: str) -> str:
    return letter if letter in "HL" else "other"


def _share(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def judge_check(meta: dict, answers: dict[str, str], cfg: dict, log: bool = True) -> dict:
    """The judge's check, graded as the score reads the answers; full figures beside."""
    s2, s3 = tw.settings(cfg3(cfg)), settings3(cfg)
    syn = meta["synthetic"]
    got, st = tw.readings([r["id"] for r in syn], answers, log=log)
    whose_b = what_f = place_b = n_s = six = five = 0
    by_frame: dict[str, Counter] = defaultdict(Counter)
    for r in syn:
        p = got.get(r["id"])
        if p is None:
            continue
        k = r["key"]
        key_s = k["whose"][0] == "S"
        ok_w = (p[0] == "S") == key_s
        whose_b += ok_w
        six += p[0] == k["whose"][0]
        five += p[1] == k["what"][0]
        f = by_frame[r["frame"]]
        f["n"] += 1
        f["whose_binary"] += ok_w
        if key_s:
            n_s += 1
            ok_what = p[1] in k["what"]
            ok_place = tw.counts_main(p, s2) == ("M" in k["where"] or "U" in k["where"])
            what_f += ok_what
            place_b += ok_place
            f["what_fair"] += ok_what
            f["place"] += ok_place
        f[f"answer {','.join(p)}"] += 1
    real = meta["real_check"]
    first, st1 = tw.readings(real, answers, log=log)
    second, st2 = tw.readings([i + "#opus" for i in real], answers, log=log)
    both = [i for i in real if i in first and i + "#opus" in second]
    pairs = [(first[i][0] == "S", second[i + "#opus"][0] == "S") for i in both]
    both_s = [i for i in both if first[i][0] == "S" and second[i + "#opus"][0] == "S"]
    what_agree = sum(_what3(first[i][1]) == _what3(second[i + "#opus"][1]) for i in both_s)
    confusion = Counter(f"{first[i][0]}/{second[i + '#opus'][0]}" for i in both
                        if first[i][0] != second[i + "#opus"][0])  # fmt: skip
    by_text = defaultdict(lambda: [0, 0])
    for (a, b), i in zip(pairs, both, strict=True):
        by_text[i.rsplit("|", 2)[0]][0] += a == b
        by_text[i.rsplit("|", 2)[0]][1] += 1
    res: dict = {
        "label": SIMULATED,
        "readers": {"main": s2["judge_model"], "second": s3["second_reader"]},
        "synthetic": {
            **st,
            "keyed_s": n_s,
            "whose_binary_right": whose_b,
            "whose_binary_share": _share(whose_b, st["answered"]),
            "what_fair_right": what_f,
            "what_fair_share": _share(what_f, n_s),
            "place_right": place_b,
            "place_share": _share(place_b, n_s),
            "full_whose_six_way_share": _share(six, st["answered"]),
            "full_what_five_way_share": _share(five, st["answered"]),
            "by_frame": {k: dict(v) for k, v in sorted(by_frame.items())},
        },
        "real": {
            "main": st1,
            "second": {**st2, "asked": len(real)},
            "both": len(both),
            "whose_binary_agree": _share(sum(a == b for a, b in pairs), len(both)),
            "whose_binary_kappa": kappa(pairs),
            "both_s": len(both_s),
            "what_agree_both_s": _share(what_agree, len(both_s)),
            "full_whose_six_way_agree": _share(
                sum(first[i][0] == second[i + "#opus"][0] for i in both), len(both)
            ),
            "full_what_five_way_agree": _share(
                sum(first[i][1] == second[i + "#opus"][1] for i in both), len(both)
            ),
            "whose_disagreements": dict(confusion.most_common()),
            "whose_binary_agree_by_text": {k: f"{a}/{b}" for k, (a, b) in sorted(by_text.items())},
        },  # fmt: skip
    }
    complete = st["answered"] == len(syn) and len(both) == len(real)
    sy, re_ = res["synthetic"], res["real"]
    bars = {
        "synthetic_whose": (sy["whose_binary_share"] or 0) >= s3["judge_bar_whose"],
        "synthetic_what": (sy["what_fair_share"] or 0) >= s3["judge_bar_what"],
        "synthetic_place": (sy["place_share"] or 0) >= s3["judge_bar_place"],
        "real_whose": (re_["whose_binary_agree"] or 0) >= s3["real_bar_whose"],
        "real_whose_kappa": (re_["whose_binary_kappa"] or 0) >= s3["real_kappa_whose"],
        "real_what": re_["both_s"] >= s3["real_min_both_s"]
        and (re_["what_agree_both_s"] or 0) >= s3["real_bar_what"],
    }
    res["bars"] = bars
    res["complete"] = complete
    res["passed"] = bool(complete and all(bars.values()))
    res["state"] = "passed" if res["passed"] else ("open" if not complete else "missed")
    return res


# ------------------------------------------------------------------------------ jobs


def write_jobs(name: str, rows: list[dict]) -> int:
    out(CARD / f"jobs_{name}.jsonl").write_text("".join(json.dumps(j) + "\n" for j in rows))
    return len(rows)


def manchester_mentions(c3: dict, texts: list[dict], labels: dict) -> tuple[list[dict], int]:
    """The Manchester works answered A-D (second design's subject answers) with this design's
    prompt; (jobs, subject questions still open)."""
    from lab import threeworlds2_manchester as mc

    match = mc.cmd_match(c3)
    rows, n_open = [], 0
    for t in mc.manchester_texts(c3, texts, match):
        if t["subject_answer"] is None:
            n_open += 1
            continue
        if t["row"] is None:
            continue
        segs = segments_of(t, c3)
        if segs is None:
            continue
        for x in tw.mentions_of(t["name"], segs, c3)["sample"]:
            rows.append({"id": x["id"], "prompt": prompt3(labels[x["feature"]], t["subject"],
                                                           x["passage"])})  # fmt: skip
    return rows, n_open


def cmd_jobs(cfg: dict) -> dict:
    """check (sonnet: made-up passages and the real mentions), check_opus (the real mentions,
    second reader), then the long files with this design's prompt, the real mentions left out
    of them (their main reading is in the check)."""
    c3 = cfg3(cfg)
    s3 = settings3(cfg)
    texts, ments = collect(c3)
    labels = {f: v[0] for f, v in feat3.FEATURES.items()}
    syn = synthetic(cfg)
    real = real_draw(texts, ments, cfg)
    by_id = {x["id"]: (t, x) for t in texts if t["name"] in ments
             for x in ments[t["name"]]["sample"]}  # fmt: skip
    check = [{"id": r["id"], "prompt": prompt3(labels[r["feature"]], r["subject"], r["passage"])}
             for r in syn]  # fmt: skip
    opus = []
    for i in real:
        t, x = by_id[i]
        q = prompt3(labels[x["feature"]], t["subject"], x["passage"])
        check.append({"id": i, "prompt": q})
        opus.append({"id": i + "#opus", "prompt": q})
    files: dict[str, list[dict]] = {k: [] for k in (*s3["long_files"], "rule_reported")}
    real_set = set(real)
    for t in texts:
        if t["name"] not in ments or (t["role"] == "rule" and t["row"] is None):
            continue
        f = t["role"]
        if f == "rule" and not pooled(t, c3):
            f = "rule_reported"  # contemporary Indians: reported, not pooled; asked last
        for x in ments[t["name"]]["sample"]:
            if x["id"] in real_set:
                continue
            files[f].append(
                {"id": x["id"], "prompt": prompt3(labels[x["feature"]], t["subject"],
                                                  x["passage"])})  # fmt: skip
    man, man_open = manchester_mentions(c3, texts, labels)
    sizes = {"jobs_check.jsonl": write_jobs("check", check),
             "jobs_check_opus.jsonl": write_jobs("check_opus", opus)}  # fmt: skip
    for k, rows in files.items():
        sizes[f"jobs_{k}.jsonl"] = write_jobs(k, rows)
    sizes["jobs_manchester.jsonl"] = write_jobs("manchester", man)
    meta = {"synthetic": syn, "real_check": real}
    out(CARD / "jobs_meta.json").write_text(json.dumps(meta))
    reused = {}
    for k in s3["reused_files"]:
        p = CARD2 / f"jobs_{k}.jsonl"
        reused[str(p)] = sum(1 for _ in p.open()) if p.exists() else None
    per_hour = cfg["lab"]["judge"]["per_hour"]
    hours = {k: round(v / per_hour, 2) for k, v in sizes.items()}
    long_total = sum(sizes[f"jobs_{k}.jsonl"] for k in s3["long_files"])
    late_total = sum(sizes[f"jobs_{k}.jsonl"] for k in s3["late_files"])
    return {
        "questions": sizes,
        "hours_at_per_hour": hours,
        "check_questions": sizes["jobs_check.jsonl"] + sizes["jobs_check_opus.jsonl"],
        "check_hours": round((sizes["jobs_check.jsonl"] + sizes["jobs_check_opus.jsonl"])
                             / per_hour, 2),
        "synthetic": len(syn), "real_check": len(real),
        "long_questions_this_design": long_total,
        "long_hours_this_design": round(long_total / per_hour, 1),
        "late_questions_this_design": late_total,
        "late_hours_this_design": round(late_total / per_hour, 1),
        "reused_second_design_files": reused,
        "reused_hours": round(sum(v or 0 for v in reused.values()) / per_hour, 1),
        "manchester_subject_open": man_open,
        "per_hour": per_hour,
        "models": {"main": tw.settings(c3)["judge_model"], "second": s3["second_reader"]},
        "order": "check (main) and check_opus (second reader); judge-check; then "
        + ", ".join(s3["long_files"]) + "; then the second design's "
        + ", ".join(s3["reused_files"]) + "; then " + ", ".join(s3["late_files"]),
        "labelled": SIMULATED + "; prepared, not run",
    }  # fmt: skip


# ------------------------------------------------------------------------------ answers


def check_answers() -> dict[str, str]:
    return tw.load_answers([CARD / f"answers_{k}.jsonl" for k in CHECK_FILES])


def all_answers(cfg: dict) -> dict[str, str]:
    s3 = settings3(cfg)
    got = tw.load_answers(
        [CARD / f"answers_{k}.jsonl" for k in (*CHECK_FILES, *s3["long_files"], *s3["late_files"])]
    )
    got.update(tw.load_answers([CARD2 / f"answers_{k}.jsonl" for k in ("partb",)]))
    return got  # fmt: skip


def meta_of() -> dict:
    return json.loads((CARD / "jobs_meta.json").read_text())


def cmd_judge_check(cfg: dict) -> dict:
    return judge_check(meta_of(), check_answers(), cfg)


def evaluate(texts: list[dict], ments: dict[str, dict], answers: dict[str, str], meta: dict,
             cfg: dict, log: bool = True) -> dict:  # fmt: skip
    """The judge check, then world values and the known texts (``tw.evaluate`` with this
    design's judge check). Never scores the book."""
    c3 = cfg3(cfg)
    s = tw.settings(c3)
    jc = judge_check(meta, answers, cfg, log)
    ref = [t for t in texts if t["role"] in ("reference", "rule") and t["row"]]
    known = [t for t in texts if t["role"] in ("known", "control")]
    states, status, sig = tw.score_texts(ref + known, ments, answers, c3, log)
    open_refs = [t["name"] for t in ref
                 if pooled(t, c3) and t["name"] in ments and t["name"] not in states]  # fmt: skip
    values = tw.world_values(states, tw.world_rows(texts), c3)
    keep, dropped = tw.kept_features(values)
    res_known = {}
    for t in known:
        n = t["name"]
        if n not in ments:
            res_known[n] = {"role": t["role"], "state": "not attempted (text not held)"}
            continue
        if n not in states:
            res_known[n] = {"role": t["role"], "state": "open", **status[n]}
            continue
        sd = tw.side(states[n], keep, values, c3)
        sd.pop("features")
        row = {"role": t["role"], "own_world": t["world"], "words": ments[n]["words"], **sd,
               "signature": sig[n]}  # fmt: skip
        if t["role"] == "known":
            row["passes"] = tw.known_passes(n, t["world"], sd, s)
        res_known[n] = row
    kn = [t["name"] for t in texts if t["role"] == "known"]
    complete = not open_refs and all("passes" in res_known.get(n, {}) for n in kn)
    passed = bool(complete and jc["passed"] and all(res_known[n]["passes"] for n in kn))
    return {"judge_check": jc, "references_open": open_refs, "features_kept": keep,
            "dropped": dropped, "world_values": values, "dplace_check": tw.dplace_check(values),
            "known": res_known,
            "diaz_passes": res_known.get("bernal_diaz_keatinge_1800", {}).get("passes"),
            "complete": complete,
            "reference_signatures": {n: sig[n] for n in sig if n not in res_known},
            "passed": passed}  # fmt: skip


def cmd_check(cfg: dict) -> dict:
    texts, ments = collect(cfg3(cfg))
    return evaluate(texts, ments, all_answers(cfg), meta_of(), cfg)


def cmd_run(cfg: dict) -> dict:
    c3 = cfg3(cfg)
    texts, ments = collect(c3)
    answers = all_answers(cfg)
    ev = evaluate(texts, ments, answers, meta_of(), cfg)
    res = {"test": "BOM-109 third design (lab; exploratory)", "card": str(CARD / "card.md"),
           "label": SIMULATED, "check": ev}  # fmt: skip
    if not ev["passed"]:
        why = ("the checks are not complete (open answers)"
               if not ev["complete"] or not ev["judge_check"]["complete"]
               else "a known-answer check missed")  # fmt: skip
        res["book_of_mormon"] = f"not scored: {why}"
        return res
    book = tw.score_book(ments, answers, ev["world_values"], ev["features_kept"], c3)
    res["book_of_mormon"] = book
    dates = tw.partb_dates(answers)
    if isinstance(book, dict) and "whole" in book:
        ms_sole = [f for f, v in book["whole"]["features"].items() if v["agrees_with"] == [MS]]
        res["part_b"] = {f: dates.get(f, {"state": "not attempted (no Part B scan for this "
                                                   "feature)"}) for f in ms_sole}  # fmt: skip
        am = [f for f, v in feat3.FEATURES.items() if v[2] == AM]
        res["part_b_1820s_features"] = {f: dates.get(f, {"state": "not attempted"}) for f in am}
    return res


def cmd_manchester(cfg: dict) -> dict:
    """Reading (b) of amendment 1, kept by the owner: the Manchester holdings as the 1820s row,
    with this design's answers; only once the main checks have passed."""
    from lab import threeworlds2_manchester as mc

    c3 = cfg3(cfg)
    texts, ments = collect(c3)
    answers = all_answers(cfg)
    ev = evaluate(texts, ments, answers, meta_of(), cfg, log=False)
    res = {"test": "BOM-109 third design, Manchester reading (b) (lab; exploratory)",
           "label": SIMULATED}  # fmt: skip
    if not ev["passed"]:
        res["state"] = "not scored: the main checks have not passed"
        return res
    match = mc.cmd_match(c3)
    ref = [t for t in texts if t["role"] in ("reference", "rule") and t["row"]]
    states, _st, _sig = tw.score_texts(ref, ments, answers, c3)
    mt = [t for t in mc.manchester_texts(c3, texts, match) if t["row"]]
    for t in mt:
        segs = segments_of(t, c3)
        if segs is not None:
            ments[t["name"]] = tw.mentions_of(t["name"], segs, c3)
    st_b, _s, _g = tw.score_texts(mt, ments, answers, c3)
    open_b = [t["name"] for t in mt if t["name"] in ments and t["name"] not in st_b]
    if open_b or any(t["subject_answer"] is None for t in mc.manchester_texts(c3, texts, match)):
        res["state"] = "open (subject or mention answers missing)"
        res["open"] = len(open_b)
        return res
    am_b = {t["name"]: (AM, t["row"]) for t in mt}
    res["b_holdings_row"] = mc.variant(texts, {**states, **st_b}, am_b, ["manchester"], ments,
                                       answers, c3)  # fmt: skip
    return res


def cmd_queue(cfg: dict, any_hour: bool = False) -> int:
    """The judge's check first; the long files only if it passed (refused otherwise)."""
    from lab import judge

    jc = cmd_judge_check(cfg)
    write(OUT / "judge_check.json", jc)
    print("judge check:", jc["state"], json.dumps(jc["bars"]), flush=True)
    if not jc["passed"]:
        print("refused: the long run waits on a passed judge check", flush=True)
        return 1
    s3 = settings3(cfg)
    model = tw.settings(cfg3(cfg))["judge_model"]
    per_hour = cfg["lab"]["judge"]["per_hour"]
    order = [(CARD / f"jobs_{k}.jsonl", CARD / f"answers_{k}.jsonl") for k in s3["long_files"]]
    order += [(CARD2 / f"jobs_{k}.jsonl", CARD2 / f"answers_{k}.jsonl")
              for k in s3["reused_files"]]  # fmt: skip
    for jobs, answers in order:
        print(f"== {jobs}", flush=True)
        judge.run(jobs, answers, model, per_hour, any_hour)
    with features3():
        c3 = cfg3(cfg)
        texts, _m = collect(c3)
        rows, _open = manchester_mentions(c3, texts, {f: v[0] for f, v in
                                                      feat3.FEATURES.items()})  # fmt: skip
    write_jobs("manchester", rows)
    left = 0
    for k in s3["late_files"]:
        print(f"== {k}", flush=True)
        left += judge.run(CARD / f"jobs_{k}.jsonl", CARD / f"answers_{k}.jsonl", model,
                          per_hour, any_hour)  # fmt: skip
    return 1 if left else 0


# ------------------------------------------------------------------------------ step 1


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except OSError:
        return None


COE_1973 = {"horses": ["horse"], "chariots": ["chariot"], "wheat_barley": ["wheat", "barley"],
            "cattle": ["cattle", "cow", "ox"], "iron_steel": ["iron", "steel"]}  # fmt: skip


def cmd_replication(cfg: dict) -> dict:
    """Step 1, their way first: each published checklist as its authors read it, from the
    modules that reproduced it (no work redone), then feature by feature beside ours."""
    dale = _load(DALE_RESULT) or {}
    dale_items = {i["id"]: i for i in (_load(tw.DALE_ITEMS) or {}).get("items", [])}
    roper = _load(ROPER_RESULT) or {}
    roper_items = (_load(tw.ROPER_ITEMS) or {}).get("items", [])
    judged = _load(ROPER_JUDGED)
    vogel = _load(VOGEL_REPORT)
    ours = _load(OUT / "result.json")
    res: dict = {"label": "step 1 (their way first), read from BOM-112, BOM-113 and amendment "
                          "1 outputs; "
                          + SIMULATED + " where a judge read anything"}  # fmt: skip
    ka = dale.get("known_answer", {})
    res["dale_and_dale_2019"] = {
        "source": "BOM-112, data/lab/setting/dale_checklist/result.json",
        "their_counts_reproduced": ka.get("counts_ok"),
        "headline_as_printed": dale.get("alternatives", {}).get("headline_as_printed"),
        "their_book_codings_second_reader": {k: v for k, v in dale.items()
                                             if k.startswith("check_c")} or "open",
        "their_controls": dale.get("controls") or "open (refused until check C passes)",
    }  # fmt: skip
    res["roper_2025"] = {
        "source": "BOM-113, data/lab/setting/anachronisms/result.json",
        "tally_reproduced": roper.get("roper_totals", {}).get("all"),
        "tally_stated": roper.get("roper_totals", {}).get("stated"),
        "his_verdicts_second_reader": (judged or {}).get("summary", judged) or "open",
    }
    book_counts = roper.get("book_of_mormon", {}).get("all_text", {}).get("counts", {})
    text_counts = {n: v.get("counts", {}) for n, v in roper.get("texts", {}).items()}
    res["coe_1973"] = {
        "source": "his short list of things missing from ancient America; counted by BOM-113",
        "book_of_mormon": {f: {w: book_counts.get(w, 0) for w in ws} for f, ws in COE_1973.items()},
        "controls": {n: {f: sum(c.get(w, 0) for w in ws) for f, ws in COE_1973.items()}
                     for n, c in text_counts.items()
                     if n in ("ss-manuscript-story-1885", "es-1825-view-of-the-hebrews",
                              "gh-1816-late-war", "bernal_diaz_keatinge_1800")},
    }  # fmt: skip
    res["vogel_1986"] = (
        vogel.get("summary", vogel)
        if vogel
        else ("open: jobs_vogel.jsonl (amendment 1, our coding of his prose) not yet answered")
    )
    res["kirchhoff_1943"] = feat3.kirchhoff_coverage()
    roper_by_thing: dict[str, list[str]] = defaultdict(list)
    for it in roper_items:
        roper_by_thing[it.get("thing")].append(it.get("roper_status"))
    book = ours.get("book_of_mormon") if ours else None
    whole = book.get("whole", {}).get("features", {}) if isinstance(book, dict) else {}
    values = (ours or {}).get("check", {}).get("world_values", {})
    rows = {}
    for fid, (_l, _t, kind, _m, prov) in feat3.FEATURES.items():
        pub = []
        for p in prov:
            src, _, arg = p.partition(":")
            if src == "dale" and arg in dale_items:
                i = dale_items[arg]
                pub.append({"source": "Dale and Dale", "item": arg, "direction": i["direction"],
                            "ratio": i["ratio"],
                            "reads": "book matches Mesoamerica" if i["direction"] == "positive"
                            else "book has a thing Mesoamerica lacked"})  # fmt: skip
            elif src == "roper":
                pub.append(
                    {
                        "source": "Roper",
                        "thing": arg,
                        "status": sorted(set(filter(None, roper_by_thing.get(arg, [])))),
                    }
                )
            elif src == "coe1973":
                pub.append({"source": "Coe 1973", "reads": "missing from ancient America; "
                                                           "the book has it"})  # fmt: skip
            elif src == "vogel":
                pub.append(
                    {
                        "source": "Vogel 1986",
                        "chapter": arg,
                        "reads": "an 1820s idea the book shares",
                    }
                )
            elif src == "kirchhoff":
                pub.append({"source": "Kirchhoff 1943", "trait": arg})
        row: dict = {"kind": kind, "published": pub}
        if whole or values:
            v = whole.get(fid)
            row["ours"] = {
                "book_whole": v["value"] if v else "not stated or not kept",
                "agrees_with": v["agrees_with"] if v else [],
                "world_values": {w: values.get(fid, {}).get(w, {}).get("value")
                                 for w in feat3.WORLDS},
            }  # fmt: skip
            row["parts_ways"] = parts_ways(pub, row["ours"])
        rows[fid] = row
    res["by_feature"] = rows
    res["ours_state"] = (
        "scored"
        if whole
        else "not scored yet: the third design's checks have not passed or not run"
    )
    return res


def parts_ways(pub: list[dict], ours: dict) -> list[str]:
    """Where a published reading and the attributed reading disagree, in words."""
    notes = []
    agrees = ours.get("agrees_with") or []
    for p in pub:
        if p["source"] == "Dale and Dale" and p["direction"] == "positive" and agrees and \
                MS not in agrees:  # fmt: skip
            notes.append(
                f"Dales {p['item']} credit a Mesoamerican match; attributed, the book "
                f"agrees with {'+'.join(agrees)}"
            )
        if p["source"] == "Dale and Dale" and p["direction"] == "negative" and \
                ours["book_whole"] == "absent":  # fmt: skip
            notes.append(
                f"Dales {p['item']} count the book as having it; attributed, its people "
                "are stated without it"
            )
        if p["source"] == "Coe 1973" and ours["book_whole"] == "absent":
            notes.append(
                "Coe counts it as in the book; attributed, its people are stated without it"
            )
        if p["source"] == "Roper" and "confirmed" in p.get("status", []) and \
                ours["world_values"].get(MS) == "absent":  # fmt: skip
            notes.append(
                f"Roper marks {p['thing']} confirmed; the Mesoamerican texts, "
                "attributed, give their people none"
            )
    return notes


# ------------------------------------------------------------------------------ texts command


def cmd_texts(cfg: dict) -> dict:
    c3 = cfg3(cfg)
    texts, ments = collect(c3)
    res: dict = {"texts": {}, "not_attempted": []}
    for t in texts:
        m = ments.get(t["name"])
        if m is None:
            res["not_attempted"].append(t["name"])
            continue
        res["texts"][t["name"]] = {"role": t["role"], "world": t["world"], "row": t["row"],
                                   "source": t["source"], "words": m["words"],
                                   "marker_hits": sum(m["hits"].values()),
                                   "sampled": len(m["sample"])}  # fmt: skip
    per_new = {f: {"texts_with_hits": sum(1 for n, m in ments.items() if m["hits"].get(f)
                                          and n != "book_of_mormon"),
                   "hits": sum(m["hits"].get(f, 0) for n, m in ments.items()
                               if n != "book_of_mormon")}
               for f in feat3.ADDED}  # fmt: skip
    res["added_features"] = per_new
    res["kirchhoff"] = feat3.kirchhoff_coverage()
    res["provenance"] = provenance()
    res["sampled_by_role"] = dict(Counter(t["role"] for t in texts if t["name"] in ments
                                          for _ in ments[t["name"]]["sample"]))  # fmt: skip
    return res


def provenance() -> dict:
    """Every code resolves: the second design's codes as there; Kirchhoff's against his table."""
    p2 = tw.check_provenance()
    bad = [b for b in p2["unresolved"] if ":kirchhoff:" not in b]
    for fid, spec in feat3.FEATURES.items():
        for p in spec[4]:
            src, _, arg = p.partition(":")
            if src == "kirchhoff" and (arg not in feat3.KIRCHHOFF):
                bad.append(f"{fid}:{p}")
    by_source = Counter(p.split(":")[0] for spec in feat3.FEATURES.values() for p in spec[4])
    return {"features": len(feat3.FEATURES), "unresolved": bad, "codes_by_source": dict(by_source),
            "by_kind": dict(Counter(v[2] for v in feat3.FEATURES.values()))}  # fmt: skip


# ------------------------------------------------------------------------------ development


def dev_case(cfg: dict) -> dict:
    """The check's grading on hand-made answers: the key (must pass), everything "S,H,M" (must
    miss), and the second design's failure pattern (fair but off-key answers in non-S frames:
    must not count against the reader)."""
    syn = synthetic(cfg)
    meta = {"synthetic": syn, "real_check": []}
    key = {r["id"]: f"{r['key']['whose'][0]},{r['key']['what'][0]},{r['key']['where'][0]}"
           for r in syn}  # fmt: skip
    naive = {r["id"]: "S,H,M" for r in syn}
    fair = dict(key)
    for r in syn:
        if r["frame"] == "n_future":
            fair[r["id"]] = "P,B,M"
        if r["frame"] == "e_author_own":
            fair[r["id"]] = "A,H,U"
    return {"label": "development run on hand-made answers; not the check",
            "with_key": judge_check(meta, key, cfg, log=False)["synthetic"],
            "naive": judge_check(meta, naive, cfg, log=False)["synthetic"],
            "fair_off_key": judge_check(meta, fair, cfg, log=False)["synthetic"]}  # fmt: skip


# ------------------------------------------------------------------------------ command line


def write(path: Path, res: dict) -> None:
    out(path).write_text(json.dumps(tw.stamp(res), indent=1, default=str) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["texts", "jobs", "dev", "judge-check", "queue", "check", "run",
                                    "manchester", "replication"])  # fmt: skip
    ap.add_argument("--any-hour", action="store_true")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "queue":
        return cmd_queue(cfg, a.any_hour)
    with features3():
        if a.cmd == "texts":
            res = cmd_texts(cfg)
            write(OUT / "texts.json", res)
            print(json.dumps({k: v for k, v in res.items() if k != "texts"}, indent=1))
        elif a.cmd == "jobs":
            res = cmd_jobs(cfg)
            write(OUT / "jobs.json", res)
            print(json.dumps(res, indent=1))
        elif a.cmd == "dev":
            res = dev_case(cfg)
            write(OUT / "dev_hand_answers.json", res)
            print(json.dumps(res, indent=1))
        elif a.cmd == "judge-check":
            res = cmd_judge_check(cfg)
            write(OUT / "judge_check.json", res)
            print(json.dumps({k: res[k] for k in ("state", "bars")}, indent=1))
            print(json.dumps({k: v for k, v in res["synthetic"].items() if k != "by_frame"}))
            print(json.dumps({k: v for k, v in res["real"].items()
                              if k != "whose_binary_agree_by_text"}))  # fmt: skip
            return 0 if res["passed"] else (2 if res["state"] == "open" else 1)
        elif a.cmd == "check":
            res = cmd_check(cfg)
            write(OUT / "check.json", res)
            print(
                "judge check:",
                res["judge_check"]["state"],
                "| references open:",
                len(res["references_open"]),
                "| kept:",
                len(res["features_kept"]),
            )
            for n, t in res["known"].items():
                print(
                    f"  {n:40s} {t.get('agree')} -> {t.get('sides_with')} lead "
                    f"{t.get('lead')} passes {t.get('passes')}"
                )
            print("Diaz passes:", res["diaz_passes"], " passed:", res["passed"])
        elif a.cmd == "run":
            res = cmd_run(cfg)
            write(OUT / "result.json", res)
            b = res["book_of_mormon"]
            print("checks passed:", res["check"]["passed"], "| book:",
                  b if isinstance(b, str) else b.get("verdict"))  # fmt: skip
        elif a.cmd == "manchester":
            res = cmd_manchester(cfg)
            write(OUT / "manchester.json", res)
            print(res.get("state") or res["b_holdings_row"].get("book_verdict"))
        else:
            res = cmd_replication(cfg)
            write(OUT / "replication.json", res)
            print(json.dumps({k: v for k, v in res.items() if k != "by_feature"}, indent=1,
                             default=str)[:4000])  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
