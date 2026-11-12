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
    python -m eval.js_register style base|mid
    python -m eval.js_register alm pilot|base|mid
    python -m eval.js_register report
    python -m eval.js_register people               # Amendment 53: whole ranking, +/- revelations
    python -m eval.js_register dose pilot|base|mid   # Amendment 45, on a GPU
    python -m eval.js_register dose-report

``dose`` (Amendment 45): every candidate unit with more training text than the revelation sample,
and the pooled non-revelatory unit, fine-tuned again on ``candidates.dose_check.slices`` seeded
contiguous slices of exactly the revelation sample's training tokens; ``dose-report`` ranks the
revelation model among these equal-dose models on the Book of Mormon chunks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from metadata.config import stamp

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


def style(size: str) -> int:
    """The style encoder (297M or 590M backbone) with the pooled unit among the references."""
    from classic.blind_score import pool, references
    from metadata.config import load as load_config
    from style_embed.blind_score import score

    cfg = load_config()
    refs = references()
    toks = [t for u in POOL_FROM for t in refs[u]["tokens"]]
    refs[POOL] = {**refs[POOL_FROM[0]], "sample": "nonrevelatory", "words": len(toks),
                  "flag": "", "tokens": toks}  # fmt: skip
    th = json.loads((A43 / "thresholds.json").read_text())["thresholds"]
    res = score(_rows(), cfg, refs, pool(cfg), th, size=size)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"style_{size}.json").write_text(json.dumps({"pool": POOL, "ids": res}))
    print(f"style {size}: {len(res)} ids -> {OUT / f'style_{size}.json'}")
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


def _dose_units() -> dict[str, np.ndarray]:
    from alm.candidates import INPUTS, PLAN

    plan = json.loads(PLAN.read_text())["units"]
    rev = next(u for u in plan if u["key"] == REVELATION)["train_tokens"]
    units = {u["key"]: np.load(INPUTS / f"{u['key']}.npz")["train"] for u in plan
             if u["kind"] == "candidate" and u["train_tokens"] > rev}  # fmt: skip
    units[POOL] = np.concatenate([np.load(INPUTS / f"{u}.npz")["train"] for u in POOL_FROM])
    return units


def dose(size: str, micro: int) -> int:
    import random

    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, finetune, window_loss
    from alm.candidates import PLAN
    from metadata.config import derive_seed
    from metadata.config import load as load_config
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    a, dc = cfg["alm"], cfg["candidates"]["dose_check"]
    n = next(u for u in json.loads(PLAN.read_text())["units"]
             if u["key"] == REVELATION)["train_tokens"]  # fmt: skip
    dev = _device()
    model = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    tok = Tokenizer.from_file(str(TOKENIZER))
    rows = sorted(_rows(), key=lambda r: r["id"])
    texts = [tok.encode(r["text"]).ids for r in rows]
    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in texts]
    out = OUT.parent / "a45" / f"dose_{size}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = json.loads(out.read_text()) if out.exists() else {"tokens": n, "models": {}}
    for unit, ids in sorted(_dose_units().items()):
        for k in range(dc["slices"]):
            name = f"{unit}#slice{k}"
            if name in res["models"]:
                continue
            rng = random.Random(derive_seed(f"{dc['seed']}:{unit}:{k}", cfg))
            start = rng.randrange(0, len(ids) - n + 1)
            model.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:a45:{name}", cfg)
            torch.manual_seed(seed)
            finetune(model, ids[start : start + n], cfg, seed, micro, dev,
                     cfg["timelocked_lm"]["finetune_lr"])  # fmt: skip
            (WEIGHTS / "a45").mkdir(parents=True, exist_ok=True)
            torch.save({kk: v.cpu() for kk, v in model.state_dict().items()},
                       WEIGHTS / "a45" / f"{name.replace('#', '_')}_{size}.pt")  # fmt: skip
            with torch.no_grad():
                loss = [window_loss(model, x, a["score_window"], dev) for x in texts]
            res["models"][name] = {"start": start, "scores": {
                r["id"]: float(np.mean(np.array(loss[i]) - np.array(base[i])))
                for i, r in enumerate(rows)}}  # fmt: skip
            out.write_text(json.dumps(res))
            print(f"  dose {size} {name}: start {start}", flush=True)
    return 0


