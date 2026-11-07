"""The classical methods on the sealed set (BOM-32; 5.1, 6.1, Amendments 30 and 32).

As validated on the benchmark (``eval.benchmark.run_task``): references are cut into 1,000-token
blocks, the vocabulary is the registered middle MFW count from the reference blocks only, Burrows
and Cosine Delta rank the candidates by distance to their mean profile (z-scored on the blocks),
General Imposters scores each candidate with the registered settings against a genre-matched
pool, and ENSC classifies with the benchmark's calibrated shrinkage and alpha. 6.1's call uses the
committed GI thresholds.

**References** are Amendment 30's candidate units (admitted provenance tiers, KJV masked), with
every span in ``data/blind/withheld.json`` cut out, so no decoy is scored against its own text.
**Imposters** are the pseudo-biblical benchmark task's pool (the curated list, filled from the
pseudo-biblical controls), less the candidates' own works and every withheld source volume.

Called by ``blind.run``; reads no key. Returns names and numbers only.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

WITHHELD = Path("data/blind/withheld.json")


def withheld() -> dict[str, list[tuple[int, int]]]:
    if not WITHHELD.exists():
        return {}
    out: dict[str, list[tuple[int, int]]] = {}
    for s in json.loads(WITHHELD.read_text())["spans"]:
        out.setdefault(s["source"], []).append((s["start"], s["end"]))
    return out


def drop_spans(words: list[str], spans: list[tuple[int, int]]) -> list[str]:
    """``words`` without the word ranges ``[start, end)`` in ``spans``."""
    keep = np.ones(len(words), dtype=bool)
    for a, b in spans:
        keep[max(0, a) : max(0, b)] = False
    return [w for w, k in zip(words, keep, strict=True) if k]


def source_of(doc_id: str) -> str:
    """A candidate document's name in ``withheld.json`` (``blind.seal.decoy_pool``)."""
    return f"candidates/clean/{doc_id.removeprefix('cand:')}.txt"


def references() -> dict[str, dict]:
    """Unit key -> its candidate, flags and reference tokens (withheld spans removed)."""
    from alm.candidates import candidate_words, slug
    from classic.features import tokenize
    from metadata.config import load as load_config

    floor = load_config()["candidates"]["min_masked_words"]
    held = withheld()
    out = {}
    for (who, sample, period), docs in sorted(candidate_words().items()):
        words = [w for d, ws in docs for w in drop_spans(ws, held.get(source_of(d), []))]
        out[slug("cand", who, sample, period)] = {
            "candidate": who, "sample": sample, "period": period,
            "confirmatory": period == "pre1830", "words": len(words),
            "flag": "unreliable sample" if len(words) < floor else "",
            "tokens": tokenize(" ".join(words)),
        }  # fmt: skip
    return out


def pool(cfg: dict) -> list[list[str]]:
    """The pseudo-biblical task's imposter pool, less candidates' works and withheld volumes."""
    from eval.benchmark import TASKS, imposter_pool
    from metadata.controls import _candidate_authors

    spec = json.loads(TASKS.read_text())["pseudo_biblical"]
    exclude = set(spec.get("exclude_from_pool", [])) | set(withheld())
    authors = tuple(sorted(_candidate_authors()))
    return imposter_pool(spec["imposter_pool"], exclude, cfg, None, authors,
                         spec.get("imposter_fill"))  # fmt: skip


def score(rows: list[dict], cfg: dict, refs: dict[str, dict], imposters: list[list[str]],
          th: dict) -> dict:  # fmt: skip
    """Per sealed id: both Deltas' distances and ranking, GI per unit with 6.1's call, ENSC."""
    from blind.thresholds import call
    from classic import (
        ENSC,
        build_vocabulary,
        frequency_matrix,
        general_imposters,
        nearest_authors,
        tokenize,
        word_counts,
    )
    from eval.power import blocks
    from metadata.config import classic_kwargs, derive_seed

    kw = classic_kwargs(cfg)
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    units = sorted(u for u, r in refs.items() if blocks(r["tokens"]))
    docs = [word_counts(b) for u in units for b in blocks(refs[u]["tokens"])]
    labels = [u for u in units for _ in blocks(refs[u]["tokens"])]
    vocab = build_vocabulary(docs, top_n=top_n, min_doc_fraction=kw["mfw_min_doc_fraction"])
    X = frequency_matrix(docs, vocab)
    prof = {u: X[[i for i, y in enumerate(labels) if y == u]].mean(axis=0) for u in units}
    P = frequency_matrix([word_counts(p) for p in imposters], vocab)
    gi_args = {**kw["imposters"],
               "n_imposters": min(len(P), cfg["classic"]["imposters"]["per_trial"])}  # fmt: skip
    gi_th = th["general_imposters"]
    ens = ENSC(shrinkage=th["ensc"]["shrinkage"], alpha=th["ensc"]["alpha"],
               priors=kw["ensc"]["priors"]).fit(X, labels)  # fmt: skip
    rng = random.Random(derive_seed("bom32-classic", cfg))
    out = {}
    for r in sorted(rows, key=lambda r: r["id"]):
        x = frequency_matrix([word_counts(tokenize(r["text"]))], vocab)[0]
        burrows = nearest_authors(x, prof, method="burrows", reference=X)
        cosine = nearest_authors(x, prof, method="cosine", reference=X)
        gs = {u: general_imposters(x, prof[u], P, seed=rng.randrange(2**31), **gi_args)
              for u in units}  # fmt: skip
        e = ens.classify(x)
        out[r["id"]] = {
            "burrows_delta": dict(burrows), "cosine_delta": dict(cosine),
            "burrows_first": burrows[0][0], "cosine_first": cosine[0][0],
            "general_imposters": gs, "gi_first": max(units, key=lambda u: (gs[u], u)),
            "gi_call": {u: call(v, gi_th) for u, v in gs.items()},
            "gi_call_achievable": {u: call(v, gi_th, "achievable") for u, v in gs.items()},
            "ensc": str(e.label),
            "ensc_posteriors": {str(k): float(v) for k, v in e.posteriors.items()},
        }  # fmt: skip
    return out


def units_table(refs: dict[str, dict]) -> dict[str, dict]:
    return {u: {k: v for k, v in r.items() if k != "tokens"} for u, r in refs.items()}
