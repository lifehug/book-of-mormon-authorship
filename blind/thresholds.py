"""6.1's per-method thresholds for the blind run, calibrated on benchmark data only (BOM-32).

6.1: a method returns *match* for a candidate when its verification score exceeds the score
with a 5% false-positive rate on open-set negatives, *non-match* below the score with a 5%
false-negative rate on positives, and *inconclusive* between (``eval.benchmark.calibrate_gi``,
rate ``benchmark.max_open_set_fpr``). The thresholds come from:

- **General Imposters:** ``data/benchmark/thresholds.json`` (BOM-21, already committed);
- **style embeddings:** the GI-on-vectors positives and open-set negatives of
  ``data/benchmark/style_embed.json`` (BOM-30's benchmark run);
- **authorial models,** one set per model size (pilot, base, large: every size runs every test,
  owner 2026-11-06): the margins (best control model minus candidate model) on the candidates'
  held-out windows in ``data/benchmark/alm_candidates_<size>.json`` (Amendment 30): positives the
  true candidate's margin on its own windows, negatives each window's largest margin of any other
  candidate (on control windows, of any candidate). A size not yet validated gets ``null``.

Beside each 5% threshold, a **ladder** (owner, 2026-11-07: objective data, not one rule): for each
false-match rate in ``blind.fpr_ladder`` the match threshold on the same negatives, with the
false-match and true-match rates it actually has on the benchmark (ties make them differ from the
nominal rate). ``rung`` gives the lowest rate at which a score counts as a match.

No Book of Mormon text is read. The file is committed before the blind run (6.1).

Usage::

    python -m blind.thresholds [pilot base mid]   # -> data/blind/thresholds.json (merged by size)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from metadata.config import stamp

BENCH = Path("data/benchmark")
OUT = Path("data/blind/thresholds.json")


def calibrate(pos: list[float], neg: list[float], rate: float) -> dict:
    from eval.benchmark import calibrate_gi

    return {**calibrate_gi(pos, neg, rate), "positives": len(pos), "negatives": len(neg)}


def ladder(pos: list[float], neg: list[float], rates: list[float]) -> list[dict]:
    """For each nominal false-match rate: the threshold (the 1 - rate quantile of the negatives)
    and the rates a score at or above it actually has on the benchmark."""
    import numpy as np

    p, n = np.asarray(pos, dtype=float), np.asarray(neg, dtype=float)
    out = []
    for r in sorted(rates):
        t = float(np.quantile(n, 1 - r))
        out.append({"rate": r, "threshold": t, "false_match": float(np.mean(n >= t)),
                    "true_match": float(np.mean(p >= t)) if len(p) else None})  # fmt: skip
    return out


def rung(score: float, steps: list[dict]) -> dict | None:
    """The lowest rung at which ``score`` counts as a match (at or above its threshold): nominal
    rate, threshold, and the false- and true-match rates it really has on the benchmark (ties can
    make the real false-match rate higher than the nominal: General Imposters' 1%, 5% and 10% rungs
    share the threshold 1.0). None if it matches at no rung."""
    for st in sorted(steps, key=lambda st: st["rate"]):
        if score >= st["threshold"]:
            return st
    return None


def call(score: float, th: dict, rule: str = "registered") -> str:
    """6.1's three-way call for one candidate. ``registered``: match only above the 5% threshold;
    ``achievable`` (owner, 2026-11-07; Amendment 33 (b)): match at or above it, for methods whose
    threshold is the highest score possible. Every output carries both, read side by side."""
    if score > th["match"] or (rule == "achievable" and score >= th["match"]):
        return "match"
    if score < th["non_match"]:
        return "non_match"
    return "inconclusive"


def alm_scores(recs: list[dict], kinds: dict[str, str]) -> tuple[list[float], list[float]]:
    """(positives, negatives) from ``alm.candidates validate`` records."""
    pos, neg = [], []
    for r in recs:
        m = r["margins"]
        if kinds.get(r["unit"]) == "candidate":
            pos.append(m[r["unit"]])
            others = [v for u, v in m.items() if u != r["unit"]]
        else:
            others = list(m.values())
        if others:
            neg.append(max(others))
    return pos, neg


SIZES = ("pilot", "base", "mid")  # the 1B was dropped for a 590M (Amendment 39)


def alm_threshold(size: str, rate: float, rates: list[float]) -> dict | None:
    cand = BENCH / f"alm_candidates_{size}.json"
    if not cand.exists():
        return None  # BOM-28's candidate models not validated at this size yet
    d = json.loads(cand.read_text())
    plan = json.loads((BENCH / "alm_candidates_plan.json").read_text())
    kinds = {u["key"]: u["kind"] for u in plan["units"]}
    pos, neg = alm_scores(d["records"], kinds)
    return {**calibrate(pos, neg, rate), "ladder": ladder(pos, neg, rates), "source": cand.name}


def _size_order(z: str) -> tuple[int, str]:
    return (SIZES.index(z) if z in SIZES else len(SIZES), z)


def merge_doc(old: dict | None, new: dict) -> dict:
    """``new`` (a run over some sizes) laid over ``old``: every authorial-model size ``old`` has
    and ``new`` did not compute is kept, so the sizes can be added one at a time (the 590M's comes
    from its own pod, 2026-11-08). A size ``new`` left ``null`` (not validated) does not erase a
    value ``old`` has. General Imposters, style and ENSC come from ``new`` (the same benchmark
    files give the same numbers)."""
    if not old:
        return new
    o_alm = (old.get("thresholds") or {}).get("alm") or {}
    n_alm = new["thresholds"].get("alm") or {}
    alm = {**o_alm, **{z: v for z, v in n_alm.items() if v is not None or z not in o_alm}}
    alm = dict(sorted(alm.items(), key=lambda kv: _size_order(kv[0])))
    sizes = sorted(set(old.get("sizes", [])) | set(new.get("sizes", [])), key=_size_order)
    return {**new, "sizes": sizes, "thresholds": {**new["thresholds"], "alm": alm}}


def add_size(local: dict, pod: dict, size: str) -> dict:
    """The Mac's thresholds with one size's authorial-model entry taken from a pod's file; every
    other entry (GI, style, ENSC, the other sizes, the stamp) stays the Mac's own."""
    entry = ((pod.get("thresholds") or {}).get("alm") or {}).get(size)
    if entry is None:
        raise ValueError(f"the pod's thresholds have no {size} entry")
    made = {k: pod.get(k) for k in ("git_commit", "config_sha256")}
    alm = {size: {**entry, "computed": made}}
    new = {**local, "sizes": [size], "thresholds": {**local["thresholds"], "alm": alm}}
    return merge_doc(local, new)


