"""How long a candidate list can each method pick the author from? (Amendment 58, BOM-90).

The 55 benchmark authors with held-out tests (BOM-75's 23, Amendment 56's 32), their registered
training words and their 910 registered held-out tests. For list sizes ``list_size.sizes``:

- **random** lists: per author and size, ``draws_per_author`` seeded draws of the other N-1
  authors; the author's tests are attributed among that list;
- **similar** lists: the author plus its N-1 nearest authors by Cosine Delta between training
  profiles (``similar_mfw`` words, z over all 55 authors' training blocks), one per author and size.

The older methods (Burrows' and Cosine Delta, ENSC, General Imposters) are refitted on every list as
``eval.benchmark.run_task`` does; General Imposters keeps each test's registered imposter pool with
every benchmark candidate removed. Our models' scores do not depend on the rest of the list, so
``report`` reads every list from one table per size (``data/benchmark/alm_<size>_pool.json``,
written by ``alm.benchmark <size> --pool``) when it exists.

Counting by author (Amendment 55): each author's accuracy over its tests and draws; the mean over
authors with an author-resampled interval; the longest list at or above each bar; at the decision
size (12, similar lists) every model size against every older method by exact sign test over
authors, Holm over the 12. Names and numbers only.

Usage::

    python -m eval.list_size prepare          # Mac: author blocks, tests, pools -> work dir
    python -m eval.list_size classic [--workers 8]   # Mac, resumes per author (a few hours)
    python -m eval.list_size report           # -> data/benchmark/list_size.json
    python -m eval.list_size tournament       # BOM-93 -> data/benchmark/list_size_tournament.json
    python -m eval.list_size normalised       # BOM-90 -> data/benchmark/list_size_normalised.json
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import pickle
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

WORK = Path("data/corpus/list_size")  # corpus-derived (test words), never in git
DATA = WORK / "pool.pkl"
METHODS = ("burrows_delta", "cosine_delta", "ensc", "general_imposters")
SIZES_ALM = ("pilot", "base", "mid")


def merged_plan(cfg: dict) -> dict[str, dict]:
    """BOM-75's seven tasks and Amendment 56's eight, as ``alm.benchmark.plan`` builds them."""
    from alm.benchmark import plan

    a, b = plan(cfg, True), plan(cfg, False, True)
    assert not set(a) & set(b)
    return {**a, **b}


def tested_authors(p: dict[str, dict]) -> dict[str, str]:
    """author -> task, for every author that has held-out tests (each in exactly one task)."""
    out: dict[str, str] = {}
    for task, tp in p.items():
        for a in sorted({x["author"] for x in tp["tests"]}):
            assert a not in out, f"{a} tested in two tasks"
            assert a in tp["train"], f"{a} has tests but no training words in {task}"
            out[a] = task
    return out


def prepare() -> int:
    from alm.benchmark import plan  # noqa: F401  (corpus needed)
    from classic.features import tokenize
    from eval.benchmark import TASKS, imposter_pool
    from eval.power import blocks

    cfg = load_config()
    p = merged_plan(cfg)
    who = tested_authors(p)
    every = tuple(sorted({b for tp in p.values() for b in tp["train"]}))
    spec = json.loads(TASKS.read_text())
    pools = {}
    for task in sorted({who[a] for a in who}):
        if task.startswith(("p2_", "p3_")):
            g = task.removeprefix("p2_") if task.startswith("p2_") else task[3:].rsplit("_", 1)[0]
            pool_set, pool_genre = cfg["part2_benchmark"]["pools"][g]
            pools[task] = imposter_pool(pool_set, set(), cfg, pool_genre, every)
        else:
            sp = spec[task]
            pools[task] = imposter_pool(sp["imposter_pool"], set(sp.get("exclude_from_pool", [])),
                                        cfg, sp.get("imposter_genre"),
                                        tuple(sp.get("exclude_authors_from_pool", [])) + every,
                                        sp.get("imposter_fill"))  # fmt: skip
        print(f"  pool {task}: {len(pools[task])} samples", flush=True)
    authors = {}
    for a, task in sorted(who.items()):
        works = p[task]["train"][a]
        bl = blocks(tokenize(" ".join(w for ws in works for w in ws)))
        tests = [(x["where"], Counter(tokenize(" ".join(x["words"]))))
                 for x in p[task]["tests"] if x["author"] == a]  # fmt: skip
        authors[a] = {"task": task, "blocks": [Counter(b) for b in bl], "tests": tests}
    WORK.mkdir(parents=True, exist_ok=True)
    pool_counts = {t: [Counter(s) for s in v] for t, v in pools.items()}
    with DATA.open("wb") as fh:
        pickle.dump({"authors": authors, "pools": pool_counts}, fh)
    n = sum(len(v["tests"]) for v in authors.values())
    print(f"{len(authors)} authors, {n} tests -> {DATA}")
    return 0


def _load() -> dict:
    with DATA.open("rb") as fh:
        return pickle.load(fh)


def similar_order(authors: dict, cfg: dict) -> dict[str, list[str]]:
    """Per author, the other authors nearest first by Cosine Delta between training profiles."""
    from classic import build_vocabulary, frequency_matrix
    from metadata.config import classic_kwargs

    kw = classic_kwargs(cfg)
    names = sorted(authors)
    docs = [c for a in names for c in authors[a]["blocks"]]
    lab = np.array([a for a in names for _ in authors[a]["blocks"]])
    vocab = build_vocabulary(docs, top_n=cfg["list_size"]["similar_mfw"],
                             min_doc_fraction=kw["mfw_min_doc_fraction"])  # fmt: skip
    X = frequency_matrix(docs, vocab)
    sd = X.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    Z = (X - X.mean(axis=0)) / sd
    P = np.stack([Z[lab == a].mean(axis=0) for a in names])
    P /= np.linalg.norm(P, axis=1, keepdims=True)
    D = 1.0 - P @ P.T
    return {a: [names[j] for j in np.argsort(D[i], kind="stable") if j != i]
            for i, a in enumerate(names)}  # fmt: skip


def lists(authors: dict, cfg: dict) -> dict[str, dict[str, dict[int, list[list[str]]]]]:
    """author -> type -> size -> lists (each sorted, the author included)."""
    ls = cfg["list_size"]
    near = similar_order(authors, cfg)
    names = sorted(authors)
    out: dict = {}
    for a in names:
        others = [b for b in names if b != a]
        rnd, sim = {}, {}
        for n in ls["sizes"]:
            k = min(n, len(names)) - 1
            if k >= len(others):
                rnd[n] = [sorted(names)]
            else:
                rng = random.Random(derive_seed(f"{ls['draw_seed']}:{a}:{n}", cfg))
                rnd[n] = [
                    sorted([a, *rng.sample(others, k)]) for _ in range(ls["draws_per_author"])
                ]
            sim[n] = [sorted([a, *near[a][:k]])]
        out[a] = {"random": rnd, "similar": sim}
    return out


@functools.cache
def _ensc_settings() -> dict:
    return json.loads(Path("data/benchmark/part2/benchmark.json").read_text())["ensc"]


def _one_list(a: str, names: list[str], data: dict, cfg: dict, seed: int) -> dict[str, int]:
    """Correct attributions of ``a``'s tests among ``names``, per older method."""
    from classic import build_vocabulary, frequency_matrix, general_imposters, nearest_authors
    from eval.benchmark import _ensc_predict
    from metadata.config import classic_kwargs

    kw = classic_kwargs(cfg)
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    au = data["authors"]
    docs = [c for b in names for c in au[b]["blocks"]]
    labels = [b for b in names for _ in au[b]["blocks"]]
    vocab = build_vocabulary(docs, top_n=top_n, min_doc_fraction=kw["mfw_min_doc_fraction"])
    X = frequency_matrix(docs, vocab)
    lab = np.array(labels)
    prof = {b: X[lab == b].mean(axis=0) for b in names}
    P = frequency_matrix(data["pools"][au[a]["task"]], vocab)
    gi_args = {
        **kw["imposters"],
        "n_imposters": min(len(P), cfg["classic"]["imposters"]["per_trial"]),
    }
    ens = _ensc_settings()
    rng = random.Random(seed)
    got = dict.fromkeys(METHODS, 0)
    for _, cnt in au[a]["tests"]:
        x = frequency_matrix([cnt], vocab)[0]
        got["burrows_delta"] += nearest_authors(x, prof, method="burrows", reference=X)[0][0] == a
        got["cosine_delta"] += nearest_authors(x, prof, method="cosine", reference=X)[0][0] == a
        got["ensc"] += _ensc_predict({"_ensc": (X, labels, x)}, ens["shrinkage"], ens["alpha"],
                                     kw["ensc"]["priors"], None) == a  # fmt: skip
        gs = {b: general_imposters(x, prof[b], P, seed=rng.randrange(2**31), **gi_args)
              for b in names}  # fmt: skip
        got["general_imposters"] += max(names, key=lambda b: (gs[b], b)) == a
    return got


