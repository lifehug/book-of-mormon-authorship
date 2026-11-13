"""Amendment 55 (post hoc): counting by author, the normalised verification curve, chunks by length.

Saved scores only; no model is trained and no text is read.

- ``head-to-head``: Amendment 52's 12 comparisons (three sizes against Burrows' and Cosine Delta,
  General Imposters and ENSC on BOM-75's 430 held-out tests) with the author as the unit: an author
  counts for the side that wins more of its disagreements; exact two-sided sign test over untied
  authors, Holm over the 12; the accuracy gap with a 95% interval from resampling authors.
- ``curve``: for each size, the verification trade-off on the 430 tests for the statistics fixed
  in ``prior_work.verification`` (raw, z-norm, z-margin), leave one author out: the held-out
  author's tests are excluded from every normalisation mean and spread and from the threshold.
  At each target false-match rate (and at Amendment 25's 95%-of-true-authors point): held-out
  false matches and true authors confirmed (ranked first and above threshold), Wilson and
  author-resampled intervals; area under the curve and equal-error rate.
- ``by-length``: the people-only rankings of Amendments 53 and 54 counted separately on the
  2,000- and 5,000-word sealed chunks (the book is cut twice).

Writes ``data/benchmark/clustered.json`` and ``data/blind/a55_by_length.json``. Usage::

    python -m eval.clustered head-to-head
    python -m eval.clustered head-to-head --ext   # Amendment 56: all 55 authors
    python -m eval.clustered curve
    python -m eval.clustered by-length
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

import numpy as np

from metadata.config import load as load_config
from metadata.config import stamp

DIR = Path("data/benchmark")
OUT = DIR / "clustered.json"
SIZES = ("pilot", "base", "mid")
METHODS = ("burrows_delta", "cosine_delta", "general_imposters", "ensc")


def sign_p(w: int, lose: int) -> float:
    """Exact two-sided sign test over ``w + lose`` untied units."""
    n = w + lose
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(w, lose) + 1)) / 2**n)


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i]))
        adj[i] = run
    return adj


def _tests(size: str) -> list[tuple[str, dict]]:
    recs = json.loads((DIR / f"alm_{size}_p2.json").read_text())["records"]
    return [(t, r) for t, rs in recs.items() for r in rs]


def _merge(out: dict) -> None:
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps({**old, **stamp(), **out}, indent=1) + "\n")


def _pairs_h2h(size: str, suffix: str) -> list[tuple[str, dict, dict]]:
    """(task, our record, the classical record) for every test of one benchmark set, in order."""
    classic = [r for rs in json.loads((DIR / f"prior_work_classic_tails_{suffix}.json")
               .read_text())["records"].values() for r in rs]  # fmt: skip
    recs = json.loads((DIR / f"alm_{size}_{suffix}.json").read_text())["records"]
    tests = [(t, r) for t, rs in recs.items() for r in rs]
    assert len(tests) == len(classic)
    assert all(c["author"] == r["author"] for c, (_, r) in zip(classic, tests, strict=True))
    return [(t, r, c) for (t, r), c in zip(tests, classic, strict=True)]


def _h2h(sets: tuple[str, ...], cfg: dict) -> list[dict]:
    """The 12 comparisons by author over the benchmark sets ``sets``, Holm over the 12."""
    rows = []
    for size in SIZES:
        pairs = [x for s in sets for x in _pairs_h2h(size, s)]
        for m in METHODS:
            per: dict[tuple, list[int]] = defaultdict(lambda: [0, 0, 0])
            for task, r, c in pairs:
                ours, theirs = r["predicted"] == r["author"], c[m] == c["author"]
                a = per[task, r["author"]]
                a[0] += ours and not theirs
                a[1] += theirs and not ours
                a[2] += 1
            w = sum(v[0] > v[1] for v in per.values())
            lo = sum(v[1] > v[0] for v in per.values())
            keys = list(per)
            rng = random.Random(cfg["seed"])
            diffs = []
            for _ in range(cfg["resamples"]):
                ks = [keys[rng.randrange(len(keys))] for _ in keys]
                diffs.append(sum(per[k][0] - per[k][1] for k in ks) / sum(per[k][2] for k in ks))
            top = sorted(per.items(), key=lambda kv: -(kv[1][0] - kv[1][1]))[:3]
            rows.append({"size": size, "method": m, "authors": len(per), "ours_ahead": w,
                         "theirs_ahead": lo, "tied": len(per) - w - lo, "sign_p": sign_p(w, lo),
                         "windows": [sum(v[0] for v in per.values()),
                                     sum(v[1] for v in per.values())],
                         "accuracy_gap": sum(v[0] - v[1] for v in per.values()) / len(pairs),
                         "gap_95": [float(x) for x in np.quantile(diffs, [0.025, 0.975])],
                         "largest": [[k[1], v[0], v[1]] for k, v in top]})  # fmt: skip
    for r, p in zip(rows, holm([r["sign_p"] for r in rows]), strict=True):
        r["holm_p"] = p
        side = "ours better" if r["ours_ahead"] > r["theirs_ahead"] else "theirs better"
        r["reading"] = side if p < cfg["alpha"] else "no difference shown"
        print(f"{r['size']:5} vs {r['method']:17} authors {r['ours_ahead']}-{r['theirs_ahead']}"
              f" (tied {r['tied']}), windows {r['windows'][0]}-{r['windows'][1]}, sign p "
              f"{r['sign_p']:.4f}, Holm {p:.4f}, gap {r['accuracy_gap']:+.3f} "
              f"[{r['gap_95'][0]:+.3f}, {r['gap_95'][1]:+.3f}] -> {r['reading']}")  # fmt: skip
    return rows


def head_to_head(ext: bool = False) -> int:
    """Amendment 55 on BOM-75's 23 authors; with ``ext``, Amendment 56's test on all 55 authors
    (the decision), with the 32 new and the 23 alone beside it."""
    cfg = load_config()["prior_work"]["by_author"]
    if not ext:
        _merge({"head_to_head_by_author": _h2h(("p2",), cfg)})
    else:
        out = {}
        for label, sets in (("all_55", ("p2", "p3")), ("new_32", ("p3",)), ("bom75_23", ("p2",))):
            print(f"== {label}")
            out[label] = _h2h(sets, cfg)
        _merge({"head_to_head_by_author_a56": out})
    print(f"-> {OUT}")
    return 0


def _stat(x: dict[str, float], kind: str, zs: dict | None) -> float:
    """``x``: closeness per candidate (higher is closer). Top statistic of the dict."""
    if kind == "raw":
        return max(x.values())
    z = {m: (v - zs[m][0]) / zs[m][1] for m, v in x.items()}
    top = sorted(z.values(), reverse=True)
    if kind == "znorm":
        return top[0]
    return top[0] - top[1] if len(top) > 1 else top[0]


def _zstats(tests: list[tuple[str, dict]], task: str, held: str) -> dict | None:
    """Per candidate model of ``task``: mean and spread of its closeness on tests by other
    authors, the held-out author's tests excluded."""
    out = {}
    rows = [r for t, r in tests if t == task and r["author"] != held]
    for m in tests[[t for t, _ in tests].index(task)][1]["scores"]:
        v = [-r["scores"][m] for r in rows if r["author"] != m]
        if len(v) < 2 or np.std(v) == 0:
            return None
        out[m] = (float(np.mean(v)), float(np.std(v, ddof=1)))
    return out


