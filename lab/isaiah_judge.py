"""BOM-122, the by-meaning step: a model judge reads each commentary at each changed verse.

The second design of ``lab.isaiah`` found by wording that Adam Clarke's commentary prints 2 of the
Book of Mormon's 523 strict Isaiah readings (and 4 of 1,080 decoys). A commentary can argue for a
reading without printing it, so the 4,991 prepared questions ask a hosted model, for Clarke's
volume and 11 other commentaries and annotated Bibles, whether the passage around each quoted
verse proposes, prints or explains the book's reading. Every answer is **simulated judging by an
AI model** (``lab.judge``). The judge's known-answer check comes first: the same question about
made-up readings (the decoys of ``lab.isaiah``) must be answered NO, and questions whose passage
prints the reading word for word must be answered YES. Only if both bars are met are the answers
counted. The test card is ``data/private/lab/owner/2026-11-22-isaiah-judging/card.md``; settings
are ``lab.isaiah.v2.judging``. Questions and replies quote text and stay private; the result
holds ids and counts.

Usage::

    python -m lab.isaiah_judge jobs     # decoy questions for the check (seeded sample) + order
    python -m lab.isaiah_judge check    # the judge's known-answer check from the answers so far
    python -m lab.isaiah_judge score    # -> data/lab/reruns/isaiah_variants/result_judged_v2.json
    python -m lab.isaiah_judge townsend # Townsend's examples looked up -> townsend_examples.json
    python -m lab.isaiah_judge clarke-gap        # post hoc: questions at Clarke's garbled verses
    python -m lab.isaiah_judge score-clarke-gap  # -> result_clarke_gap.json (main result unchanged)
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from math import comb
from pathlib import Path

from lab import isaiah
from lab.paths import out
from metadata import config

CARD = isaiah.NOTES / "owner" / "2026-11-22-isaiah-judging"
REAL = isaiah.CARD2 / "judge_jobs_v2.jsonl"
PUBLIC = isaiah.OUT / "result_judged_v2.json"
TOWNSEND_ITEMS = isaiah.OUT / "townsend_article_items.json"
TOWNSEND_OUT = isaiah.OUT / "townsend_examples.json"


def settings(cfg: dict) -> dict:
    return isaiah.v2_settings(cfg) | cfg["lab"]["isaiah"]["v2"]["judging"]


def _load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def verbatim(prompt: str) -> bool:
    """Does the passage print the reading asked about, word for word?"""
    m = re.search(r"Book of Mormon reads '([^']*)'", prompt)
    passage = prompt.split("\n\n", 1)[1]
    return bool(m) and f" {m.group(1)} " in f" {passage} "


def parse(reply: str) -> str | None:
    m = re.match(r"\W*(YES|NO|UNCLEAR)\b", reply.strip(), re.I)
    return m.group(1).upper() if m else None


def decoy_readings(decoys: list[dict], readings: list[dict]) -> list[dict]:
    """Made-up readings in the shape of real ones: each decoy is a real reading's change moved to
    another verse, so its "King James form" is the decoy with the change undone. Decoys whose
    change adds no words (an omission) cannot be undone by position and are left out."""
    src = {r["rid"]: r for r in readings}
    res = []
    for x in decoys:
        r = src[x["rid"]]
        new, old = r["new"].split(), r["kjv"].split()
        words = x["reading"]
        at = next((i for i in range(len(words)) if new and words[i : i + len(new)] == new), None)
        if at is None:
            continue
        res.append(
            {
                "rid": len(res),
                "ref": x["ref"],
                "reading": words,
                "kjv_form": words[:at] + old + words[at + len(new) :],
                "context": x["context"],
                "kjv": r["kjv"],
                "new": r["new"],
                "kind": r["kind"],
            }
        )
    return res


def jobs(cfg: dict) -> dict:
    """Decoy questions (expected NO) for the check, and the order the real ones are asked in."""
    d = settings(cfg)
    isa = isaiah.Isaiah()
    res = json.loads(isaiah.OUT2["result"].read_text())
    if "book_of_mormon" not in res:
        raise SystemExit("result_v2.json has no scored readings")
    rows = isaiah.library(d)
    by = {r["work_id"]: r for r in rows}
    bom = isaiah.two_sets(isaiah.bom_queries(isa, d), isa, d)
    works = sorted({j["id"].split("|")[0] for j in _load(REAL)})
    decoys = decoy_readings(bom["strict"]["decoys"], bom["strict"]["readings"])
    tmp = CARD / "decoy_all.jsonl"
    isaiah._judge_jobs(
        decoys, {"works": [{"work_id": w, "class": ["commentary"], "kjv_forms": 0} for w in works]},
        by, isa, d | {"judge_top_works": len(works)}, tmp,
    )  # fmt: skip
    pool = [j for j in _load(tmp) if not verbatim(j["prompt"])]
    rng = random.Random(d["random_seed"])
    clarke = [j for j in pool if j["id"].startswith(d["clarke_isaiah"] + "|")]
    rest = [j for j in pool if not j["id"].startswith(d["clarke_isaiah"] + "|")]
    rng.shuffle(clarke)
    rng.shuffle(rest)
    pick = clarke[: d["check_decoys_clarke"]] + rest[: d["check_decoys_other"]]
    for j in pick:
        j["id"] = "decoy|" + j["id"]
    real = _load(REAL)
    first = [
        j for j in real if j["id"].startswith(d["clarke_isaiah"] + "|") or verbatim(j["prompt"])
    ]
    ids = {j["id"] for j in first}
    later = [j for j in real if j["id"] not in ids]
    for name, js in (("jobs_first.jsonl", pick + first), ("jobs_rest.jsonl", later)):
        out(CARD / name).write_text("".join(json.dumps(j) + "\n" for j in js))
    return {"decoy_pool": len(pool), "decoys": len(pick), "first": len(pick) + len(first),
            "rest": len(later)}  # fmt: skip


def answers() -> dict[str, str | None]:
    res = {}
    for name in ("answers_first.jsonl", "answers_rest.jsonl"):
        p = CARD / name
        for r in _load(p) if p.exists() else []:
            res[r["id"]] = parse(r["reply"])
    return res


def check_of(ans: dict[str, str | None], prompts: dict[str, str], d: dict) -> dict:
    dec = [i for i in prompts if i.startswith("decoy|")]
    verb = [i for i, p in prompts.items() if not i.startswith("decoy|") and verbatim(p)]
    open_ = [i for i in dec + verb if i not in ans]
    got_d = [ans[i] for i in dec if ans.get(i)]
    got_v = [ans[i] for i in verb if ans.get(i)]
    res = {
        "decoy_questions": len(dec),
        "verbatim_questions": len(verb),
        "not_yet_answered": len(open_),
        "decoys_answered_no": round(got_d.count("NO") / len(got_d), 4) if got_d else None,
        "verbatim_answered_yes": round(got_v.count("YES") / len(got_v), 4) if got_v else None,
        "bars": {
            "decoys_answered_no": d["bar_decoy_no"],
            "verbatim_answered_yes": d["bar_verbatim_yes"],
        },
    }
    res["attempted"] = not open_ and bool(got_d) and bool(got_v)
    res["passed"] = bool(
        res["attempted"]
        and res["decoys_answered_no"] >= d["bar_decoy_no"]
        and res["verbatim_answered_yes"] >= d["bar_verbatim_yes"]
    )
    return res


def fisher_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher exact p for a/(a+b) > c/(c+d)."""
    n, k, m = a + b + c + d, a + c, a + b
    den = comb(n, k)
    return sum(comb(m, x) * comb(n - m, k - x) for x in range(a, min(k, m) + 1)) / den