def dose_report() -> int:
    key = json.loads(KEY.read_text())
    bom = [i for i, k in key.items() if k["kind"] == "bom"]
    res = {}
    for size in ("pilot", "base", "mid"):
        p = OUT.parent / "a45" / f"dose_{size}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())["models"]
        prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        ranks, firsts = [], 0
        beats = {m: 0 for m in d}
        for i in bom:
            s = {m: d[m]["scores"][i] for m in d}
            r = prior[i]["scores"][REVELATION]
            rank = 1 + sum(v < r for v in s.values())
            ranks.append(rank)
            firsts += rank == 1
            for m, v in s.items():
                beats[m] += r < v
        share = {m: b / len(bom) for m, b in beats.items()}
        res[size] = {"equal_dose_models": len(d), "revelation_mean_rank": float(np.mean(ranks)),
                     "revelation_first": firsts, "chunks": len(bom),
                     "revelation_beats_share": share}  # fmt: skip
        print(f"{size}: revelation model mean rank {np.mean(ranks):.1f} of {len(d) + 1} "
              f"equal-dose models, first in {firsts}/{len(bom)} chunks", flush=True)  # fmt: skip
    (OUT.parent / "a45" / "report.json").write_text(json.dumps(res, indent=1) + "\n")
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


def _scores(bom: set[str]) -> dict[str, tuple[dict[str, dict[str, float]], bool]]:
    """method -> ({chunk: {unit: score}}, lower is closer), every method Amendment 44 scored."""
    out: dict[str, tuple[dict, bool]] = {}
    c = json.loads((OUT / "classic.json").read_text())["ids"]
    for m, lower in (("cosine_delta", True), ("burrows_delta", True), ("general_imposters", False)):
        out[m] = ({i: c[i][m] for i in bom}, lower)
    for size in ("base", "mid"):
        p = OUT / f"style_{size}.json"
        if p.exists():
            st = json.loads(p.read_text())["ids"]
            out[f"style_{size}"] = ({i: st[i]["cosine"] for i in bom}, True)
    for size in ("pilot", "base", "mid"):
        p = OUT / f"alm_{size}.json"
        if p.exists():
            pooled = json.loads(p.read_text())["scores"]
            prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
            out[f"alm_{size}"] = ({i: {**prior[i]["scores"], POOL: pooled[i]} for i in bom}, True)
    return out


def people() -> int:
    """Amendment 53 (post hoc): the whole people-only ranking (candidate units, no controls) on the
    Book of Mormon chunks for every method Amendment 44 scored, with Joseph Smith's revelation
    sample in the list and with it taken out: every unit's mean rank and times ranked first."""
    key = json.loads(KEY.read_text())
    bom = {i for i, k in key.items() if k["kind"] == "bom"}
    res: dict = {"revelation": REVELATION, "pool": POOL, "chunks": len(bom), "methods": {}}
    for m, (per, lower) in _scores(bom).items():
        res["methods"][m] = {}
        for label, drop in (("with_revelations", ()), ("without_revelations", (REVELATION,))):
            ranks: dict[str, list[int]] = {}
            for sc in per.values():
                c = {u: v for u, v in sc.items() if u.startswith("cand__") and u not in drop}
                order = sorted(c, key=lambda u: c[u] if lower else -c[u])
                for r, u in enumerate(order, 1):
                    ranks.setdefault(u, []).append(r)
            res["methods"][m][label] = {
                u: {"mean_rank": float(np.mean(v)), "first": sum(r == 1 for r in v)}
                for u, v in sorted(ranks.items(), key=lambda kv: np.mean(kv[1]))}  # fmt: skip
        top = {k: next(iter(v.items())) for k, v in res["methods"][m].items()}
        print(m, " | ".join(f"{k}: {u.removeprefix('cand__')[:30]} {x['mean_rank']:.1f} "
                            f"({x['first']})" for k, (u, x) in top.items()))  # fmt: skip
    (OUT / "people.json").write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    print(f"-> {OUT / 'people.json'}")
    return 0


def report() -> int:
    key = json.loads(KEY.read_text())
    bom = {i for i, k in key.items() if k["kind"] == "bom"}
    res: dict = {"pool": POOL, "methods": {}}
    c = json.loads((OUT / "classic.json").read_text())["ids"]
    for m, lower in (("cosine_delta", True), ("burrows_delta", True), ("general_imposters", False)):
        res["methods"][m] = _ranks({i: c[i][m] for i in bom}, lower)
    for size in ("base", "mid"):
        p = OUT / f"style_{size}.json"
        if p.exists():
            st = json.loads(p.read_text())["ids"]
            res["methods"][f"style_{size}"] = _ranks({i: st[i]["cosine"] for i in bom}, True)
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
    ap.add_argument("cmd", choices=["classic", "style", "alm", "report", "dose", "dose-report",
                                    "people"])  # fmt: skip
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "alm":
        return alm(a.size, a.micro_batch)
    if a.cmd == "style":
        return style(a.size)
    if a.cmd == "dose":
        return dose(a.size, a.micro_batch)
    if a.cmd == "dose-report":
        return dose_report()
    if a.cmd == "people":
        return people()
    return classic() if a.cmd == "classic" else report()


if __name__ == "__main__":
    sys.exit(main())