def _author_job(a: str) -> str:
    out = WORK / "classic" / f"{a.replace('/', '_')}.json"
    if out.exists():
        return f"{a}: already done"
    cfg = load_config()
    data = _load()
    ls = lists(data["authors"], cfg)[a]
    res: dict = {"author": a, "tests": len(data["authors"][a]["tests"])}
    for typ, by in ls.items():
        res[typ] = {}
        for n, lst in by.items():
            gs = cfg["list_size"]["gi_seed"]
            res[typ][str(n)] = [
                _one_list(a, names, data, cfg, derive_seed(f"{gs}:{a}:{typ}:{n}:{d}", cfg))
                for d, names in enumerate(lst)
            ]
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(res))
    tmp.replace(out)
    return f"{a}: done"


def classic(workers: int) -> int:
    import multiprocessing as mp

    (WORK / "classic").mkdir(parents=True, exist_ok=True)
    names = sorted(_load()["authors"])
    todo = [a for a in names if not (WORK / "classic" / f"{a.replace('/', '_')}.json").exists()]
    print(f"{len(names) - len(todo)} of {len(names)} authors done; {len(todo)} to run", flush=True)
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    with mp.get_context("spawn").Pool(workers) as pool:
        for k, msg in enumerate(pool.imap_unordered(_author_job, todo), 1):
            print(f"  [{k}/{len(todo)}] {msg}", flush=True)
    return 0