def score(cfg: dict) -> dict:
    d = settings(cfg)
    prompts = {j["id"]: j["prompt"] for n in ("jobs_first.jsonl", "jobs_rest.jsonl")
               for j in _load(CARD / n)}  # fmt: skip
    ans = answers()
    chk = check_of(ans, prompts, d)
    res: dict = {
        "judging": f"simulated judging by an AI model (lab.judge, model {d['model']})",
        "known_answer": chk,
    }
    if not chk["passed"]:
        res["stopped"] = "the judge's known-answer check is not passed; nothing is counted"
        return res
    works: dict[str, Counter] = {}
    for i, v in ans.items():
        kind = "decoy" if i.startswith("decoy|") else "real"
        wid = i.removeprefix("decoy|").split("|")[0]
        c = works.setdefault(wid, Counter())
        c[f"{kind}_asked"] += 1
        c[f"{kind}_{(v or 'unparsed').lower()}"] += 1
        if kind == "real" and v == "YES" and not verbatim(prompts[i]):
            c["real_yes_not_verbatim"] += 1
    res["unanswered_real"] = len([i for i in prompts if i not in ans])
    res["works"] = {w: dict(c) for w, c in sorted(works.items())}
    ck = works.get(d["clarke_isaiah"], Counter())
    oth = Counter()
    for w, c in works.items():
        if w != d["clarke_isaiah"]:
            oth.update(c)
    rate = lambda c: c["real_yes"] / c["real_asked"] if c["real_asked"] else None  # noqa: E731
    others = {w: rate(c) for w, c in works.items() if w != d["clarke_isaiah"]}
    res["clarke"] = {
        "asked": ck["real_asked"], "yes": ck["real_yes"], "rate": rate(ck),
        "decoys_asked": ck["decoy_asked"], "decoys_yes": ck["decoy_yes"],
        "others_asked": oth["real_asked"], "others_yes": oth["real_yes"], "others_rate": rate(oth),
        "rank_among_works": 1 + sum(1 for r in others.values() if (r or 0) > (rate(ck) or 0)),
        "p_above_others": fisher_greater(ck["real_yes"], ck["real_asked"] - ck["real_yes"],
                                         oth["real_yes"], oth["real_asked"] - oth["real_yes"]),
    }  # fmt: skip
    k = res["clarke"]
    res["verdict"] = (
        "Clarke stands out"
        if k["rank_among_works"] == 1 and k["p_above_others"] < d["alpha"]
        else "Clarke does not stand out among the commentaries"
    )
    return res


