"""The style embeddings on the sealed set (BOM-32; 5.4, 6.1, Amendments 24 and 32).

As validated on the benchmark (``style_embed.benchmark.run``): a text is embedded as one episode
of its passages; each candidate unit's profile is its reference text embedded the same way; the
closed set ranks units by cosine distance (``classic.delta.cosine_delta``); verification is
General Imposters on the vectors with the registered settings against the same genre-matched
pool as the classical methods, embedded. 6.1's call uses thresholds from the style benchmark's
own positives and negatives (``blind.thresholds``). References and pool are
``classic.blind_score``'s (withheld decoy spans and volumes removed).

Called by ``blind.run``; reads no key. Returns names and numbers only.
"""

from __future__ import annotations

import random

import numpy as np


def score(rows: list[dict], cfg: dict, refs: dict[str, dict], imposters: list[list[str]],
          th: dict, embed=None, size: str = "base") -> dict:  # fmt: skip
    """Per sealed id: cosine distance to every unit, GI on the vectors with 6.1's call."""
    from blind.thresholds import call
    from classic import general_imposters, tokenize
    from classic.delta import cosine_delta
    from metadata.config import classic_kwargs, derive_seed
    from style_embed.names import run_dir, tag

    key = tag(size)  # thresholds from that encoder's own benchmark
    if embed is None:
        from style_embed.benchmark import embedder

        embed = embedder(run_dir(size) / "style.pt", cfg, size)
    kw = classic_kwargs(cfg)
    units = sorted(u for u, r in refs.items() if r["tokens"])
    prof = {u: embed(refs[u]["tokens"]) for u in units}
    P = np.stack([embed(p) for p in imposters])
    gi_args = {**kw["imposters"],
               "n_imposters": min(len(P), cfg["classic"]["imposters"]["per_trial"])}  # fmt: skip
    rng = random.Random(derive_seed("bom32-style", cfg))
    out = {}
    for r in sorted(rows, key=lambda r: r["id"]):
        x = embed(tokenize(r["text"]))
        dist = {u: float(cosine_delta(x, prof[u])) for u in units}
        gs = {u: general_imposters(x, prof[u], P, seed=rng.randrange(2**31), **gi_args)
              for u in units}  # fmt: skip
        out[r["id"]] = {"cosine": dist, "first": min(units, key=lambda u: (dist[u], u)),
                        "general_imposters": gs,
                        "call": {u: call(v, th[key]) for u, v in gs.items()},
                        "call_achievable": {u: call(v, th[key], "achievable")
                                            for u, v in gs.items()}}  # fmt: skip
    return out