def pool_records(path: Path) -> list[dict]:
    """A pool score file's records with ``scores`` as {candidate: score}. Files are kept compact
    (one candidate list, scores as rows rounded to 7 places); a file as the pod wrote it (a dict
    per test) is rewritten compact on first read."""
    d = json.loads(path.read_text())
    if "candidates" not in d:
        cands = sorted(d["records"][0]["scores"])
        d["candidates"] = cands
        for r in d["records"]:
            r["scores"] = [round(r["scores"][b], 7) for b in cands]
        head = {k: v for k, v in d.items() if k != "records"}
        rows = ",\n".join(json.dumps(r, separators=(",", ":")) for r in d["records"])
        path.write_text(json.dumps(head, indent=1)[:-2] + ',\n "records": [\n' + rows + "\n]}\n")
    return [{**r, "scores": dict(zip(d["candidates"], r["scores"], strict=True))}
            for r in d["records"]]  # fmt: skip


def _alm_tables(data: dict) -> dict[str, dict[str, list[dict[str, float]]]]:
    """size -> author -> per test {candidate: score} (lower is closer), where scored."""
    out = {}
    for z in SIZES_ALM:
        f = Path(f"data/benchmark/alm_{z}_pool.json")
        if not f.exists():
            continue
        by: dict[str, list] = {}
        for r in pool_records(f):
            by.setdefault(r["author"], []).append((r["where"], r["scores"]))
        for a, v in data["authors"].items():  # same tests in the same order
            assert [w for w, _ in by[a]] == [w for w, _ in v["tests"]], a
        by = {a: [s for _, s in v] for a, v in by.items()}
        out[f"alm_{z}"] = by
    return out