# ------------------------------------------------------------------ Townsend's examples
# Each example in Townsend (2025), keyed from the article, looked up in what already exists: the
# variant list, the wording search and the judged answers. No model is run.
ORDER = ("clarke_by_wording", "clarke_by_note", "not_supported", "not_asked_of_clarke",
         "outside_variant_set")  # fmt: skip
OUTSIDE = {"LONG", "PREFACE", "PARAPHRASE"}


def townsend_examples(
    items: list[dict],
    detail: list[dict],
    variants: list[dict],
    ans: dict[str, str | None],
    asked: set[str],
    clarke: str,
    kjv_in_clarke: dict[int, bool] | None = None,
) -> dict:
    """Class each example: the first of ``ORDER`` that any of its named changes reaches (the rule
    written on the card), and beside it the class of the one change Townsend ties to Clarke
    (``primary``, added after the first output showed a minor neighbouring change could decide).

    ``detail`` is the strict readings (rid, ref, kjv, new, in_clarke, works), ``variants`` the
    full variant list (ref, kjv, new, long), ``ans`` the parsed answers by job id, ``asked`` the
    real job ids, ``kjv_in_clarke`` whether each reading's King James form is in Clarke's OCR."""
    strict = {(r["ref"], r["kjv"], r["new"]): r for r in detail}
    full = {(v["ref"], v["kjv"], v["new"]) for v in variants}
    long_at = Counter(v["ref"] for v in variants if v["long"])
    by_rid: dict[int, set[str]] = {}
    for i in asked:
        w, rid = i.rsplit("|", 1)
        by_rid.setdefault(int(rid), set()).add(w)
    rows, tally, tally_main = [], Counter(), Counter()
    for it in items:
        ch_rows = []
        for ref, kjv, new in it["changes"]:
            c: dict = {"ref": ref}
            if new in OUTSIDE:
                c |= {"what": new.lower(), "class": "outside_variant_set",
                      "in_variant_list": new == "LONG" and long_at[ref] > 0}  # fmt: skip
                ch_rows.append(c)
                continue
            c |= {"kjv": kjv, "new": new, "in_variant_list": (ref, kjv, new) in full}
            r = strict.get((ref, kjv, new))
            if r is None:
                c["class"] = "outside_variant_set"
                ch_rows.append(c)
                continue
            rid = r["rid"]
            ws = by_rid.get(rid, set())
            others = ws - {clarke}
            c |= {
                "rid": rid,
                "in_strict_set": True,
                "works_by_wording": r["works"],
                "clarke_by_wording": bool(r["in_clarke"]),
                "clarke_asked": clarke in ws,
                "clarke_answer": ans.get(f"{clarke}|{rid}") if clarke in ws else None,
                "others_asked": len(others),
                "others_yes": sum(ans.get(f"{w}|{rid}") == "YES" for w in others),
            }
            if kjv_in_clarke is not None:
                c["kjv_form_in_clarke_ocr"] = kjv_in_clarke.get(rid)
            c["class"] = (
                "clarke_by_wording" if c["clarke_by_wording"]
                else "clarke_by_note" if c["clarke_answer"] == "YES"
                else "not_supported" if c["clarke_asked"]
                else "not_asked_of_clarke"
            )  # fmt: skip
            ch_rows.append(c)
        if it.get("tied_to_clarke", True):
            cls = min((c["class"] for c in ch_rows), key=ORDER.index)
            main = ch_rows[it.get("primary", 0)]["class"]
        else:
            cls = main = "townsend_credits_other_works"
        tally[cls] += 1
        tally_main[main] += 1
        rows.append({
            "n": it["n"], "isaiah": it["isaiah"], "book_of_mormon": it["book_of_mormon"],
            "townsend_pages": it["townsend_pages"], "jackson_pages": it.get("jackson_pages"),
            "class": cls, "primary": it.get("primary", 0), "primary_class": main,
            "changes": ch_rows,
        })  # fmt: skip
    ins = [c for r in rows for c in r["changes"] if c.get("in_strict_set")]
    return {
        "examples": len(rows),
        "classes": dict(tally),
        "primary_classes": dict(tally_main),
        "named_changes": sum(len(r["changes"]) for r in rows),
        "named_changes_in_strict_set": len(ins),
        "clarke_asked": sum(c["clarke_asked"] for c in ins),
        "clarke_yes": sum(c["clarke_answer"] == "YES" for c in ins),
        "clarke_by_wording": sum(c["clarke_by_wording"] for c in ins),
        "others_asked": sum(c["others_asked"] for c in ins),
        "others_yes": sum(c["others_yes"] for c in ins),
        "found_in_any_work_by_wording": sum(c["works_by_wording"] > 0 for c in ins),
        "rows": rows,
    }


