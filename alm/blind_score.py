"""The authorial language models on the sealed set (BOM-32; 5.2, 6.1, Amendments 22, 30, 32).

As validated (``alm.candidates validate``): a text's score for a unit is the mean, over
``alm.score_window``-token windows, of the unit model's log-loss minus the base model's; the
closed set is the lowest-scoring candidate unit; 6.1's statistic is each candidate's margin, the
best control model's score minus the candidate's (``alm.candidates.margins``), called against the
thresholds calibrated on the candidates' held-out windows (``blind.thresholds``). The models are
BOM-28's kept weights at the working size, ``data/corpus/alm/candidates/<size>/<unit>.pt``, each
checked against the SHA-256 recorded when it was trained. Text is encoded as in training (the
masked words joined by spaces).

Called by ``blind.run``; reads no key. Returns names and numbers only. One model in memory at a
time; on an H100 the whole sealed set takes about a minute per unit model.
"""

from __future__ import annotations

import json

import numpy as np


def scores(losses: dict[str, list[list[float]]], base: list[list[float]]) -> list[dict[str, float]]:
    """Per text, unit -> mean window log-loss minus the base model's."""
    return [{u: float(np.mean(np.array(ls[i]) - np.array(base[i]))) for u, ls in losses.items()}
            for i in range(len(base))]  # fmt: skip


def decide(s: dict[str, float], kinds: dict[str, str], th: dict | None) -> dict:
    from alm.candidates import margins
    from blind.thresholds import call

    cands = {u: v for u, v in s.items() if kinds[u] == "candidate"}
    m = margins(s, kinds)
    return {"scores": s, "first": min(s, key=lambda u: (s[u], u)),
            "first_candidate": min(cands, key=lambda u: (cands[u], u)), "margins": m,
            "call": {u: call(v, th) for u, v in m.items()} if th else None,
            "call_achievable": {u: call(v, th, "achievable") for u, v in m.items()}
            if th else None}  # fmt: skip


def score(rows: list[dict], cfg: dict, size: str, th: dict) -> dict:
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, window_loss
    from alm.candidates import PLAN, WORK, _sha
    from timelocked_lm.release import TOKENIZER

    a = cfg["alm"]
    plan = json.loads(PLAN.read_text())["units"]
    kinds = {u["key"]: u["kind"] for u in plan}
    work = WORK / size
    info = {u: json.loads((work / f"{u}.json").read_text()) for u in kinds}
    tok = Tokenizer.from_file(str(TOKENIZER))
    rows = sorted(rows, key=lambda r: r["id"])
    ids = [tok.encode(r["text"]).ids for r in rows]
    dev = _device()
    model = _base(size, cfg).to(dev).eval()
    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in ids]
        losses = {}
        for u in sorted(kinds):
            w = work / f"{u}.pt"
            if _sha(w) != info[u]["weights_sha256"]:
                raise SystemExit(f"{w}: SHA-256 differs from the one recorded at training")
            model.load_state_dict(torch.load(w, map_location="cpu"))
            losses[u] = [window_loss(model, x, a["score_window"], dev) for x in ids]
    per = scores(losses, base)
    return {r["id"]: {"windows": len(base[i]), **decide(per[i], kinds, th["alm"])}
            for i, r in enumerate(rows)}  # fmt: skip
