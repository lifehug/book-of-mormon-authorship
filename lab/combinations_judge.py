"""BOM-123, second design (post hoc, the last allowed): a model judge reads a wider passage.

The first design (``lab/combinations.py``) labelled each use of "secret combination(s)" by a word
rule on 30 words each side, and its known-answer check missed: in anti-Masonic books the phrase is
an epithet whose referent is the book's subject, with no Masonic word within 30 words. Here the
referent is read by a model (**simulated judging by an AI model**, ``lab/judge.py``) from a passage
of ``lab.combinations.v2.window_words`` words each side, found again in the source text by the
same phrase rule. The prompt carries neither the title nor the year: the check sample is defined
by titles, and every Masonic-titled use is from 1827 on, so either would give the answer away.

Three private question files go into the card's folder: ``jobs_check.jsonl`` (the first design's
titled sample: Masonic-, trade- and politics-titled works), ``jobs_bom.jsonl`` (every Book of
Mormon use and the control uses: Bible-style books, marked translations, Joseph Smith's other
texts), ``jobs_sample.jsonl`` (the seeded per-year sample of library and newspaper uses, the same
rule and seed as the first design's 826 questions). They are run by ``lab/judge.py`` into
``answers_check.jsonl``, ``answers_bom.jsonl`` and ``answers_sample.jsonl`` beside them. The check
counts near-identical passages once (``dedup_words`` normalised words each side, ``dedup_overlap``
shared) and its bars are those of the card; ``score`` refuses unless the check passed. The test
card is ``data/private/lab/owner/2026-11-22-secret-combinations-2/card.md``; settings are
``lab.combinations.v2``. The public result holds ids, years, labels and counts, no text.

Usage::

    python -m lab.combinations_judge jobs    # re-read the uses with the wide window -> 3 jobs files
    python -m lab.combinations_judge check   # known-answer check from answers_check.jsonl (prints)
    python -m lab.combinations_judge score   # check, then -> result_judged.json (refuses on a miss)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab import combinations as c1
from lab import door
from lab.paths import out
from metadata import config

CARD = Path("data/private/lab/owner/2026-11-22-secret-combinations-2")
RESULT = c1.OUT / "result_judged.json"
UNPARSED_LOG = Path("logs/lab/combinations_judge_unparsed.jsonl")
LABELS = [
    "freemasonry",
    "other_society",
    "political",
    "trade",
    "crime",
    "religious",
    "other",
    "unclear",
]
CONTROL_GROUPS = ("control_bible_style", "control_js", "translations")


def v2(cfg: dict) -> dict:
    return cfg["lab"]["combinations"]["v2"]


def v2_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(v2(cfg), sort_keys=True).encode()).hexdigest()


# ------------------------------------------------------------------------------ passages


def wide_uses(low: str, d: dict, w: int) -> list[dict]:
    """Every use of the phrase in normalised text with ``w`` words each side and its position."""
    if "ombinat" not in low:
        return []
    rx, exact = re.compile(d["phrase"]), re.compile(d["exact"])
    got = []
    for m in rx.finditer(low):
        left = low[max(0, m.start() - 12 * w) : m.start()].split()[-w:]
        right = low[m.end() : m.end() + 12 * w].split()[:w]
        got.append(
            {
                "start": m.start(),
                "exact": bool(exact.fullmatch(m.group(0))),
                "left": " ".join(left),
                "mid": m.group(0),
                "right": " ".join(right),
            }
        )
    return got


def agrees(wide: dict, short: dict, n: int = 10) -> bool:
    """The wide use is the scan's use: same phrase, same ``n`` words next to it on both sides."""
    if wide["mid"] != short["mid"]:
        return False
    sl, sr = short["left"].split()[-n:], short["right"].split()[:n]
    wl, wr = wide["left"].split(), wide["right"].split()
    return (not sl or wl[-len(sl) :] == sl) and wr[: len(sr)] == sr


