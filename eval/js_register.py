"""Joseph Smith's revelatory and non-revelatory writing against the sealed text (Amendment 44).

Post hoc, after unblinding. His only pre-1830 sample is revelation, in a scriptural voice like the
Book of Mormon's; this asks whether the methods' closeness to him holds for his ordinary prose.
His non-revelatory writing (``POOL_FROM``: the 1832-33 dictated letters and the 1831-32 handwritten
letters and history) is pooled into one unit (``POOL``) and scored on the sealed set beside every
other unit, in the Amendment 43 setting (Book of Mormon quotations dropped):

- ``classic``: Burrows' and Cosine Delta and General Imposters with the pooled unit added to the
  candidate references (withheld decoy spans already removed), against the Amendment 43
  thresholds;
- ``alm <size>`` (on a GPU): one model fine-tuned on the pooled unit exactly as the other units
  (``alm.benchmark.finetune``, seed from the unit's key), its score on each sealed text (mean
  window log-loss less the base model's), as ``alm.blind_score``; combined with the Amendment 43
  scores of every other unit, which share the base model and windows;
- ``report``: for the Book of Mormon chunks, each Joseph Smith sample's mean rank among the
  candidate samples and how often it is ranked first, per method and size.

Numbers only: ``data/blind/a44/``. Usage::

    python -m eval.js_register classic
    python -m eval.js_register alm pilot|base|mid
    python -m eval.js_register report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

POOL = "cand__joseph-smith__nonrevelatory__post1830"
POOL_FROM = ["cand__joseph-smith__dictated__post1830", "cand__joseph-smith__handwritten__post1830"]
REVELATION = "cand__joseph-smith__dictated__pre1830"
OUT = Path("data/blind/a44")
A43 = Path("data/blind/a43")
WEIGHTS = Path("data/corpus/alm/a44")
SEALED = Path("data/corpus/blind/sealed.jsonl")
KEY = Path("~/.bom-blind/key.json").expanduser()  # used only by report, after unblinding


def _rows() -> list[dict]:
    return [json.loads(ln) for ln in SEALED.read_text().splitlines()]


def classic() -> int:
    from classic.blind_score import pool, references, score
    from metadata.config import load as load_config

    cfg = load_config()
    refs = references()
    toks = [t for u in POOL_FROM for t in refs[u]["tokens"]]
    refs[POOL] = {**refs[POOL_FROM[0]], "sample": "nonrevelatory", "words": len(toks),
                  "flag": "", "tokens": toks}  # fmt: skip
    th = json.loads((A43 / "thresholds.json").read_text())["thresholds"]
    res = score(_rows(), cfg, refs, pool(cfg), th)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "classic.json").write_text(json.dumps({"pool": POOL, "words": len(toks), "ids": res}))
    print(f"classic: {len(res)} ids, pooled unit {len(toks):,} tokens -> {OUT / 'classic.json'}")
    return 0


def alm(size: str, micro: int) -> int:
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, finetune, window_loss
    from alm.candidates import INPUTS
    from metadata.config import derive_seed
    from metadata.config import load as load_config
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    a = cfg["alm"]
    ids = np.concatenate([np.load(INPUTS / f"{u}.npz")["train"] for u in POOL_FROM])
    dev = _device()
    model = _base(size, cfg).to(dev).eval()
    tok = Tokenizer.from_file(str(TOKENIZER))
    rows = sorted(_rows(), key=lambda r: r["id"])
    texts = [tok.encode(r["text"]).ids for r in rows]
    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in texts]
    seed = derive_seed(f"{a['train_seed']}:candidates:{POOL}", cfg)
    torch.manual_seed(seed)
    info = finetune(model, ids, cfg, seed, micro, dev, cfg["timelocked_lm"]["finetune_lr"])
    OUT.mkdir(parents=True, exist_ok=True)
    WEIGHTS.mkdir(parents=True, exist_ok=True)  # kept and published, like every trained model
    torch.save({k: v.cpu() for k, v in model.state_dict().items()}, WEIGHTS / f"{POOL}_{size}.pt")
    with torch.no_grad():
        loss = [window_loss(model, x, a["score_window"], dev) for x in texts]
    s = {r["id"]: float(np.mean(np.array(loss[i]) - np.array(base[i])))
         for i, r in enumerate(rows)}  # fmt: skip
    (OUT / f"alm_{size}.json").write_text(json.dumps({"pool": POOL, "size": size,
                                                      "train_tokens": int(len(ids)), **info,
                                                      "scores": s}))  # fmt: skip
    print(f"alm {size}: pooled unit {len(ids):,} tokens, {len(s)} ids -> {OUT}/alm_{size}.json")
    return 0


def _ranks(per_id: dict[str, dict[str, float]], lower_is_closer: bool) -> dict[str, dict]:
    """Each Joseph Smith unit's mean rank among candidate units, and times ranked first."""
    out: dict[str, dict] = {}
    for unit in [REVELATION, POOL, *POOL_FROM]:
        ranks = []
        for s in per_id.values():
            c = {u: v for u, v in s.items() if u.startswith("cand__")}
            if unit not in c:
                continue
            order = sorted(c, key=lambda u: c[u] if lower_is_closer else -c[u])
            ranks.append(order.index(unit) + 1)
        if ranks:
            out[unit] = {"mean_rank": float(np.mean(ranks)), "first": sum(r == 1 for r in ranks),
                         "of_units": len(c), "chunks": len(ranks)}  # fmt: skip
    return out


def report() -> int:
    key = json.loads(KEY.read_text())
    bom = {i for i, k in key.items() if k["kind"] == "bom"}
    res: dict = {"pool": POOL, "methods": {}}
    c = json.loads((OUT / "classic.json").read_text())["ids"]
    for m, lower in (("cosine_delta", True), ("burrows_delta", True), ("general_imposters", False)):
        res["methods"][m] = _ranks({i: c[i][m] for i in bom}, lower)
    for size in ("pilot", "base", "mid"):
        p = OUT / f"alm_{size}.json"
        if not p.exists():
            continue
        pooled = json.loads(p.read_text())["scores"]
        prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        per = {i: {**prior[i]["scores"], POOL: pooled[i]} for i in bom}
        res["methods"][f"alm_{size}"] = _ranks(per, True)
    (OUT / "report.json").write_text(json.dumps(res, indent=1) + "\n")
    for m, r in res["methods"].items():
        print(m, {u.replace("cand__joseph-smith__", ""): (round(v["mean_rank"], 1), v["first"])
                  for u, v in r.items()})  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["classic", "alm", "report"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "alm":
        return alm(a.size, a.micro_batch)
    return classic() if a.cmd == "classic" else report()


if __name__ == "__main__":
    sys.exit(main())