def reproduction() -> dict[str, dict]:
    """Per size: the new pool scores against the saved Amendment 22/56 records on each author's
    own-task tests (largest absolute difference, and agreement of the predicted author)."""
    out = {}
    for z in SIZES_ALM:
        f = Path(f"data/benchmark/alm_{z}_pool.json")
        if not f.exists():
            continue
        old = {}
        for s in ("p2", "p3"):
            for task, rs in json.loads(Path(f"data/benchmark/alm_{z}_{s}.json").read_text())[
                "records"
            ].items():
                for r in rs:
                    old[task, r["author"], r["where"]] = r["scores"]
        diffs, same, n = [], 0, 0
        for r in pool_records(f):
            o = old[r["task"], r["author"], r["where"]]
            shared = [b for b in o if b in r["scores"]]
            diffs += [abs(r["scores"][b] - o[b]) for b in shared]
            same += min(shared, key=lambda b: (o[b], b)) == min(
                shared, key=lambda b: (r["scores"][b], b)
            )
            n += 1
        out[f"alm_{z}"] = {"tests": n, "max_abs_diff": max(diffs),
                           "median_abs_diff": float(np.median(diffs)),
                           "same_pick_share": same / n}  # fmt: skip
    return out


def _alm_ranks(scores: list[dict[str, float]], a: str, names: list[str]) -> list[int]:
    """The true author's rank among ``names`` for each test (1 = closest; ties by name)."""
    return [sorted(names, key=lambda b: (s[b], b)).index(a) + 1 for s in scores]


def top_k(alm: dict, lst: dict, names: list[str], ls: dict) -> dict:
    """Our models: mean over authors of the share of attributions with the true author among the
    closest k, per list type and size (k below the list size)."""
    out: dict = {}
    for m, tab in alm.items():
        for typ in ("random", "similar"):
            rows = []
            for n in ls["sizes"]:
                per = {a: [r for x in lst[a][typ][n] for r in _alm_ranks(tab[a], a, x)]
                       for a in names}  # fmt: skip
                rows.append({"size": n, **{
                    f"top{k}": float(np.mean([np.mean(np.array(v) <= k) for v in per.values()]))
                    for k in ls["top_k"] if k < n}})  # fmt: skip
            out.setdefault(m, {})[typ] = rows
    return out


def _alm_correct(scores: list[dict[str, float]], a: str, names: list[str]) -> int:
    return sum(min(names, key=lambda b: (s[b], b)) == a for s in scores)


