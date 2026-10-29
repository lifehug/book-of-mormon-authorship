"""Time-split validation: does an author's style survive the years? (BOM-48; gates BOM-49)

Amendment 5 lets a candidate's later writing stand in for the scarce pre-1830 sample only if a
profile built on one side of the gap recognises their writing on the other. This measures that,
on known authors only (no Book of Mormon text):

* **Baseline.** Corpus authors with ``timesplit.min_words`` or more words both early and late,
  with at least ``timesplit.min_gap_years`` between their last early and first late work.
  ``timesplit.authors`` are drawn with the root seed. Each author's early passage
  (``power.fixed_test_words``) is attributed among every drawn author's late profile, and the
  reverse. This is how much drift is normal.
* **Candidates.** Every candidate with text on both sides of 1830 -- only Joseph Smith and Oliver
  Cowdery; Rigdon, Pratt and Phelps have no pre-1830 text -- using the provenance tiers Amendment 5
  admits (holograph and dictated; for printed items, the author's own signed work). Their pre-1830
  text is attributed among the post-1830 profiles of every candidate with any, and the reverse.
  Both pre-1830 samples are under BOM-43's 10,000-word reference floor, so the reverse direction is
  reported as below the floor.

Methods and settings are BOM-43's (``eval.power._attribute``). Masked text for candidates (4.4);
the baseline uses the normalised corpus text.

Usage::

    python -m eval.timesplit      # -> data/benchmark/timesplit.json
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from classic import tokenize
from eval.power import BLOCK, METHODS, _attribute, blocks
from metadata.config import classic_kwargs, derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/benchmark/timesplit.json")
ADMITTED = {"handwritten", "dictated", "printed_by_author", "posthumous"}


def baseline_authors(cfg: dict) -> dict[str, dict[str, list[dict]]]:
    """Personal authors with enough text on both sides of a gap: {author: {early, late}}."""
    from classic.corpus_run import eligible

    ts = cfg["timesplit"]
    out = {}
    for a, works in eligible(cfg).items():
        works = sorted(works, key=lambda w: w["year"])
        for i in range(1, len(works)):
            early, late = works[:i], works[i:]
            if late[0]["year"] - early[-1]["year"] >= ts["min_gap_years"]:
                out[a] = {"early": early, "late": late}
                break
    return out


def _text_tokens(rows: list[dict], limit: int) -> list[str]:
    from ocr_fix.normalize import norm_path

    toks: list[str] = []
    for r in rows:
        if len(toks) >= limit:
            break
        toks += tokenize(norm_path(r).read_text(encoding="utf-8", errors="replace"))
    return toks[:limit]


def candidate_text() -> dict[tuple[str, str], list[str]]:
    """Masked tokens per (candidate, period), admitted provenance tiers only."""
    from kjv_mask.run import _docs
    from ocr_fix.candidates import units
    from segment.build import original_words

    meta = {
        "cand:" + u["unit"].replace(":", "__"): (u["author"], u["sample"], u["period"])
        for u in units()
    }
    spans = {}
    for ln in Path("data/kjv_mask/candidates/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    out: dict[tuple[str, str], list[str]] = defaultdict(list)
    for d in _docs("candidates"):
        if d["id"] in meta:
            who, sample, period = meta[d["id"]]
        else:
            person, sample, period = d["id"].removeprefix("cand:").split("__")
            who = person.replace("-", " ").title()
        if sample not in ADMITTED:
            continue
        out[who, period] += tokenize(" ".join(original_words(d["load"](), spans.get(d["id"], []))))
    return out


def _accuracy(
    tests: dict[str, list[str]], refs: dict[str, list[list[str]]], cfg: dict, rng: random.Random
) -> dict:
    """Attribute each test among ``refs``; per method, the share named correctly."""
    kw = classic_kwargs(cfg)
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    per = {}
    for a, toks in tests.items():
        pred = _attribute(toks, refs, top_n, kw, rng)
        per[a] = {m: pred[m] == a if pred[m] is not None else None for m in METHODS}
    acc = {
        m: (
            sum(v[m] for v in per.values() if v[m] is not None)
            / max(1, sum(v[m] is not None for v in per.values()))
        )
        for m in METHODS
    }
    return {"accuracy": acc, "per_author": per, "n": len(tests)}


def run() -> int:
    cfg = load_config()
    ts, pw = cfg["timesplit"], cfg["power"]
    rng = random.Random(derive_seed("timesplit", cfg))
    test_words = pw["fixed_test_words"]

    # baseline
    pool = baseline_authors(cfg)
    ok = {}
    for a, sides in pool.items():
        e = _text_tokens(sides["early"], ts["min_words"] * 2)
        late = _text_tokens(sides["late"], ts["min_words"] * 2)
        if len(e) >= ts["min_words"] and len(late) >= ts["min_words"]:
            ok[a] = {
                "early": e,
                "late": late,
                "gap": sides["late"][0]["year"] - sides["early"][-1]["year"],
            }  # noqa: E501
    authors = sorted(rng.sample(sorted(ok), min(ts["authors"], len(ok))))
    print(
        f"{len(pool):,} authors span a {ts['min_gap_years']}+ year gap; {len(ok):,} with "
        f"{ts['min_words']:,}+ words each side; {len(authors)} drawn",
        flush=True,
    )

    def mid(toks: list[str]) -> list[str]:
        s = max(0, len(toks) // 2 - test_words // 2)
        return toks[s : s + test_words]

    base = {}
    for direction, (src, ref) in {
        "late_profile_early_test": ("early", "late"),
        "early_profile_late_test": ("late", "early"),
    }.items():
        tests = {a: mid(ok[a][src]) for a in authors}
        refs = {a: blocks(ok[a][ref]) for a in authors}
        base[direction] = _accuracy(tests, refs, cfg, rng)

    # candidates
    ct = candidate_text()
    words = {f"{c} {p}": len(t) for (c, p), t in sorted(ct.items())}
    both = sorted({c for c, p in ct if p == "pre1830"} & {c for c, p in ct if p == "post1830"})
    post = sorted(c for c, p in ct if p == "post1830" and len(ct[c, p]) >= BLOCK * 2)
    pre = sorted(c for c, p in ct if p == "pre1830" and len(ct[c, p]) >= BLOCK * 2)
    cand = {
        "late_profile_early_test": _accuracy(
            {c: ct[c, "pre1830"] for c in both},
            {c: blocks(ct[c, "post1830"]) for c in post},
            cfg,
            rng,
        ),
        "early_profile_late_test": _accuracy(
            {c: mid(ct[c, "post1830"]) for c in both},
            {c: blocks(ct[c, "pre1830"]) for c in pre},
            cfg,
            rng,
        ),
    }
    floor = max(cfg["power"]["reference_floor_words"].values())
    result = {
        **stamp(),
        "baseline": {
            "authors": authors,
            "gaps": {a: ok[a]["gap"] for a in authors},
            "chance": 1 / len(authors),
            **base,
        },
        "candidates": {
            "words": words,
            "both_sides": both,
            "post1830_profiles": post,
            "pre1830_profiles": pre,
            "reference_floor_words": floor,
            **cand,
            "note": "pre-1830 samples are below the reference floor; the early-profile direction "
            "is reported but is below the floor",
        },
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    for d in base:
        print(f"baseline {d}: " + ", ".join(f"{m} {v:.0%}" for m, v in base[d]["accuracy"].items()))
    for d in cand:
        print(f"candidates {d}: " + json.dumps(cand[d]["per_author"]))
    print(f"candidate words {words}\n-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