def run(sizes: list[str]) -> int:
    from metadata.config import load as load_config

    cfg = load_config()
    rate = cfg["benchmark"]["max_open_set_fpr"]
    rates = cfg["blind"]["fpr_ladder"]
    gi = json.loads((BENCH / "thresholds.json").read_text())
    bench = json.loads((BENCH / "benchmark.json").read_text())
    grecs = [r for rs in bench["records"].values() for r in rs]
    style = json.loads((BENCH / "style_embed.json").read_text())
    srecs = [r for rs in style["records"].values() for r in rs]
    spos = [r["positive"] for r in srecs]
    sneg = [r["open_negative"] for r in srecs if r["open_negative"] is not None]
    th = {"general_imposters": {**gi["general_imposters"], "source": "thresholds.json",
                                "ladder": ladder([r["gi_positive"] for r in grecs
                                                  if r.get("gi_positive") is not None],
                                                 [r["gi_open_negative"] for r in grecs
                                                  if r.get("gi_open_negative") is not None],
                                                 rates)},
          "ensc": gi["ensc"],
          "style": {**calibrate(spos, sneg, rate), "ladder": ladder(spos, sneg, rates),
                    "source": "style_embed.json"}}  # fmt: skip
    for f in sorted(BENCH.glob("style_embed_*.json")):  # another backbone's encoder, if run
        d = json.loads(f.read_text())
        rs = [r for rs in d["records"].values() for r in rs]
        p, n = [r["positive"] for r in rs], [r["open_negative"] for r in rs
                                             if r["open_negative"] is not None]  # fmt: skip
        th[f"style_{d['size']}"] = {**calibrate(p, n, rate), "ladder": ladder(p, n, rates),
                                    "source": f.name}  # fmt: skip
    th["alm"] = {z: alm_threshold(z, rate, rates) for z in sizes}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {**stamp(), "sizes": sizes, "rate": rate, "fpr_ladder": rates, "thresholds": th}
    old = json.loads(OUT.read_text()) if OUT.exists() else None
    doc = merge_doc(old, doc)  # one size at a time never drops the others
    th = doc["thresholds"]
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    shown = {k: v for k, v in th.items() if k != "alm"} | {
        f"alm_{z}": v for z, v in th["alm"].items()}  # fmt: skip
    print(f"thresholds -> {OUT}: " + ", ".join(
        f"{k} {v.get('match')}/{v.get('non_match')}" if isinstance(v, dict) and "match" in v
        else f"{k} not yet" for k, v in shown.items() if k != "ensc"))  # fmt: skip
    return 0


def load(size: str | None = None) -> dict:
    """The thresholds; with ``size``, ``alm`` is that size's (``None`` if not validated)."""
    if not OUT.exists():
        raise SystemExit(f"{OUT} missing: run python -m blind.thresholds and commit it")
    th = json.loads(OUT.read_text())["thresholds"]
    if size is not None:
        alm = th.get("alm")
        th = {**th, "alm": alm.get(size) if isinstance(alm, dict) and "match" not in alm
              else alm}  # fmt: skip
    return th


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("sizes", nargs="*", help="pilot, base, large (default: all three)")
    sizes = ap.parse_args(argv).sizes or list(SIZES)
    bad = [z for z in sizes if z not in SIZES]
    if bad:
        ap.error(f"unknown size(s) {bad}; choose from {SIZES}")
    return run(sizes)


if __name__ == "__main__":
    sys.exit(main())
