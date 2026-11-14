"""Shortlist coverage from per-episode style vectors (BOM-89 step 2; exploratory).

``python -m sweep.index episodes`` writes, for every unit, one vector per 8-passage episode and
the whole-unit vector. For each of the 200 known books three kinds of score are ranked over the
gallery (the true author represented by the profile rebuilt without the book):

- ``whole``: cosine distance between whole-unit vectors, averaged over the book's chunks (what
  ``sweep.calibrate`` does; with the BOM-30 encoder it reproduces its ranks).
- ``top<k>``: for each of the book's episodes, the mean similarity to an author's ``k`` closest
  episodes; averaged over the book's episodes. ``k`` from ``sweep.episodes.top``.

Two galleries: every swept author, and ``possible`` (authors not known to be dead or under age in
``sweep.people.year``, from ``data/sweep/people.parquet``; the true author always stays). Groups
(identity, genre) are those of ``python -m sweep.coverage``.

``--profile-episodes N`` cuts every profile to its middle N consecutive episodes (about 1,024
tokens each), an equal profile size for every author; the whole-unit score is not meaningful
then (it still uses the full profile) and is to be ignored.

Writes names and numbers only: ``data/sweep/coverage_episodes<tag>[_N].json``.

Usage::

    python -m sweep.episodes [--tag _v2] [--profile-episodes 3]
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp
from sweep.coverage import coverage
from sweep.index import WORK
from sweep.units import OUT


def load(tag: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """unit -> its episode vectors, unit -> its whole-unit vector."""
    eps, whole = {}, {}
    for f in sorted((WORK / f"episodes{tag}").glob("part_*.npz")):
        z = np.load(f)
        cuts = np.cumsum(z["counts"])[:-1]
        for u, v, w in zip(z["units"].tolist(), np.split(z["V"], cuts), z["W"], strict=True):
            eps[u], whole[u] = v.astype(np.float32), w.astype(np.float32)
    return eps, whole


def padded(vecs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """(authors, most episodes, dim) with zeros, and the mask of real episodes."""
    most = max(len(v) for v in vecs)
    G = np.zeros((len(vecs), most, vecs[0].shape[1]), dtype=np.float32)
    M = np.zeros((len(vecs), most), dtype=bool)
    for i, v in enumerate(vecs):
        G[i, : len(v)], M[i, : len(v)] = v, True
    return G, M


def topk_scores(
    Q: np.ndarray, G: np.ndarray, M: np.ndarray, ks: list[int]
) -> dict[int, np.ndarray]:
    """Per author, the mean over query episodes of the mean of their ``k`` most similar episodes
    (an author with fewer than ``k`` episodes is scored on those they have)."""
    out = {k: np.zeros(len(G)) for k in ks}
    most = max(ks)
    for q in Q:
        sim = np.where(M, G @ q, -np.inf)
        best = -np.sort(-sim, axis=1)[:, :most]
        for k in ks:
            b = best[:, :k]
            ok = np.isfinite(b)
            out[k] += np.where(ok, b, 0).sum(axis=1) / np.maximum(ok.sum(axis=1), 1)
    return {k: v / len(Q) for k, v in out.items()}


def rank(score: np.ndarray, t: int, keep: np.ndarray) -> int:
    """The true author's rank by descending score among the kept authors."""
    k = keep.copy()
    k[t] = False
    return int((score[k] > score[t]).sum()) + 1


def cut(v: np.ndarray, n: int | None) -> np.ndarray:
    """The middle ``n`` consecutive episodes of a profile (all of it when shorter or n is None)."""
    if n is None or len(v) <= n:
        return v
    start = (len(v) - n) // 2
    return v[start : start + n]