def report() -> int:
    from eval.clustered import holm, sign_p

    cfg = load_config()
    ls = cfg["list_size"]
    data = _load()
    names = sorted(data["authors"])
    lst = lists(data["authors"], cfg)
    alm = _alm_tables(data)
    acc: dict = {}  # method -> type -> size -> author -> (correct, attributions)
    for a in names:
        f = WORK / "classic" / f"{a.replace('/', '_')}.json"
        cl = json.loads(f.read_text()) if f.exists() else None
        nt = len(data["authors"][a]["tests"])
        for typ in ("random", "similar"):
            for n in ls["sizes"]:
                if cl is not None:
                    for m in METHODS:
                        c = sum(d[m] for d in cl[typ][str(n)])
                        acc.setdefault(m, {}).setdefault(typ, {}).setdefault(n, {})[a] = (
                            c,
                            nt * len(cl[typ][str(n)]),
                        )
                for m, tab in alm.items():
                    c = sum(_alm_correct(tab[a], a, x) for x in lst[a][typ][n])
                    acc.setdefault(m, {}).setdefault(typ, {}).setdefault(n, {})[a] = (
                        c,
                        nt * len(lst[a][typ][n]),
                    )
    rng = random.Random(derive_seed(ls["resample_seed"], cfg))
    idx = [[rng.randrange(len(names)) for _ in names] for _ in range(ls["resamples"])]
    curves: dict = {}
    for m, by_t in acc.items():
        for typ, by_n in by_t.items():
            rows = []
            for n in ls["sizes"]:
                per = by_n.get(n, {})
                if len(per) < len(names):
                    continue
                v = np.array([per[a][0] / per[a][1] for a in names])
                boots = np.sort(v[np.array(idx)].mean(axis=1))
                rows.append({"size": n, "mean_by_author": float(v.mean()),
                             "interval": [float(boots[int(0.025 * len(boots))]),
                                          float(boots[int(0.975 * len(boots)) - 1])],
                             "share_of_attributions": sum(per[a][0] for a in names)
                             / sum(per[a][1] for a in names)})  # fmt: skip
            if not rows:
                continue
            longest = {}
            for bar in ls["bars"]:
                ok = [r["size"] for r in rows if r["mean_by_author"] >= bar]
                lo = [r["size"] for r in rows if r["interval"][0] >= bar]
                longest[str(bar)] = {"mean_at_or_above": max(ok) if ok else None,
                                     "lower_end_at_or_above": max(lo) if lo else None}  # fmt: skip
            curves.setdefault(m, {})[typ] = {"curve": rows, "longest_list": longest}
    decision = []
    n = ls["decision_size"]
    for z in alm:
        for m in METHODS:
            if m not in acc or len(acc[m]["similar"][n]) < len(names):
                continue  # the older methods' run is not complete yet
            ours, theirs = acc[z]["similar"][n], acc[m]["similar"][n]
            d = [ours[a][0] / ours[a][1] - theirs[a][0] / theirs[a][1] for a in names]
            w, lose = sum(x > 0 for x in d), sum(x < 0 for x in d)
            decision.append({"ours": z, "theirs": m, "ours_ahead": w, "theirs_ahead": lose,
                             "tied": len(d) - w - lose, "sign_p": sign_p(w, lose)})  # fmt: skip
    for r, p in zip(decision, holm([r["sign_p"] for r in decision]), strict=True):
        r["holm_p"] = p
        r["ours_better"] = p < ls["alpha"] and r["ours_ahead"] > r["theirs_ahead"]
    out = Path(ls["out"])
    out.write_text(json.dumps({**stamp(), "authors": len(names),
                               "tests": sum(len(v["tests"]) for v in data["authors"].values()),
                               "methods_scored": sorted(curves), "curves": curves,
                               "decision_size": n, "decision": decision,
                               "top_k": top_k(alm, lst, names, ls),
                               "reproduction": reproduction()},
                              indent=1) + "\n")  # fmt: skip
    for m, by_t in curves.items():
        for typ, v in by_t.items():
            pts = " ".join(f"{r['size']}:{r['mean_by_author']:.2f}" for r in v["curve"])
            print(f"{m:<18} {typ:<8} {pts}")
    print(f"-> {out}")
    return 0


def _span(where: str) -> tuple[str, int, int]:
    m = re.match(r"(?:(.*) )?blocks (\d+)-(\d+)", where)
    return m.group(1) or "", int(m.group(2)), int(m.group(3))


def _disjoint(wheres: list[str]) -> list[int]:
    """Indices of a largest set of tests that share no block (greedy by end)."""
    keep, last = [], {}
    for i in sorted(range(len(wheres)), key=lambda i: (_span(wheres[i])[0], _span(wheres[i])[2])):
        w, s, e = _span(wheres[i])
        if s > last.get(w, -1):
            keep.append(i)
            last[w] = e
    return keep