def _pairs(tests, kind: str, held: str, zcache: dict) -> list[tuple[float, float, bool, str]]:
    """(positive statistic, negative statistic, ranked first, author) per test, normalised
    with statistics that exclude ``held``; None when a task cannot be normalised."""
    out = []
    for t, r in tests:
        zs = None
        if kind != "raw":
            key = (t, held)
            if key not in zcache:
                zcache[key] = _zstats(tests, t, held)
            zs = zcache[key]
            if zs is None:
                continue
        x = {m: -s for m, s in r["scores"].items()}
        neg = {m: v for m, v in x.items() if m != r["author"]}
        out.append((_stat(x, kind, zs), _stat(neg, kind, zs), r["predicted"] == r["author"],
                    f"{t}|{r['author']}"))  # fmt: skip
    return out


def _auc_eer(pos: list[float], neg: list[float]) -> tuple[float, float]:
    p, n = np.array(pos), np.array(neg)
    auc = float((p[:, None] > n[None, :]).mean() + 0.5 * (p[:, None] == n[None, :]).mean())
    ts = np.unique(np.concatenate([p, n]))
    fr = np.array([(n > t).mean() for t in ts])
    mr = np.array([(p <= t).mean() for t in ts])
    i = int(np.argmin(np.abs(fr - mr)))
    return auc, float((fr[i] + mr[i]) / 2)


