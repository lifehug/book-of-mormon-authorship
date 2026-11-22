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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["jobs", "check", "score"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "jobs":
        print(json.dumps(jobs(cfg), indent=1))
    elif a.cmd == "check":
        d = settings(cfg)
        prompts = {j["id"]: j["prompt"] for j in _load(CARD / "jobs_first.jsonl")}
        print(json.dumps(check_of(answers(), prompts, d), indent=1))
    else:
        res = score(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(PUBLIC).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "works"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