def tournament() -> int:
    """BOM-93 part 1 (exploratory): on the full 55-author list, per model size and by author:
    straight ranking on one passage; heats then a final on the **same** passage; heats then a
    final on a **different**, non-overlapping passage; and straight ranking on several
    non-overlapping passages averaged (the same extra evidence spent on everyone)."""
    cfg = load_config()
    tc = cfg["list_size"]["tournament"]
    data = _load()
    names = sorted(data["authors"])
    alm = _alm_tables(data)
    out: dict = {}
    for m, tab in alm.items():
        rng = random.Random(derive_seed(f"{tc['seed']}:{m}", cfg))
        S = {a: np.array([[s[b] for b in names] for s in tab[a]]) for a in names}
        dis = {a: _disjoint([w for w, _ in data["authors"][a]["tests"]]) for a in names}
        res: dict = {"straight": [], "pooled": {str(k): [] for k in tc["pooled"]}}
        for h in tc["heats"]:
            res[f"heats_{h[0]}x{h[1]}_keep{h[2]}"] = {"in_final": [], "same": [], "fresh": []}
        for a in names:
            t = names.index(a)
            idx = dis[a]
            res["straight"].append(float(np.mean(S[a].argmin(axis=1) == t)))
            for k in tc["pooled"]:
                if len(idx) >= k:
                    sets = [rng.sample(idx, k) for _ in range(tc["draws"])]
                    hit = [S[a][x].mean(axis=0).argmin() == t for x in sets]
                    res["pooled"][str(k)].append(float(np.mean(hit)))
            if len(idx) < 2:
                continue
            for nh, hs, kp in tc["heats"]:
                fin, same, fresh = [], [], []
                for _ in range(tc["draws"]):
                    i, j = rng.sample(idx, 2)
                    order = list(range(len(names)))
                    rng.shuffle(order)
                    surv = []
                    for g in range(nh):
                        grp = order[g * hs : (g + 1) * hs]
                        surv += sorted(grp, key=lambda b: S[a][i][b])[:kp]
                    fin.append(t in surv)
                    same.append(min(surv, key=lambda b: S[a][i][b]) == t)
                    fresh.append(min(surv, key=lambda b: S[a][j][b]) == t)
                r = res[f"heats_{nh}x{hs}_keep{kp}"]
                r["in_final"].append(float(np.mean(fin)))
                r["same"].append(float(np.mean(same)))
                r["fresh"].append(float(np.mean(fresh)))

        def mean(v: list[float]) -> dict:
            return {"authors": len(v), "mean_by_author": float(np.mean(v))}

        out[m] = {"straight_one_passage": mean(res["straight"]),
                  "pooled_passages": {k: mean(v) for k, v in res["pooled"].items() if v},
                  **{k: {q: mean(v) for q, v in r.items()}
                     for k, r in res.items() if k.startswith("heats")}}  # fmt: skip
        print(m, json.dumps(out[m], indent=1))
    path = Path("data/benchmark/list_size_tournament.json")
    path.write_text(json.dumps({**stamp(), "list": len(names), "exploratory": True,
                                "results": out}, indent=1) + "\n")  # fmt: skip
    print(f"-> {path}")
    return 0


def scale_scores(X: np.ndarray, cohort: np.ndarray) -> np.ndarray:
    """Each model's column put on its own scale: minus its mean, over its spread, on the cohort
    rows (passages by other authors). NaN cohort entries (the model's own passages) are skipped."""
    return (X - np.nanmean(cohort, axis=0)) / np.nanstd(cohort, axis=0)


