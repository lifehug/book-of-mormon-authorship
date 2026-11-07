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

No Book of Mormon text is read. The file is committed before the blind run (6.1).

Usage::

    python -m blind.thresholds [pilot base large]   # -> data/blind/thresholds.json
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


def alm_threshold(size: str, rate: float) -> dict | None:
    cand = BENCH / f"alm_candidates_{size}.json"
    if not cand.exists():
        return None  # BOM-28's candidate models not validated at this size yet
    d = json.loads(cand.read_text())
    plan = json.loads((BENCH / "alm_candidates_plan.json").read_text())
    kinds = {u["key"]: u["kind"] for u in plan["units"]}
    pos, neg = alm_scores(d["records"], kinds)
    return {**calibrate(pos, neg, rate), "source": cand.name}


def run(sizes: list[str]) -> int:
    from metadata.config import load as load_config

    cfg = load_config()
    rate = cfg["benchmark"]["max_open_set_fpr"]
    gi = json.loads((BENCH / "thresholds.json").read_text())
    style = json.loads((BENCH / "style_embed.json").read_text())
    srecs = [r for rs in style["records"].values() for r in rs]
    th = {"general_imposters": {**gi["general_imposters"], "source": "thresholds.json"},
          "ensc": gi["ensc"],
          "style": {**calibrate([r["positive"] for r in srecs],
                                [r["open_negative"] for r in srecs
                                 if r["open_negative"] is not None], rate),
                    "source": "style_embed.json"}}  # fmt: skip
    th["alm"] = {z: alm_threshold(z, rate) for z in sizes}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({**stamp(), "sizes": sizes, "rate": rate, "thresholds": th},
                              indent=1) + "\n")  # fmt: skip
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
