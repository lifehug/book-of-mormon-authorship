"""The Bayesian synthesis (BOM-35; pre-registration 6.7, Amendment 7; ``docs/synthesis-plan.md``).

Hypotheses: each candidate with a reliable confirmatory sample, and "not in set". Each method
family (classical: General Imposters; embedding: the style fingerprints; authorial: the candidate
language models) contributes, per Book of Mormon chunk, one observation: the hypothesis candidate it
ranks first and 6.1's call for that candidate (match, inconclusive, non-match). Its likelihood comes
from the family's benchmark behaviour only:

    L(c) = [a if first == c else (1 - a) / (K - 1)] * P(call | true author)    if first == c
                                                    * P(call | not the author) otherwise
    L(none) = (1 / K) * P(call | not the author)

with ``a`` the family's closed-set accuracy, ``K`` the number of candidate hypotheses, and the call
rates the shares of the benchmark's positives and open-set negatives in each band (smoothed by
``synthesis.smoothing``). A half's evidence from a family is the mean of its chunks' log
likelihoods (the half counts as one observation: chunks are not independent). The posterior is

    log P(h | half) = log prior(h) + sum over families of w_f * mean_chunks log L_f(h) + const

with prior ``synthesis.prior_none`` on "not in set" and the rest shared equally among candidates,
and ``w_f`` the family's closed-set accuracy times its section 9 imitation weight (BOM-31). Both
halves together add the two halves' evidence. Sensitivity: the prior on "not in set" over
``synthesis.prior_grid``, each family dropped in turn, equal weights (Amendment 7), chunks
treated as independent (an upper bound on confidence), and the secondary candidates (post-1830
samples, Amendment 5). Dating, the sweep, access (BOM-33) and manuscript evidence (BOM-34) are
reported beside the posterior, not multiplied into it.

``rates`` writes each family's accuracy and call rates from benchmark data only; ``run`` reads
``data/blind/unblinded.json``. Names and numbers only, to ``data/synthesis/``.

Usage::

    python -m synth.model rates base|large   # -> data/synthesis/rates.json
    python -m synth.model run [--unblinded data/blind/unblinded.json]   # -> posterior.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from metadata.config import load as load_config
from metadata.config import stamp

OUT = Path("data/synthesis")
BENCH = Path("data/benchmark")
PLAN = BENCH / "alm_candidates_plan.json"
NONE = "not in set"
BANDS = ("match", "inconclusive", "non_match")
FAMILIES = ("classical", "embedding", "authorial")
# the method whose imitation weight (BOM-31) applies to each family
IMITATION_METHOD = {"classical": "general_imposters", "embedding": "style", "authorial": "alm"}


# ---- benchmark rates -----------------------------------------------------------------------------


def band_rates(pos: list[float], neg: list[float], th: dict, smooth: float) -> dict:
    """Shares of benchmark positives and negatives in each 6.1 band, add-``smooth`` smoothed."""
    from blind.thresholds import call

    out = {}
    for name, xs in (("pos", pos), ("neg", neg)):
        n = {b: smooth for b in BANDS}
        for x in xs:
            n[call(x, th)] += 1
        tot = sum(n.values())
        out[name] = {b: v / tot for b, v in n.items()}
    return out


def rates(size: str) -> int:
    """Each family's closed-set accuracy and call rates, from benchmark data only."""
    from blind.thresholds import alm_scores
    from blind.thresholds import load as thresholds

    cfg = load_config()
    sm = cfg["synthesis"]["smoothing"]
    th = thresholds()
    bench = json.loads((BENCH / "benchmark.json").read_text())
    recs = [r for rs in bench["records"].values() for r in rs]
    style = json.loads((BENCH / "style_embed.json").read_text())
    srecs = [r for rs in style["records"].values() for r in rs]
    fam = {
        "classical": {"accuracy": bench["verdict"]["general_imposters"]["closed_set"],
                      **band_rates([r["gi_positive"] for r in recs],
                                   [r["gi_open_negative"] for r in recs
                                    if r["gi_open_negative"] is not None],
                                   th["general_imposters"], sm)},
        "embedding": {"accuracy": style["verdict"]["closed_set"],
                      **band_rates([r["positive"] for r in srecs],
                                   [r["open_negative"] for r in srecs
                                    if r["open_negative"] is not None], th["style"], sm)},
    }  # fmt: skip
    cand = BENCH / f"alm_candidates_{size}.json"
    if cand.exists() and th.get("alm"):
        d = json.loads(cand.read_text())
        kinds = {u["key"]: u["kind"] for u in json.loads(PLAN.read_text())["units"]}
        pos, neg = alm_scores(d["records"], kinds)
        tested = [v for v in d["units"].values() if "closed_set_candidates" in v and v["tests"]]
        acc = sum(v["closed_set_candidates"] * v["tests"] for v in tested) / max(
            1, sum(v["tests"] for v in tested)
        )  # held-out windows, among candidates
        fam["authorial"] = {"accuracy": acc,
                            **band_rates(pos, neg, th["alm"], sm)}  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rates.json").write_text(json.dumps({**stamp(), "size": size, "families": fam},
                                               indent=1) + "\n")  # fmt: skip
    print(f"rates -> {OUT / 'rates.json'}: " + ", ".join(
        f"{k} a={v['accuracy']:.3f}" for k, v in fam.items()))  # fmt: skip
    return 0