def normalised() -> int:
    """BOM-90 follow-up (exploratory, post hoc): do a few models win everywhere, and does putting
    each model's score on its own scale fix it? Strict version: the scale comes from one group of
    authors' passages (BOM-75's 23 or Amendment 56's 32), the test from the other group, both
    directions, on the full 55-author list; raw and scaled read on the same draws."""
    from eval.clustered import sign_p

    cfg = load_config()
    nc = cfg["list_size"]["normalised"]
    data = _load()
    names = sorted(data["authors"])
    late = {a for a in names if data["authors"][a]["task"].startswith(nc["later_prefix"])}
    groups = {"first_23": [a for a in names if a not in late], "later_32": sorted(late)}
    out: dict = {}
    for m, tab in _alm_tables(data).items():
        rng = random.Random(derive_seed(f"{nc['seed']}:{m}", cfg))
        S = {a: np.array([[s[b] for b in names] for s in tab[a]]) for a in names}
        res: dict = {}
        per: dict[str, dict[str, list[float]]] = {}
        for test_g, cohort_g in (("later_32", "first_23"), ("first_23", "later_32")):
            rows = []
            for c in groups[cohort_g]:  # a model never sets its scale on its own passages
                x = S[c].copy()
                x[:, names.index(c)] = np.nan
                rows.append(x)
            cohort = np.vstack(rows)
            r: dict = {"raw": {}, "scaled": {}}
            for a in groups[test_g]:
                t = names.index(a)
                idx = _disjoint([w for w, _ in data["authors"][a]["tests"]])
                sets = {k: [rng.sample(idx, k) for _ in range(nc["draws"])]
                        for k in nc["pooled"] if len(idx) >= k}  # fmt: skip
                for kind, X in (("raw", S[a]), ("scaled", scale_scores(S[a], cohort))):
                    v = {"one": float(np.mean(X.argmin(axis=1) == t)),
                         "all": float(X[idx].mean(axis=0).argmin() == t)}  # fmt: skip
                    for k, ss in sets.items():
                        v[f"pooled_{k}"] = float(np.mean([X[x].mean(axis=0).argmin() == t
                                                          for x in ss]))  # fmt: skip
                    for q, val in v.items():
                        r[kind].setdefault(q, []).append(val)
                        per.setdefault(f"{kind}:{q}", {})[a] = val
            res[f"test_{test_g}_scale_from_{cohort_g}"] = {
                kind: {q: {"authors": len(v), "mean_by_author": float(np.mean(v))}
                       for q, v in qs.items()} for kind, qs in r.items()}  # fmt: skip
        both: dict = {}
        for q in sorted({k.split(":")[1] for k in per}):
            raw, sc = per[f"raw:{q}"], per[f"scaled:{q}"]
            w = sum(sc[a] > raw[a] for a in raw)
            lose = sum(sc[a] < raw[a] for a in raw)
            both[q] = {"authors": len(raw), "raw": float(np.mean(list(raw.values()))),
                       "scaled": float(np.mean(list(sc.values()))), "scaled_ahead": w,
                       "raw_ahead": lose, "tied": len(raw) - w - lose,
                       "sign_p": sign_p(w, lose)}  # fmt: skip
        res["both_directions"] = both
        out[m] = res
        print(m, json.dumps(both, indent=1))
    path = Path(nc["out"])
    path.write_text(json.dumps({**stamp(), "list": len(names), "exploratory": True,
                                "post_hoc": True, "results": out}, indent=1) + "\n")  # fmt: skip
    print(f"-> {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m eval.list_size")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    c = sub.add_parser("classic")
    c.add_argument("--workers", type=int, default=8)
    sub.add_parser("report")
    sub.add_parser("tournament")
    sub.add_parser("normalised")
    args = ap.parse_args(argv)
    if args.cmd == "prepare":
        return prepare()
    if args.cmd == "tournament":
        return tournament()
    if args.cmd == "normalised":
        return normalised()
    if args.cmd == "classic":
        return classic(args.workers)
    return report()


if __name__ == "__main__":
    sys.exit(main())