def prompt(left: str, mid: str, right: str) -> str:
    """The question: the first design's labels, no title, no year; reply = the label only."""
    passage = f"{left} [{mid}] {right}"
    return (
        "A printed text uses the phrase marked in square brackets. What does the phrase refer to "
        "in this passage? Answer with exactly one label: freemasonry; other_society (a named or "
        "described secret society other than the Freemasons); political (a faction, party or "
        "conspiracy against a government); trade (a combination of merchants, masters or "
        "workmen); crime (robbers, murderers, a criminal band); religious; other; unclear.\n\n"
        "Passage:\n" + passage + "\n\nReply with the label only."
    )


def parse_reply(reply: str | None) -> str | None:
    """The label, or None when the reply is not one of the labels (logged, never counted)."""
    if not reply:
        return None
    first = reply.strip().splitlines()[0] if reply.strip() else ""
    t = first.strip().strip("*`\"'.:;!,() ").lower()
    t = re.sub(r"^label\s*:\s*", "", t)
    t = re.sub(r"[\s-]+", "_", t)
    if t in LABELS:
        return t
    if t.startswith("other_society"):  # a label followed by more words
        return "other_society"
    m = re.match(r"[a-z]+", t)
    return m.group(0) if m and m.group(0) in LABELS else None


# ------------------------------------------------------------------------------ dedup


def dedup_key(left: str, right: str, n: int) -> list[str]:
    """``n`` words each side of the phrase: lower-case, letters only, long s read as s."""

    def words(s: str) -> list[str]:
        return re.findall(r"[a-z]+", s.lower().replace("f", "s"))

    return (words(left)[-n:] if n else []) + words(right)[:n]


def overlap(a: list[str], b: list[str]) -> float:
    """Share of key words shared (multiset), over the longer key."""
    if not a or not b:
        return 0.0
    return sum((Counter(a) & Counter(b)).values()) / max(len(a), len(b))


def group_passages(items: list[tuple[str, list[str]]], thr: float) -> list[list[str]]:
    """Near-identical uses grouped as one passage: in id order, each use joins the first group
    whose first member it shares at least ``thr`` of its key words with, else starts a group."""
    groups: list[tuple[list[str], list[str]]] = []
    for i, key in sorted(items):
        for rep, members in groups:
            if overlap(key, rep) >= thr:
                members.append(i)
                break
        else:
            groups.append((key, [i]))
    return [m for _, m in groups]


def passage_label(ids: list[str], labels: dict[str, str | None]) -> str | None:
    """The label most of a passage's copies got; ties: the copy with the smallest id. Copies with
    no parsed label are ignored; a passage with none is not counted."""
    got = [(i, labels.get(i)) for i in sorted(ids) if labels.get(i)]
    if not got:
        return None
    n = Counter(lab for _, lab in got)
    top = max(n.values())
    return next(lab for _, lab in got if n[lab] == top)


# ------------------------------------------------------------------------------ the check