def _kjv_in_clarke(d: dict) -> dict[int, bool] | None:
    """Whether each strict reading's King James form occurs in Clarke's OCR text: where it does
    not, the job list could not place Clarke's quotation of the verse and asked him nothing."""
    from lab import door, registry

    isa = isaiah.Isaiah()
    rd = isaiah.two_sets(isaiah.bom_queries(isa, d), isa, d)["strict"]["readings"]
    reg = [r for r in registry.load().to_pylist() if r["work_id"] == d["clarke_isaiah"]]
    cat = door.catalog({d["clarke_isaiah"]})
    if not reg or d["clarke_isaiah"] not in cat:
        return None
    text = " " + " ".join(isaiah.tokens(door.text_of(cat[d["clarke_isaiah"]] | reg[0]))) + " "
    return {r["rid"]: f" {' '.join(r['kjv_form'])} " in text for r in rd}


def townsend(cfg: dict) -> dict:
    d = settings(cfg)
    items = json.loads(TOWNSEND_ITEMS.read_text())
    res2 = json.loads(isaiah.OUT2["result"].read_text())["book_of_mormon"]
    detail = res2["strict"]["readings_detail"]
    variants = json.loads(isaiah.OUT2["variants"].read_text())["variants"]
    asked = {j["id"] for n in ("jobs_first.jsonl", "jobs_rest.jsonl") for j in _load(CARD / n)
             if not j["id"].startswith("decoy|")}  # fmt: skip
    kic = _kjv_in_clarke(d)
    res = townsend_examples(
        items["items"], detail, variants, answers(), asked, d["clarke_isaiah"], kic
    )
    per_work = Counter(i.rsplit("|", 1)[0] for i in asked)
    res["coverage"] = {
        "strict_readings": len(detail),
        "kjv_form_in_clarke_ocr": sum(kic.values()) if kic is not None else None,
        "clarke_asked": per_work[d["clarke_isaiah"]],
        "others_asked_min": min(v for w, v in per_work.items() if w != d["clarke_isaiah"]),
        "others_asked_max": max(v for w, v in per_work.items() if w != d["clarke_isaiah"]),
    }
    return {
        "what": "Townsend's examples (keyed from his article) looked up in the BOM-122 results; "
        "no model run. Judged answers are simulated judging by an AI model.",
        "items_file": str(TOWNSEND_ITEMS),
        "classes_in_order": list(ORDER) + ["townsend_credits_other_works"],
        **res,
    }