def run(tag: str, n: int | None = None) -> int:
    cfg = load_config()
    c, e = cfg["sweep"]["coverage"], cfg["sweep"]["episodes"]
    eps, whole = load(tag)
    swept = sorted(u[len("profile:") :] for u in eps if u.startswith("profile:"))
    pos = {a: i for i, a in enumerate(swept)}
    G, M = padded([cut(eps[f"profile:{a}"], n) for a in swept])
    W = np.stack([whole[f"profile:{a}"] for a in swept])
    people = OUT / "people.parquet"
    possible = np.ones(len(swept), dtype=bool)
    if people.exists():
        st = dict(zip(*pq.read_table(people, columns=["author", "status"]).to_pydict().values(),
                      strict=True))  # fmt: skip
        possible = np.array([st.get(a) not in ("dead", "too_young") for a in swept])
    base = {r["author"]: r for r in json.loads((OUT / "coverage.json").read_text())["records"]}
    every = np.ones(len(swept), dtype=bool)
    recs = []
    for k, (a, b) in enumerate(sorted(base.items()), 1):
        if a not in pos or f"calib_profile:{a}" not in eps:
            continue
        t = pos[a]
        qs = sorted(u for u in eps if u.startswith(f"calib_query:{a}:"))
        own, own_m, own_w = G[t].copy(), M[t].copy(), W[t].copy()
        cp = cut(eps[f"calib_profile:{a}"], n)[: G.shape[1]]
        G[t], M[t] = 0, False
        G[t, : len(cp)], M[t, : len(cp)] = cp, True
        W[t] = whole[f"calib_profile:{a}"]
        scores = {"whole": (W @ np.stack([whole[u] for u in qs]).T).mean(axis=1)}
        tk = topk_scores(np.concatenate([eps[u] for u in qs]), G, M, e["top"])
        scores.update({f"top{k_}": v for k_, v in tk.items()})
        rec = {x: b[x] for x in ("author", "book", "identity", "genre", "profile_works")}
        rec["old_style"] = b["style"]
        for name, s in scores.items():
            rec[name] = rank(s, t, every)
            rec[f"{name}_possible"] = rank(s, t, possible)
        recs.append(rec)
        G[t], M[t], W[t] = own, own_m, own_w
        if k % 20 == 0:
            print(f"  {k}/{len(base)}", flush=True)
    methods = [m for m in recs[0] if m not in ("author", "book", "identity", "genre",
                                               "profile_works")]  # fmt: skip
    conf = [r for r in recs if r["identity"] in c["confirmed"]]
    groups = {"all": recs, "confirmed": conf,
              **{f"genre_{g}": [r for r in recs if r["genre"] == g]
                 for g in ("same", "mixed", "cross")},
              "confirmed_genre_cross": [r for r in conf if r["genre"] == "cross"]}  # fmt: skip
    doc = {**stamp(), "exploratory": True, "encoder": tag or "bom30", "ks": c["ks"],
           "gallery": {"all": int(every.sum()), "possible": int(possible.sum())},
           "groups": {g: {"n": len(rs), **{m: coverage([r[m] for r in rs], c["ks"])
                                           for m in methods}} for g, rs in groups.items()},
           "records": recs}  # fmt: skip
    doc["profile_episodes"] = n
    out = OUT / f"coverage_episodes{tag}{f'_{n}' if n else ''}.json"
    out.write_text(json.dumps(doc, indent=1) + "\n")
    show = [k for k in c["ks"] if k in c["show"]]
    print(f"gallery {doc['gallery']}; true author within K = {show} (%)")
    for g, t_ in doc["groups"].items():
        print(f"{g} (n={t_['n']})")
        for m in methods:
            print(f"   {m:16s}" + "".join(f"{100 * t_[m][str(k)]:7.1f}" for k in show))
    print(f"-> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--tag", default="", help="the encoder's suffix: _gpu (BOM-30's), _v2")
    ap.add_argument(
        "--profile-episodes",
        type=int,
        help="equal profile size: each author's middle N episodes only",
    )
    a = ap.parse_args(argv)
    return run(a.tag, a.profile_episodes)


if __name__ == "__main__":
    sys.exit(main())