def check_from(classes: dict[str, list[dict]], answers: dict[str, str], s: dict) -> dict:
    """The known-answer check on judged answers. ``classes`` maps masonic/trade/politics to uses
    ``{"id", "key"}``; ``answers`` maps id to the raw reply (a missing id = not yet asked)."""
    res: dict = {"classes": {}, "dedup_rule": {"words": s["dedup_words"],
                                               "overlap": s["dedup_overlap"]}}  # fmt: skip
    missing = [u["id"] for hs in classes.values() for u in hs if u["id"] not in answers]
    labels = {i: parse_reply(r) for i, r in answers.items()}
    asked = [u["id"] for hs in classes.values() for u in hs if u["id"] in answers]
    unparsed = [i for i in asked if labels[i] is None]
    res["questions"] = len(asked) + len(missing)
    res["not_yet_answered"] = len(missing)
    res["unparsed"] = len(unparsed)
    for name, hs in classes.items():
        raw = Counter(labels.get(u["id"]) for u in hs if labels.get(u["id"]))
        groups = group_passages([(u["id"], u["key"]) for u in hs], s["dedup_overlap"])
        ded = Counter(lab for g in groups if (lab := passage_label(g, labels)))
        res["classes"][name] = {
            "uses": len(hs),
            "uses_labelled": sum(raw.values()),
            "labels_raw": {k: raw.get(k, 0) for k in LABELS},
            "passages": len(groups),
            "passages_labelled": sum(ded.values()),
            "labels_dedup": {k: ded.get(k, 0) for k in LABELS},
        }
    if missing:
        res.update(attempted=False, passed=False,
                   reason=f"{len(missing)} check questions not yet answered")  # fmt: skip
        return res
    if asked and len(unparsed) / len(asked) > s["max_unparsed"]:
        res.update(attempted=False, passed=False,
                   reason=f"{len(unparsed)} of {len(asked)} replies unparsed")  # fmt: skip
        return res
    c = res["classes"]

    def frac(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    for kind in ("raw", "dedup"):
        n_key = "uses_labelled" if kind == "raw" else "passages_labelled"
        lab = f"labels_{kind}"
        nm_n = c["trade"][n_key] + c["politics"][n_key]
        nm_fm = c["trade"][lab]["freemasonry"] + c["politics"][lab]["freemasonry"]
        res[f"measures_{kind}"] = {
            "masonic_titled_labelled_freemasonry": frac(
                c["masonic"][lab]["freemasonry"], c["masonic"][n_key]
            ),
            "trade_politics_titled_not_freemasonry": frac(nm_n - nm_fm, nm_n),
            "trade_titled_labelled_trade": frac(c["trade"][lab]["trade"], c["trade"][n_key]),
            "politics_titled_labelled_political": frac(
                c["politics"][lab]["political"], c["politics"][n_key]
            ),
        }
    sizes = {
        "masonic": c["masonic"]["passages_labelled"],
        "trade_politics": c["trade"]["passages_labelled"] + c["politics"]["passages_labelled"],
    }
    mins = {"masonic": s["ka_min_masonic"], "trade_politics": s["ka_min_not_masonic"]}
    res["sizes_dedup"], res["minimums"] = sizes, mins
    if any(sizes[k] < mins[k] for k in sizes):
        res.update(attempted=False, passed=False, reason="a class is under its minimum")
        return res
    m = res["measures_dedup"]
    res["bars_required"] = {
        "masonic_titled_labelled_freemasonry": s["ka_bar_masonic"],
        "trade_politics_titled_not_freemasonry": s["ka_bar_not_masonic"],
    }
    res["bars_reported_not_required"] = {
        "trade_titled_labelled_trade": s["ka_report_trade"],
        "politics_titled_labelled_political": s["ka_report_politics"],
    }
    res["met"] = {k: m[k] is not None and m[k] >= b for k, b in res["bars_required"].items()}
    res["reported_met"] = {
        k: m[k] is not None and m[k] >= b for k, b in res["bars_reported_not_required"].items()
    }
    res["attempted"] = True
    res["passed"] = all(res["met"].values())
    return res


# ------------------------------------------------------------------------------ inputs


def library_hits() -> tuple[list[dict], list[dict]]:
    """(all scan hits, the library and newspaper hits) with each library hit's ``id`` as the first
    design's jobs file numbered it (``work_id|i`` over the library and newspaper hits)."""
    allh = c1.load_hits()
    lib = []
    for h in allh:
        if h["group"] in ("works", "newspapers"):
            h["i"] = len(lib)
            h["id"] = f"{h['work_id']}|{h['i']}"
            lib.append(h)
    return allh, lib


def check_classes(allh: list[dict], d: dict, s: dict) -> dict[str, list[dict]]:
    sample = c1.ka_sample(allh, d)
    return {
        name: [{**h, "key": dedup_key(h["left"], h["right"], s["dedup_words"])} for h in hs]
        for name, hs in sample.items()
    }


def year_sample(lib: list[dict], s: dict) -> list[dict]:
    """The first design's judging sample rule: up to ``per_year`` uses a year, seeded."""
    by_y: dict[int, list[dict]] = defaultdict(list)
    for h in lib:
        by_y[h["year"]].append(h)
    rng, got = random.Random(s["seed"]), []
    for y in sorted(by_y):
        pool = list(by_y[y])
        rng.shuffle(pool)
        got.extend(pool[: s["per_year"]])
    return got


def _reread(job: tuple[dict, list[dict], dict, int]) -> tuple[str, list[dict] | None]:
    """A work's wide passages for its scan hits in order, or None where it cannot be re-read."""
    row, short, d, w = job
    try:
        low = c1.normalise(door.text_of(row))
    except OSError:
        return row["work_id"], None
    wide = wide_uses(low, d, w)
    got = [wide[k] if k < len(wide) and agrees(wide[k], sh) else None for k, sh in enumerate(short)]
    return row["work_id"], got


def wide_library(lib: list[dict], need: set[str], d: dict, w: int) -> tuple[dict, Counter]:
    """Wide passage (left, mid, right) by library id for the ids in ``need``; falls back to the
    scan's 30 words where the text cannot be re-read or the k-th match does not agree."""
    by_work: dict[str, list[dict]] = defaultdict(list)
    for h in lib:
        by_work[h["work_id"]].append(h)
    works = sorted({h["work_id"] for h in lib if h["id"] in need})
    cat = door.catalog(set(works))
    jobs = [(cat[wid], by_work[wid], d, w) for wid in works if wid in cat]
    got, why = {}, Counter()
    with ProcessPoolExecutor(d["workers"]) as pool:
        for wid, wide in pool.map(_reread, jobs, chunksize=4):
            for k, h in enumerate(by_work[wid]):
                if h["id"] not in need:
                    continue
                wd = wide[k] if wide is not None and k < len(wide) else None
                if wd is None:
                    why["unreadable" if wide is None else "no_agreeing_match"] += 1
                    got[h["id"]] = (h["left"], h["mid"], h["right"], False)
                else:
                    got[h["id"]] = (wd["left"], wd["mid"], wd["right"], True)
    for h in lib:
        if h["id"] in need and h["id"] not in got:
            why["not_in_catalog"] += 1
            got[h["id"]] = (h["left"], h["mid"], h["right"], False)
    return got, why


def bom_passages(d: dict, w: int) -> tuple[list[dict], dict]:
    """Every use in the 1830 body text, on the body joined in order (so a window may run past a
    paragraph), each with its paragraph ``seq`` and book."""
    starts, parts, pos, meta = [], [], 0, []
    per_para = 0
    for line in c1.EDITION.read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") != "body":
            continue
        low = c1.normalise(r["text"])
        per_para += len(c1.find_uses(low, d))
        starts.append(pos)
        meta.append((r["seq"], r["book"]))
        parts.append(low)
        pos += len(low) + 1
    joined = " ".join(parts)
    got = []
    for u in wide_uses(joined, d, w):
        k = max(i for i, s in enumerate(starts) if s <= u["start"])
        got.append({**u, "seq": meta[k][0], "book": meta[k][1]})
    return got, {"uses_joined": len(got), "uses_by_paragraph": per_para}


def control_passages(d: dict, w: int) -> tuple[list[dict], dict]:
    from lab import emode

    got, info = [], {}
    for name, texts in (
        ("control_bible_style", emode.bible_style_texts()),
        ("control_js", emode.js_texts()),
    ):
        n_texts = 0
        for k, text in sorted(texts.items()):
            if len(text.split()) < d["controls_min_words"]:
                continue  # too short to count: not attempted, as in the first design
            n_texts += 1
            for j, u in enumerate(wide_uses(c1.normalise(text), d, w)):
                got.append({**u, "group": name, "work_id": k, "k": j})
        info[name] = {"texts": n_texts, "uses": sum(g["group"] == name for g in got)}
    return got, info


def write_jobs(path: Path, jobs: list[dict]) -> None:
    out(path).write_text("".join(json.dumps(j) + "\n" for j in jobs))


def make_jobs(cfg: dict) -> dict:
    d, s = c1.settings(cfg), v2(cfg)
    w = s["window_words"]
    allh, lib = library_hits()
    classes = check_classes(allh, d, s)
    check_ids = [h["id"] for hs in classes.values() for h in hs]
    sample = year_sample(lib, s)
    trans = [h for h in lib if h["translation"] and h["group"] == "works"]
    need = set(check_ids) | {h["id"] for h in sample} | {h["id"] for h in trans}
    wide, why = wide_library(lib, need, d, w)

    def job(jid: str, lib_id: str) -> dict:
        left, mid, right, _ = wide[lib_id]
        return {"id": jid, "prompt": prompt(left, mid, right)}

    write_jobs(CARD / "jobs_check.jsonl", [job(i, i) for i in check_ids])
    write_jobs(CARD / "jobs_sample.jsonl", [job(h["id"], h["id"]) for h in sample])
    bom, bom_info = bom_passages(d, w)
    ctrl, ctrl_info = control_passages(d, w)
    bjobs = [{"id": f"bom|{u['seq']}|{n}", "prompt": prompt(u["left"], u["mid"], u["right"])}
             for n, u in enumerate(bom)]  # fmt: skip
    bjobs += [
        {"id": f"{u['group']}|{u['work_id']}|{u['k']}",
         "prompt": prompt(u["left"], u["mid"], u["right"])}
        for u in ctrl
    ]  # fmt: skip
    bjobs += [job(f"translations|{h['id']}", h["id"]) for h in trans]
    write_jobs(CARD / "jobs_bom.jsonl", bjobs)
    old = CARD.parent / "2026-11-21-secret-combinations" / "jobs_referent.jsonl"
    old_ids = {json.loads(x)["id"] for x in old.read_text().splitlines()} if old.exists() else None
    summary = {
        "v2_sha256": v2_hash(cfg),
        "config_sha256": config.sha256_of_config(),
        "window_words": w,
        "questions": {
            "check": len(check_ids),
            "bom_and_controls": len(bjobs),
            "sample": len(sample),
        },  # fmt: skip
        "check_classes": {k: len(v) for k, v in classes.items()},
        "check_passages_by_dedup": {
            k: len(group_passages([(h["id"], h["key"]) for h in v], s["dedup_overlap"]))
            for k, v in classes.items()
        },
        "library_uses_needed": len(need),
        "fell_back_to_30_words": dict(why),
        "fell_back_total": sum(why.values()),
        "bom": bom_info,
        "controls": {**ctrl_info, "translations": {"uses": len(trans)}},
        "sample_same_as_first_design": (
            None if old_ids is None else {h["id"] for h in sample} == old_ids
        ),
    }
    out(CARD / "jobs_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


# ------------------------------------------------------------------------------ answers


def load_answers(path: Path) -> tuple[dict[str, str], set[str]]:
    """(id -> raw reply, models named) from a ``lab/judge.py`` answers file; absent = empty."""
    if not path.exists():
        return {}, set()
    got, models = {}, set()
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            got[r["id"]] = r.get("reply")
            if r.get("model"):
                models.add(r["model"])
    return got, models


def log_unparsed(name: str, answers: dict[str, str]) -> int:
    bad = [(i, r) for i, r in answers.items() if parse_reply(r) is None]
    if bad:
        with out(UNPARSED_LOG).open("a", encoding="utf-8") as fh:
            for i, r in bad:
                fh.write(json.dumps({"file": name, "id": i, "reply": r}) + "\n")
    return len(bad)


def check(cfg: dict) -> dict:
    d, s = c1.settings(cfg), v2(cfg)
    allh, _ = library_hits()
    answers, models = load_answers(CARD / "answers_check.jsonl")
    log_unparsed("answers_check", answers)
    res = check_from(check_classes(allh, d, s), answers, s)
    res["models"] = sorted(models)
    res["judging"] = "simulated judging by an AI model (lab.judge)"
    return res


# ------------------------------------------------------------------------------ the score


def tally(items: list[tuple[str, float]]) -> dict:
    """Labels of judged uses, unweighted and weighted: ``items`` are (label, weight)."""
    n, wn = Counter(), Counter()
    for lab, wt in items:
        n[lab] += 1
        wn[lab] += wt
    tot, wtot = sum(n.values()), sum(wn.values())
    clear, wclear = tot - n["unclear"], wtot - wn["unclear"]
    return {
        "judged": tot,
        "labels": {k: n.get(k, 0) for k in LABELS},
        "share_freemasonry": round(n["freemasonry"] / tot, 4) if tot else None,
        "share_freemasonry_excl_unclear": round(n["freemasonry"] / clear, 4) if clear else None,
        "weighted_uses": round(wtot, 2),
        "weighted_share_freemasonry": round(wn["freemasonry"] / wtot, 4) if wtot else None,
        "weighted_share_freemasonry_excl_unclear": (
            round(wn["freemasonry"] / wclear, 4) if wclear else None
        ),
    }


def vogel(per: dict, s: dict) -> dict:
    late, mid = per.get("1827-1830"), per.get("1800-1825")
    n_late = late["judged"] if late else 0
    s_late = late["weighted_share_freemasonry"] if late else None
    s_mid = mid["weighted_share_freemasonry"] if mid else None
    v = {"judged_1827_1830": n_late, "weighted_share_1827_1830": s_late,
         "weighted_share_1800_1825": s_mid}  # fmt: skip
    if n_late < s["vogel_min_uses"] or s_late is None:
        v["answer"] = f"cannot tell (fewer than {s['vogel_min_uses']} judged uses in 1827-1830)"
    elif s_late >= s["vogel_yes"] and s_mid is not None and s_late - s_mid >= s["vogel_rise"]:
        v["answer"] = "yes (Vogel): almost all Masonic after the rise"
    elif s_late <= s["vogel_no"]:
        v["answer"] = "no (general term): the Masonic share stays at or below half"
    else:
        v["answer"] = "mixed"
    return v


def score(cfg: dict, chk: dict | None = None) -> dict:
    chk = check(cfg) if chk is None else chk
    if not chk.get("passed"):
        raise SystemExit(
            "the known-answer check has not passed (or is not complete): no score is written; "
            f"{chk.get('reason', 'bars missed')}"
        )
    d, s = c1.settings(cfg), v2(cfg)
    _, lib = library_hits()
    by_id = {h["id"]: h for h in lib}
    ans, models = load_answers(CARD / "answers_sample.jsonl")
    bans, bmodels = load_answers(CARD / "answers_bom.jsonl")
    unparsed = {"sample": log_unparsed("answers_sample", ans),
                "bom": log_unparsed("answers_bom", bans)}  # fmt: skip
    sample_ids = _ids(CARD / "jobs_sample.jsonl")
    bom_ids = _ids(CARD / "jobs_bom.jsonl")
    labelled = {i: parse_reply(ans[i]) for i in sample_ids if i in ans}
    labelled = {i: lab for i, lab in labelled.items() if lab}
    total_y = Counter(h["year"] for h in lib)
    judged_y = Counter(by_id[i]["year"] for i in labelled)
    weight = {i: total_y[by_id[i]["year"]] / judged_y[by_id[i]["year"]] for i in labelled}

    def per_period(groups: tuple[str, ...]) -> dict:
        table, wide = {}, defaultdict(list)
        for i, lab in labelled.items():
            h = by_id[i]
            if h["group"] in groups:
                p = c1.period_of(h["year"], d)
                if p:
                    table.setdefault(p, []).append((lab, weight[i]))
                if 1827 <= h["year"] <= 1830:
                    wide["1827-1830"].append((lab, weight[i]))
                elif 1800 <= h["year"] <= 1825:
                    wide["1800-1825"].append((lab, weight[i]))
                elif h["year"] <= 1799:
                    wide["1700-1799"].append((lab, weight[i]))
        res = {}
        for a, b in d["periods"]:
            p = f"{a}" if a == b else f"{a}-{b}"
            res[p] = tally(table.get(p, []))
        res["spans"] = {k: tally(v) for k, v in sorted(wide.items())}
        return res

    by_period = {
        "books": per_period(("works",)),
        "newspapers": per_period(("newspapers",)),
        "pooled": per_period(("works", "newspapers")),
    }
    news = [(i, lab) for i, lab in labelled.items() if by_id[i]["group"] == "newspapers"]
    md = d["morgan_date"]
    morgan = {
        "date": md,
        "before": tally([(lab, weight[i]) for i, lab in news if by_id[i]["date"] < md]),
        "after": tally([(lab, weight[i]) for i, lab in news if by_id[i]["date"] >= md]),
    }
    blab = {i: parse_reply(bans[i]) for i in bom_ids if i in bans}
    bom_rows = [
        {"id": i, "seq": int(i.split("|")[1]), "label": blab.get(i)}
        for i in sorted(bom_ids, key=lambda x: (x.split("|")[0], x))
        if i.startswith("bom|")
    ]
    controls = {}
    for g in CONTROL_GROUPS:
        ids = [i for i in bom_ids if i.startswith(g + "|")]
        controls[g] = {
            "uses": len(ids),
            "not_yet_answered": sum(i not in bans for i in ids),
            **tally([(blab[i], 1.0) for i in ids if blab.get(i)]),
        }
    used = ", ".join(sorted(models | bmodels | set(chk.get("models", [])))) or s["model"]
    return {
        "judging": f"simulated judging by an AI model (lab.judge, model {used})",
        "v2_sha256": v2_hash(cfg),
        "settings_sha256": c1.settings_hash(cfg),
        "config_sha256": config.sha256_of_config(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "known_answer": chk,
        "sample": {
            "questions": len(sample_ids),
            "labelled": len(labelled),
            "not_yet_answered": sum(i not in ans for i in sample_ids),
            "unparsed": unparsed["sample"],
            "uses_by_year": {str(y): total_y[y] for y in sorted(total_y)},
            "judged_by_year": {str(y): judged_y[y] for y in sorted(judged_y)},
        },
        "by_period": by_period,
        "newspapers_before_after_morgan": morgan,
        "verdict": vogel(by_period["pooled"]["spans"], s),
        "book_of_mormon": {
            "uses": len(bom_rows),
            "not_yet_answered": sum(
                r["label"] is None and r["id"] not in bans for r in bom_rows
            ),  # fmt: skip
            "unparsed": sum(r["label"] is None and r["id"] in bans for r in bom_rows),
            **tally([(r["label"], 1.0) for r in bom_rows if r["label"]]),
            "uses_by_label": bom_rows,
        },
        "controls": controls,
        "labels_by_id": {
            i: [by_id[i]["year"], by_id[i]["group"], lab] for i, lab in sorted(labelled.items())
        },  # fmt: skip
    }


def _ids(path: Path) -> list[str]:
    return [json.loads(x)["id"] for x in path.read_text().splitlines() if x.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["jobs", "check", "score"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "jobs":
        print(json.dumps(make_jobs(cfg), indent=1))
    elif a.cmd == "check":
        print(json.dumps(check(cfg), indent=1))
    else:
        res = score(cfg)
        out(RESULT).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: res[k] for k in ("judging", "verdict")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
