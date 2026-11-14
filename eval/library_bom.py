"""The Book of Mormon against the whole library and the Phase 1 candidates (BOM-95; exploratory).

Fixed path step 4 (tracker BOM-92), as changed on 2026-11-14 after BOM-94 showed the style encoder
ranks library authors better than equal-dose author models. **This module and its
``library_search`` config block were committed before any Book of Mormon vector under the second
encoder was made**; the commit is the record of what was fixed first.

- **Query**: the sealed Book of Mormon chunks (``data/corpus/blind/sealed.jsonl``, the ``bom``
  ids of the unblinded key: 121 of 2,000 words and 47 of 5,000, KJV-masked as in Phase 1), each
  embedded per episode by the second style encoder (``style_embed.v2``).
- **Gallery**: every swept author's profile episodes (``sweep.index episodes --tag _v2``), tagged
  alive / unknown / dead / too young in 1829 (``sweep.people``); and the Phase 1 candidate units
  with Joseph Smith's pooled later prose and his 1830-34 revelations (``eval.js_later._refs``: KJV
  masked, Book of Mormon quotations dropped), embedded the same way. Nobody is removed: the dead
  are the decoys.
- **Score**: as validated on the 200 known books (``sweep.episodes``): for each query episode the
  similarity to an author's closest episode, averaged over the query episodes.
- **Three rankings by profile size**: ``small`` = as many episodes as the 1828-29 revelation
  sample has, every profile cut to its middle that-many episodes; ``large`` =
  ``library_search.large_episodes``; ``full`` = everything each author has. A candidate with more
  text than the size is also scored on every other non-overlapping slice (its best, median and
  worst rank reported). The known-book coverage at the same profile size
  (``data/sweep/coverage_episodes_v2[_N].json``) is the X that goes with each ranking.

Reported per ranking: the top ``top`` with status and dates; every candidate's rank among all
and among the possible (not dead, not under age); how many dead authors are in the top 20, 100
and 1,000 against their share of the gallery; the same ranking from the 2,000-word and the
5,000-word chunks alone (the book cut twice) and their overlap.

Vectors of the candidates and the book stay in ``data/corpus/library_bom/``; the ranking holds
names and numbers only: ``data/sweep/bom_ranking.json``.

Usage::

    python -m eval.library_bom embed     # Mac GPU, minutes
    python -m eval.library_bom rank
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from metadata.config import load as load_config
from metadata.config import stamp

WORK = Path("data/corpus/library_bom")
VECS = WORK / "vectors.npz"
OUT = Path("data/sweep/bom_ranking.json")
SEALED = Path("data/corpus/blind/sealed.jsonl")
KEY = Path("~/.bom-blind/key.json").expanduser()  # Phase 1 is unblinded; read for the bom ids
REVELATION = "cand__joseph-smith__dictated__pre1830"


def embed() -> int:
    import torch
    from tokenizers import Tokenizer

    from classic.features import tokenize
    from eval.js_later import _refs
    from style_embed.train import load_encoder
    from sweep.index import episode_vectors
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    s, ls = cfg["style_embed"], cfg["library_search"]
    dev = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    enc = load_encoder(Path(ls["encoder"]), cfg).to(dev)
    tok = Tokenizer.from_file(str(TOKENIZER))

    def vec(words: list[str]) -> np.ndarray:
        ids = tok.encode(" ".join(words)).ids
        return episode_vectors(enc, ids, s["passage_tokens"], s["episode_passages"], dev)[0]

    key = json.loads(KEY.read_text())
    rows = [json.loads(ln) for ln in SEALED.read_text().splitlines()]
    rows = sorted((r for r in rows if key[r["id"]]["kind"] == "bom"), key=lambda r: r["id"])
    q = [vec(tokenize(r["text"])) for r in rows]
    refs = {u: r["tokens"] for u, r in sorted(_refs().items()) if r["tokens"]}
    c = {u: vec(t) for u, t in refs.items()}
    WORK.mkdir(parents=True, exist_ok=True)
    np.savez(VECS, q=np.concatenate(q), q_counts=np.array([len(v) for v in q]),
             q_ids=np.array([r["id"] for r in rows]), q_words=np.array([r["words"] for r in rows]),
             c=np.concatenate(list(c.values())), c_counts=np.array([len(v) for v in c.values()]),
             c_units=np.array(list(c)))  # fmt: skip
    sizes = {u: len(v) for u, v in c.items()}
    print(f"{len(rows)} Book of Mormon chunks ({sum(len(v) for v in q)} episodes); "
          f"{len(c)} candidate units {sizes} -> {VECS}")  # fmt: skip
    return 0


def windows(n_eps: int, n: int | None) -> list[tuple[int, int]]:
    """The middle ``n`` episodes first, then every other non-overlapping run of ``n`` to its left
    and right; the whole profile when ``n`` is None or it is no longer than ``n``."""
    if n is None or n_eps <= n:
        return [(0, n_eps)]
    mid = (n_eps - n) // 2
    out = [(mid, mid + n)]
    out += [(s_, s_ + n) for s_ in range(mid - n, -1, -n)]
    out += [(s_, s_ + n) for s_ in range(mid + n, n_eps - n + 1, n)]
    return out


def rank() -> int:
    import pyarrow.parquet as pq

    from sweep.episodes import cut, load, padded, topk_scores

    cfg = load_config()
    ls = cfg["library_search"]
    z = np.load(VECS)
    split = lambda v, counts: np.split(v.astype(np.float32), np.cumsum(counts)[:-1])  # noqa: E731
    cands = dict(zip(z["c_units"].tolist(), split(z["c"], z["c_counts"]), strict=True))
    q_words = z["q_words"]
    q_of = np.repeat(np.arange(len(q_words)), z["q_counts"])
    Q = z["q"].astype(np.float32)
    eps, _ = load(ls["tag"])
    swept = sorted(u[len("profile:") :] for u in eps if u.startswith("profile:"))
    people = {r["author"]: r for r in pq.read_table("data/sweep/people.parquet").to_pylist()}
    status = np.array([people[a]["status"] for a in swept])
    possible = ~np.isin(status, ["dead", "too_young"])
    small = len(cands[REVELATION])
    doc = {**stamp(), "exploratory": True, "encoder": ls["encoder"], "query_chunks": len(q_words),
           "query_episodes": len(Q), "library_authors": len(swept),
           "status": {s_: int((status == s_).sum()) for s_ in sorted(set(status))},
           "small_episodes": small, "rankings": {}}  # fmt: skip
    for name, n in (("small", small), ("large", ls["large_episodes"]), ("full", None)):
        G, M = padded([cut(eps[f"profile:{a}"], n) for a in swept])
        subsets = {"all": np.ones(len(Q), dtype=bool)}
        subsets.update({f"{w}_words": (q_words[q_of] == w) for w in sorted(set(q_words.tolist()))})
        res: dict = {"profile_episodes": n, "candidates": {}}
        for sub, mask in subsets.items():
            lib = topk_scores(Q[mask], G, M, [1])[1]
            order = np.argsort(-lib)
            if sub == "all":
                lib_all, order_all = lib, order
                res["top"] = [{"rank": i + 1, "author": swept[j], "score": round(float(lib[j]), 4),
                               "status": status[j], "born": people[swept[j]]["born"],
                               "died": people[swept[j]]["died"],
                               "date_source": people[swept[j]]["date_source"]}
                              for i, j in enumerate(order[: ls["top"]])]  # fmt: skip
                dead = status[order] == "dead"
                res["dead_in_top"] = {str(k): int(dead[:k].sum()) for k in ls["dead_k"]}
                res["dead_share_of_library"] = round(float((status == "dead").mean()), 4)
            else:
                a_, b_ = set(order_all[: ls["overlap_k"]]), set(order[: ls["overlap_k"]])
                res.setdefault("chunk_lengths", {})[sub] = {
                    "chunks": int((q_words == int(sub.split("_")[0])).sum()),
                    f"top{ls['overlap_k']}_shared_with_all": len(a_ & b_),
                    "top5": [swept[j] for j in order[:5]]}  # fmt: skip
        for u, v in sorted(cands.items()):
            if n is not None and len(v) < n:
                continue
            ws = windows(len(v), n)
            Gc, Mc = padded([v[a:b] for a, b in ws])
            sc = topk_scores(Q, Gc, Mc, [1])[1]
            r_all = [int((lib_all > x).sum()) + 1 for x in sc]
            r_pos = [int((lib_all[possible] > x).sum()) + 1 for x in sc]
            res["candidates"][u] = {
                "episodes": len(v), "slices": len(ws), "score": round(float(sc[0]), 4),
                "rank_among_all": r_all[0], "rank_among_possible": r_pos[0],
                "slice_ranks_among_all": {"best": min(r_all), "median": float(np.median(r_all)),
                                          "worst": max(r_all)}}  # fmt: skip
        res["compared_with"] = {"library_all": len(swept), "library_possible": int(possible.sum())}
        doc["rankings"][name] = res
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n")
    for name, res in doc["rankings"].items():
        print(f"\n== {name} (profile episodes {res['profile_episodes']}); dead in top "
              f"{res['dead_in_top']} (library share {res['dead_share_of_library']})")  # fmt: skip
        for t in res["top"][:20]:
            print(f"  {t['rank']:3d} {t['score']:.4f} {t['status']:9s} {t['born']}-{t['died']} "
                  f"{t['author']}")  # fmt: skip
        for u, c_ in sorted(res["candidates"].items(), key=lambda kv: kv[1]["rank_among_all"]):
            print(f"  cand {u:55s} rank {c_['rank_among_all']:6d} of all, "
                  f"{c_['rank_among_possible']:6d} of possible; slices {c_['slices']} "
                  f"{c_['slice_ranks_among_all']}")  # fmt: skip
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["embed", "rank"])
    return {"embed": embed, "rank": rank}[ap.parse_args(argv).cmd]()


if __name__ == "__main__":
    sys.exit(main())