# ---- the model -----------------------------------------------------------------------------------


def hypotheses(plan: dict, secondary: bool = False) -> tuple[list[str], dict[str, str]]:
    """(candidate hypotheses, unit -> candidate) from reliable samples: confirmatory (pre-1830)
    units, or every reliable unit when ``secondary``."""
    units = {u["key"]: u["candidate"] for u in plan["units"]
             if u["kind"] == "candidate" and not u["flag"]
             and (u["confirmatory"] or secondary)}  # fmt: skip
    return sorted(set(units.values())), units


def chunk_loglik(first: str, band: str, a: float, r: dict, cands: list[str]) -> dict[str, float]:
    """log L(h) for one chunk's observation under one family (module docstring)."""
    k = len(cands)
    out = {}
    for c in cands:
        pick = a if first == c else (1 - a) / (k - 1) if k > 1 else 1.0
        out[c] = math.log(pick) + math.log(r["pos" if first == c else "neg"][band])
    out[NONE] = math.log(1 / k) + math.log(r["neg"][band])
    return out


def evidence(obs: list[tuple[str, str]], a: float, r: dict, cands: list[str],
             independent: bool = False) -> dict[str, float]:  # fmt: skip
    """A family's evidence from a half: mean (or, as an upper bound, sum) of chunk log L."""
    if not obs:
        return dict.fromkeys([*cands, NONE], 0.0)
    ll = [chunk_loglik(f, b, a, r, cands) for f, b in obs]
    agg = sum if independent else (lambda xs: sum(xs) / len(xs))
    return {h: agg([x[h] for x in ll]) for h in [*cands, NONE]}


def posterior(ev: dict[str, dict[str, float]], weights: dict[str, float], cands: list[str],
              prior_none: float) -> dict[str, float]:  # fmt: skip
    """Normalised posterior over the candidates and "not in set"."""
    prior = {c: (1 - prior_none) / len(cands) for c in cands} | {NONE: prior_none}
    logp = {h: math.log(prior[h]) + sum(weights.get(f, 0.0) * e[h] for f, e in ev.items())
            for h in prior}  # fmt: skip
    top = max(logp.values())
    z = sum(math.exp(v - top) for v in logp.values())
    return {h: math.exp(v - top) / z for h, v in logp.items()}


def observations(methods: dict, units: dict[str, str], split: dict[str, str]
                 ) -> dict[str, dict[str, list[tuple[str, str]]]]:  # fmt: skip
    """half -> family -> [(first hypothesis candidate, its 6.1 band)] per Book of Mormon chunk,
    from ``blind.unblind``'s per-chunk records (``methods[m]['bom'][chunk_id]``)."""
    out: dict[str, dict[str, list]] = {"discovery": {}, "confirmation": {}}

    def add(half: str, fam: str, scores: dict[str, float], calls: dict[str, str],
            lower: bool) -> None:  # fmt: skip
        s = {u: v for u, v in scores.items() if u in units}
        if not s:
            return
        u = min(s, key=lambda x: (s[x], x)) if lower else max(s, key=lambda x: (s[x], x))
        out[half].setdefault(fam, []).append((units[u], calls[u]))

    for chunk, rec in (methods.get("classic") or {}).get("bom", {}).items():
        if chunk in split:
            add(split[chunk], "classical", rec["general_imposters"], rec["gi_call"], False)
    for chunk, rec in (methods.get("style") or {}).get("bom", {}).items():
        if chunk in split:
            add(split[chunk], "embedding", rec["cosine"], rec["call"], True)
    for chunk, rec in (methods.get("alm") or {}).get("bom", {}).items():
        if chunk in split and rec.get("call"):
            add(
                split[chunk],
                "authorial",
                {u: -v for u, v in rec["margins"].items()},
                rec["call"],
                True,
            )  # larger margin is closer
    return out