# ------------------------------------------------------------- Clarke's lost verses (post hoc)
# 2026-11-24, after the scored result: Clarke's scan garbles the King James line at many verses,
# so the job list asked him about 237 of 523 readings. Here his verse is located by overlapping
# word sequences, tolerant of single damaged words, and the same question is asked there.
GAP_JOBS = CARD / "jobs_clarke_gap.jsonl"
GAP_ANSWERS = CARD / "answers_clarke_gap.jsonl"
GAP_LOCATED = isaiah.OUT / "clarke_gap_located.json"
GAP_OUT = isaiah.OUT / "result_clarke_gap.json"


def shingle_index(text: list[str], n: int) -> dict[tuple, list[int]]:
    idx: dict[tuple, list[int]] = {}
    for i in range(len(text) - n + 1):
        idx.setdefault(tuple(text[i : i + n]), []).append(i)
    return idx


def locate(
    verse: list[str], idx: dict[tuple, list[int]], g: dict, lo: int = 0, hi: int | None = None
) -> dict | None:
    """Best window of ``span_factor`` x the verse's length holding the largest share of the
    verse's distinct ``shingle``-word sequences, between ``lo`` and ``hi``. None below
    ``min_share`` or for a verse with fewer than ``min_shingles`` sequences. Earliest on a tie.
    Returns the window start, the share and the hits (position, index in the verse)."""
    n = g["shingle"]
    sh: dict[tuple, int] = {}
    for i in range(len(verse) - n + 1):
        sh.setdefault(tuple(verse[i : i + n]), i)
    if len(sh) < g["min_shingles"]:
        return None
    hits = sorted((p, k) for k in sh for p in idx.get(k, ()) if p >= lo and (hi is None or p < hi))
    width = max(n, round(g["span_factor"] * len(verse)))
    best, j, have = None, 0, Counter()
    for i, (p, _) in enumerate(hits):
        while j < len(hits) and hits[j][0] < p + width:
            have[hits[j][1]] += 1
            j += 1
        share = len(have) / len(sh)
        if best is None or share > best[1]:
            best = (i, share, j)
        have[hits[i][1]] -= 1
        if not have[hits[i][1]]:
            del have[hits[i][1]]
    if best is None or best[1] < g["min_share"]:
        return None
    i, share, j = best
    return {"start": hits[i][0], "share": round(share, 4),
            "hits": [(p, sh[k]) for p, k in hits[i:j]]}  # fmt: skip