def curve() -> int:
    from eval.open_set import wilson

    cfg = load_config()["prior_work"]
    vc, bc = cfg["verification"], cfg["by_author"]
    res: dict = {}
    for size in SIZES:
        tests = _tests(size)
        authors = sorted({f"{t}|{r['author']}" for t, r in tests})
        res[size] = {}
        for kind in vc["statistics"]:
            for subset in ["all", "no_dictated"] if kind == "raw" else ["normalisable"]:
                ts = [x for x in tests if subset == "all" or x[0] != "dictated"]
                zc: dict = {}
                held_rows, per_author = [], defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
                points = [*vc["target_false_match"], "registered_95"]
                counts = {str(f): [0, 0, 0] for f in points}  # false matches, confirmed, tests
                for a in authors:
                    task, name = a.split("|", 1)
                    if subset != "all" and task == "dictated":
                        continue
                    rows = _pairs(ts, kind, name, zc)
                    cal = [x for x in rows if x[3] != a]
                    ev = [x for x in rows if x[3] == a]
                    if not ev or not cal:
                        continue
                    held_rows += ev
                    cneg = np.array([x[1] for x in cal])
                    cpos = np.array([x[0] for x in cal if x[2]] or [np.inf])
                    for f in points:
                        thr = (float(np.quantile(cpos, 0.05)) if f == "registered_95"
                               else float(np.quantile(cneg, 1 - f)))  # fmt: skip
                        fm = sum(x[1] > thr for x in ev)
                        ok = sum(x[2] and x[0] > thr for x in ev)
                        c = counts[str(f)]
                        c[0] += fm
                        c[1] += ok
                        c[2] += len(ev)
                        pa = per_author[str(f)][a]
                        pa[0] += fm
                        pa[1] += ok
                        pa[2] += len(ev)
                if not held_rows:
                    continue
                auc, eer = _auc_eer([x[0] for x in held_rows if x[2]], [x[1] for x in held_rows])
                ops = {}
                rng = random.Random(bc["seed"])
                for f in points:
                    fm, ok, n = counts[str(f)]
                    pa = per_author[str(f)]
                    ks = list(pa)
                    boots = []
                    for _ in range(bc["resamples"]):
                        s = [pa[ks[rng.randrange(len(ks))]] for _ in ks]
                        tot = sum(x[2] for x in s)
                        boots.append((sum(x[0] for x in s) / tot, sum(x[1] for x in s) / tot))
                    b = np.array(boots)
                    ops[str(f)] = {"tests": n, "false_match": fm / n, "false_match_wilson":
                                   wilson(fm, n), "false_match_authors_95":
                                   [float(v) for v in np.quantile(b[:, 0], [0.025, 0.975])],
                                   "confirmed": ok / n, "confirmed_wilson": wilson(ok, n),
                                   "confirmed_authors_95": [float(v) for v in
                                   np.quantile(b[:, 1], [0.025, 0.975])]}  # fmt: skip
                label = kind if subset in ("all", "normalisable") else f"{kind}_{subset}"
                n_auth = len(per_author[str(points[0])])
                res[size][label] = {"tests": len(held_rows), "authors": n_auth,
                                    "auc": auc, "eer": eer, "operating_points": ops}  # fmt: skip
                print(f"{size:5} {label:16} n={len(held_rows)} AUC {auc:.3f} EER {eer:.3f} | "
                      + " | ".join(f"{f}: FM {v['false_match']:.3f} conf {v['confirmed']:.3f}"
                                   for f, v in ops.items()))  # fmt: skip
    _merge({"verification_curve": res})
    print(f"-> {OUT}")
    return 0