def weights(fams: dict, imitation: dict, equal: bool = False) -> dict[str, float]:
    """w_f = closed-set accuracy x section 9 weight; equal weights (Amendment 7) are 1 each."""
    out = {}
    for f, r in fams.items():
        m = imitation.get("methods", {}).get(IMITATION_METHOD[f])
        if m is None:
            raise SystemExit(f"no BOM-31 imitation weight for {f} ({IMITATION_METHOD[f]})")
        out[f] = 1.0 if equal else r["accuracy"] * m["weight"]
    return out


def synthesise(obs: dict, fams: dict, w: dict[str, float], cands: list[str], cfg: dict,
               independent: bool = False) -> dict:  # fmt: skip
    """Posteriors for each half and both, at the registered prior and over the prior grid."""
    s = cfg["synthesis"]
    ev = {half: {f: evidence(o, fams[f]["accuracy"], fams[f], cands, independent)
                 for f, o in by.items() if f in fams}
          for half, by in obs.items()}  # fmt: skip
    ev["both"] = {f: {h: sum(ev[x].get(f, {}).get(h, 0.0) for x in ("discovery", "confirmation"))
                      for h in [*cands, NONE]} for f in fams}  # fmt: skip
    return {half: {"posterior": posterior(e, w, cands, s["prior_none"]),
                   "prior_grid": {str(p): posterior(e, w, cands, p) for p in s["prior_grid"]},
                   "by_family": {f: posterior({f: e[f]}, {f: 1.0}, cands, s["prior_none"])
                                 for f in e}}
            for half, e in ev.items()}  # fmt: skip


def run(unblinded: Path) -> int:
    cfg = load_config()
    fams = json.loads((OUT / "rates.json").read_text())["families"]
    imitation = json.loads((BENCH / "imitation.json").read_text())
    methods = json.loads(unblinded.read_text())["methods"]
    split = json.loads(Path("data/bom/segments/split.json").read_text())["assignment"]
    plan = json.loads(PLAN.read_text())
    res: dict = {**stamp(), "hypotheses": {}, "beside": {}}
    for label, secondary in (("primary", False), ("secondary", True)):
        cands, units = hypotheses(plan, secondary)
        obs = observations(methods, units, split)
        w = weights(fams, imitation)
        r = {"candidates": cands, "weights": w, "main": synthesise(obs, fams, w, cands, cfg),
             "equal_weights": synthesise(obs, fams, weights(fams, imitation, True), cands, cfg),
             "independent_chunks": synthesise(obs, fams, w, cands, cfg, independent=True),
             "drop_one": {f: synthesise(obs, fams, {**w, f: 0.0}, cands, cfg) for f in fams},
             "chunks": {h: {f: len(o) for f, o in b.items()} for h, b in obs.items()}}  # fmt: skip
        res["hypotheses"][label] = r
    for m in ("dating", "sweep"):
        if m in methods:
            res["beside"][m] = methods[m] if m == "sweep" else "see data/blind/unblinded.json"
    acc = Path("data/access/access_table.csv")
    res["beside"]["access"] = str(acc) if acc.exists() else None
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posterior.json").write_text(json.dumps(res, indent=1) + "\n")
    p = res["hypotheses"]["primary"]["main"]["both"]["posterior"]
    print("posterior (primary, both halves): " + ", ".join(
        f"{h} {v:.3f}" for h, v in sorted(p.items(), key=lambda kv: -kv[1])))  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rates")
    r.add_argument("size", choices=["pilot", "base", "large"])
    u = sub.add_parser("run")
    u.add_argument("--unblinded", type=Path, default=Path("data/blind/unblinded.json"))
    a = ap.parse_args(argv)
    return rates(a.size) if a.cmd == "rates" else run(a.unblinded)


if __name__ == "__main__":
    sys.exit(main())