def centre(loc: dict, verse: list[str], kjv_form: list[str]) -> int:
    """Position in the work of the reading's King James words: the hit nearest their place."""
    at = next((i for i in range(len(verse)) if verse[i : i + len(kjv_form)] == kjv_form), None)
    if at is None:  # the reading reaches into a neighbouring verse: use its words' first match
        at = next((verse.index(w) for w in kjv_form if w in verse), len(verse) // 2)
    p, k = min(loc["hits"], key=lambda h: abs(h[1] - at))
    return max(0, p + at - k)


def _verse(ref: str) -> tuple[int, int]:
    ch, vs = ref.split(":")
    return int(ch), int(vs)


def gap_jobs(
    gap: list[dict], decoys: list[dict], verses: dict, text: list[str], d: dict, rng_seed: int
) -> dict:
    """Questions for Clarke at ``gap`` readings and ``check_decoys`` made-up ones, each at the
    verse located in ``text``. Pure: returns jobs and the located / not-located ids."""
    g = d["clarke_gap"]
    idx = shingle_index(text, g["shingle"])

    # Isaiah's span: from the first verse of chapter 1 that can be located to the last of 66
    # (1:1 itself is unreadable in Clarke's scan); the whole volume if either end is not found.
    def end(keys: list) -> tuple | None:
        return next(((k, x) for k in keys if (x := locate(verses[k], idx, g))), None)

    first = end(sorted(k for k in verses if k[0] == 1))
    last = end(sorted((k for k in verses if k[0] == 66), reverse=True))
    lo, hi = 0, None
    if first and last and first[1]["start"] < last[1]["start"]:
        lo = first[1]["start"]
        hi = last[1]["start"] + round(g["span_factor"] * len(verses[last[0]])) + 1

    def ask(r: dict) -> tuple[str, dict] | None:
        verse = verses.get(_verse(r["ref"]), [])
        loc = locate(verse, idx, g, lo, hi)
        if loc is None:
            return None
        c = centre(loc, verse, r["kjv_form"])
        win = " ".join(text[max(0, c - d["judge_window"]) : c + d["judge_window"]])
        return isaiah.judge_prompt(r, win), {"share": loc["share"], "at": c}

    jobs_, located, missing = [], [], []
    for r in gap:
        got = ask(r)
        if got is None:
            missing.append(r["rid"])
            continue
        jobs_.append({"id": f"{d['clarke_isaiah']}|{r['rid']}", "prompt": got[0]})
        located.append({"rid": r["rid"], "ref": r["ref"], **got[1]})
    pool = []
    for r in decoys:
        got = ask(r)
        if got is not None and not verbatim(got[0]):
            pool.append({"id": f"decoy|{d['clarke_isaiah']}|{r['rid']}", "prompt": got[0]})
    random.Random(rng_seed).shuffle(pool)
    picked = pool[: g["check_decoys"]]
    return {"jobs": picked + jobs_, "located": located, "not_located": missing,
            "decoy_pool": len(pool), "decoys": len(picked),
            "isaiah_span": [lo, hi]}  # fmt: skip


def clarke_gap(cfg: dict) -> dict:
    """Build the post hoc questions (private) and the located ids (public: ids and numbers)."""
    from lab import door, registry

    d = settings(cfg)
    isa = isaiah.Isaiah()
    bom = isaiah.two_sets(isaiah.bom_queries(isa, d), isa, d)["strict"]
    rd = bom["readings"]
    asked = {j["id"] for n in ("jobs_first.jsonl", "jobs_rest.jsonl") for j in _load(CARD / n)}
    clarke = d["clarke_isaiah"]
    gap = [r for r in rd if f"{clarke}|{r['rid']}" not in asked]
    used = {int(i.rsplit("|", 1)[1]) for i in asked if i.startswith(f"decoy|{clarke}|")}
    decoys = [r for r in decoy_readings(bom["decoys"], rd) if r["rid"] not in used]
    reg = [r for r in registry.load().to_pylist() if r["work_id"] == clarke]
    text = isaiah.tokens(door.text_of(door.catalog({clarke})[clarke] | reg[0]))
    res = gap_jobs(gap, decoys, isa.verse_words, text, d, d["random_seed"])
    out(GAP_JOBS).write_text("".join(json.dumps(j) + "\n" for j in res.pop("jobs")))
    res = {"post_hoc": "2026-11-24, after the scored result (card: Clarke's lost verses)",
           "strict_readings": len(rd), "clarke_asked_before": len(rd) - len(gap),
           "gap": len(gap), **res, "jobs_file": str(GAP_JOBS)}  # fmt: skip
    out(GAP_LOCATED).write_text(json.dumps(res, indent=1) + "\n")
    return res


def _answers_of(path: Path) -> dict[str, str | None]:
    return {r["id"]: parse(r["reply"]) for r in (_load(path) if path.exists() else [])}


def score_gap(main: dict, located: dict, jobs_: list[dict], ans: dict, detail: list[dict],
              townsend_rids: list[int], d: dict) -> dict:  # fmt: skip
    """Beside the main result (unchanged): Clarke's rate over every asked reading, the gap's own
    made-up-reading check, and the four Townsend changes."""
    ids = [j["id"] for j in jobs_]
    dec = [i for i in ids if i.startswith("decoy|")]
    real = [i for i in ids if not i.startswith("decoy|")]
    open_ = [i for i in ids if i not in ans]
    got_d = [ans[i] for i in dec if ans.get(i)]
    chk = {"decoy_questions": len(dec), "not_yet_answered": len(open_),
           "decoys_answered_no": round(got_d.count("NO") / len(got_d), 4) if got_d else None,
           "bar": d["bar_decoy_no"]}  # fmt: skip
    chk["passed"] = bool(not open_ and got_d and chk["decoys_answered_no"] >= d["bar_decoy_no"])
    res: dict = {
        "post_hoc": "2026-11-24, after the scored result; the main result is unchanged",
        "judging": f"simulated judging by an AI model (lab.judge, model {d['model']})",
        "main_result_unchanged": {
            k: main["clarke"][k]
            for k in ("asked", "yes", "rate", "rank_among_works", "p_above_others")
        }
        | {"verdict": main["verdict"]},  # fmt: skip
        "located": {
            "gap": located["gap"],
            "located": len(located["located"]),
            "not_located": len(located["not_located"]),
        },  # fmt: skip
        "check": chk,
    }
    if not chk["passed"]:
        res["stopped"] = "the gap's made-up-reading check is not passed or not complete"
        return res
    yes = [int(i.rsplit("|", 1)[1]) for i in real if ans.get(i) == "YES"]
    k = main["clarke"]
    asked, n_yes = k["asked"] + len(real), k["yes"] + len(yes)
    rate = n_yes / asked if asked else None
    others = [c["real_yes"] / c["real_asked"] for w, c in main["works"].items()
              if w != d["clarke_isaiah"] and c.get("real_asked")]  # fmt: skip
    by = {r["rid"]: r for r in detail}
    res["clarke_all_located"] = {
        "asked": asked, "yes": n_yes, "rate": rate,
        "gap_asked": len(real), "gap_yes": len(yes),
        "others_asked": k["others_asked"], "others_yes": k["others_yes"],
        "others_rate": k["others_rate"],
        "rank_among_works": 1 + sum(1 for r in others if r > (rate or 0)),
        "p_above_others": fisher_greater(n_yes, asked - n_yes, k["others_yes"],
                                         k["others_asked"] - k["others_yes"]),
    }  # fmt: skip
    c = res["clarke_all_located"]
    res["verdict"] = (
        "Clarke stands out"
        if c["rank_among_works"] == 1 and c["p_above_others"] < d["alpha"]
        else "Clarke does not stand out among the commentaries"
    )
    res["gap_yes"] = [{k2: by[r][k2] for k2 in ("rid", "ref", "kind", "kjv", "new")}
                      for r in sorted(yes) if r in by]  # fmt: skip
    res["townsend"] = [
        {"rid": r, "ref": by[r]["ref"], "kjv": by[r]["kjv"], "new": by[r]["new"],
         "located": f"{d['clarke_isaiah']}|{r}" in real,
         "clarke_answer": ans.get(f"{d['clarke_isaiah']}|{r}")}
        for r in townsend_rids if r in by
    ]  # fmt: skip
    return res


def score_clarke_gap(cfg: dict) -> dict:
    d = settings(cfg)
    main_ = json.loads(PUBLIC.read_text())
    located = json.loads(GAP_LOCATED.read_text())
    detail = json.loads(isaiah.OUT2["result"].read_text())["book_of_mormon"]["strict"][
        "readings_detail"
    ]
    tw = json.loads(TOWNSEND_OUT.read_text())["rows"]
    rids = [r["changes"][r["primary"]].get("rid") for r in tw
            if r["primary_class"] == "not_asked_of_clarke"]  # fmt: skip
    return score_gap(main_, located, _load(GAP_JOBS), _answers_of(GAP_ANSWERS), detail,
                     [r for r in rids if r is not None], d)  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "cmd", choices=["jobs", "check", "score", "townsend", "clarke-gap", "score-clarke-gap"]
    )
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "jobs":
        print(json.dumps(jobs(cfg), indent=1))
    elif a.cmd == "check":
        d = settings(cfg)
        prompts = {j["id"]: j["prompt"] for j in _load(CARD / "jobs_first.jsonl")}
        print(json.dumps(check_of(answers(), prompts, d), indent=1))
    elif a.cmd == "clarke-gap":
        res = clarke_gap(cfg)
        print(json.dumps({k: v for k, v in res.items() if k not in ("located", "not_located")}
                         | {"located": len(res["located"]),
                            "not_located": len(res["not_located"])}, indent=1))  # fmt: skip
    elif a.cmd == "score-clarke-gap":
        res = score_clarke_gap(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(GAP_OUT).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res, indent=1))
    elif a.cmd == "townsend":
        res = townsend(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(TOWNSEND_OUT).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    else:
        res = score(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(PUBLIC).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "works"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