def by_length() -> int:
    from eval.js_register import KEY, REVELATION, _scores

    key = json.loads(KEY.read_text())
    length = {i: k["chunk_id"].split(":")[3] for i, k in key.items() if k["kind"] == "bom"}
    out: dict = {"chunks": {n: sum(v == n for v in length.values()) for n in ("2000", "5000")}}
    a54 = Path("data/blind/a54/report.json")
    sources = {"a53": _scores(set(length))}
    if a54.exists():
        from eval.js_later import OUT as A54_OUT

        sources["a54"] = _a54_scores(set(length), A54_OUT)
    for src, methods in sources.items():
        out[src] = {}
        for m, (per, lower) in methods.items():
            out[src][m] = {}
            for label, drop in (("with_revelations", ()), ("without_revelations", (REVELATION,))):
                firsts: dict[str, dict[str, int]] = defaultdict(lambda: {"2000": 0, "5000": 0})
                for i, sc in per.items():
                    c = {u: v for u, v in sc.items() if u.startswith("cand__") and u not in drop}
                    top = min(c, key=c.get) if lower else max(c, key=c.get)
                    firsts[top][length[i]] += 1
                out[src][m][label] = dict(sorted(firsts.items(), key=lambda kv: -sum(
                    kv[1].values())))  # fmt: skip
            w = out[src][m]["with_revelations"]
            print(f"{src} {m:18} first (2,000 / 5,000-word chunks): " + "; ".join(
                f"{u.removeprefix('cand__')[:28]} {v['2000']}/{v['5000']}"
                for u, v in list(w.items())[:3]))  # fmt: skip
    p = Path("data/blind/a55_by_length.json")
    p.write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"-> {p}")
    return 0


def _a54_scores(bom: set[str], d: Path) -> dict:
    """Amendment 54's per-chunk scores with the later revelations among the units."""
    from eval.js_later import UNIT
    from eval.js_register import A43, POOL
    from eval.js_register import OUT as A44

    out: dict = {}
    c = json.loads((d / "classic.json").read_text())["ids"]
    for m, lower in (("cosine_delta", True), ("burrows_delta", True), ("general_imposters", False)):
        out[m] = ({i: c[i][m] for i in bom}, lower)
    for size in ("base", "mid"):
        st = json.loads((d / f"style_{size}.json").read_text())["ids"]
        out[f"style_{size}"] = ({i: st[i]["cosine"] for i in bom}, True)
    for size in SIZES:
        mine = json.loads((d / f"alm_{size}.json").read_text())["models"]["whole"]["scores"]
        prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        pooled = json.loads((A44 / f"alm_{size}.json").read_text())["scores"]
        out[f"alm_{size}"] = ({i: {**prior[i]["scores"], POOL: pooled[i], UNIT: mine[i]}
                               for i in bom}, True)  # fmt: skip
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["head-to-head", "curve", "by-length"])
    ap.add_argument("--ext", action="store_true", help="Amendment 56: all 55 authors")
    a = ap.parse_args(argv)
    if a.cmd == "head-to-head":
        return head_to_head(a.ext)
    return {"curve": curve, "by-length": by_length}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
