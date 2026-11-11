"""Seed stability of the candidate models (BOM-77, first half; Amendment 50).

Part 1 trained each candidate and control model once, and V2 showed what one seed can hide (9% to
98% false matches across seeds). Every Amendment 43 unit is fine-tuned again with
``part2.seeds_per_candidate`` further seeds, same inputs and settings, and scored on the sealed
set as Amendment 43 (mean window log-loss less the base model's). ``report`` ranks the units on
every Book of Mormon chunk per seed and gives each unit's mean rank and rank-first share for each
seed and the original run, and their range.

The seed models' weights are not kept (owner, 2026-11-11: Stage 0 publishes scores); each is
rebuilt from the published base model, the encoded inputs (``alm.candidates plan``) and its seed.

Usage::

    python -m eval.part2_seeds run pilot|base|mid   # GPU: data/blind/part2/seeds_<size>.json
    python -m eval.part2_seeds report               # Mac: data/benchmark/part2/seeds_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

BLIND = Path("data/blind/part2")
OUT = Path("data/benchmark/part2/seeds_report.json")


def run(size: str, micro: int) -> int:
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, finetune, window_loss
    from alm.candidates import INPUTS, PLAN
    from eval.js_register import _rows
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    a = cfg["alm"]
    n_seeds = cfg["part2"]["seeds_per_candidate"]
    dev = _device()
    model = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    tok = Tokenizer.from_file(str(TOKENIZER))
    rows = sorted(_rows(), key=lambda r: r["id"])
    texts = [tok.encode(r["text"]).ids for r in rows]
    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in texts]
    out = BLIND / f"seeds_{size}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = json.loads(out.read_text()) if out.exists() else {"models": {}}
    units = [u["key"] for u in json.loads(PLAN.read_text())["units"]]
    for k in range(1, n_seeds + 1):
        for unit in units:
            name = f"{unit}#seed{k}"
            if name in res["models"]:
                continue
            ids = np.load(INPUTS / f"{unit}.npz")["train"]
            model.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:part2-seed{k}:{unit}", cfg)
            torch.manual_seed(seed)
            info = finetune(model, ids, cfg, seed, micro, dev,
                            cfg["timelocked_lm"]["finetune_lr"])  # fmt: skip
            with torch.no_grad():
                loss = [window_loss(model, x, a["score_window"], dev) for x in texts]
            res["models"][name] = {"seed": seed, "steps": info["steps"], "scores": {
                r["id"]: float(np.mean(np.array(loss[i]) - np.array(base[i])))
                for i, r in enumerate(rows)}}  # fmt: skip
            out.write_text(json.dumps(res))
            print(f"  seeds {size} {name}: {len(ids):,} tokens", flush=True)
    return 0


def report() -> int:
    from eval.js_register import A43, KEY

    key = json.loads(KEY.read_text())
    bom = [i for i, k in key.items() if k["kind"] == "bom"]
    res: dict = {}
    for size in ("pilot", "base", "mid"):
        f = BLIND / f"seeds_{size}.json"
        if not f.exists():
            continue
        models = json.loads(f.read_text())["models"]
        prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        runs: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)  # run -> unit -> id
        for name, v in models.items():
            unit, seed = name.split("#")
            runs[seed][unit] = v["scores"]
        units = sorted({u for r in runs.values() for u in r})
        runs["original"] = {u: {i: prior[i]["scores"][u] for i in bom if u in prior[i]["scores"]}
                            for u in units}  # fmt: skip
        per: dict[str, dict] = defaultdict(dict)
        for run_name, by_unit in sorted(runs.items()):
            if set(by_unit) != set(units):
                continue  # a seed not finished for every unit is not ranked
            ranks: dict[str, list[int]] = defaultdict(list)
            for i in bom:
                order = sorted(units, key=lambda u: by_unit[u][i])
                for r, u in enumerate(order, 1):
                    ranks[u].append(r)
            for u in units:
                first = float(np.mean([r == 1 for r in ranks[u]]))
                per[u][run_name] = {"mean_rank": float(np.mean(ranks[u])), "first_share": first}
        summary = {}
        for u, by in per.items():
            new = [v["first_share"] for k, v in by.items() if k != "original"]
            orig = by.get("original", {}).get("first_share")
            rng = [min(new), max(new)] if new else None
            stable = None if orig is None or rng is None else rng[0] <= orig <= rng[1]
            summary[u] = {"runs": by, "first_share_range_new": rng,
                          "original_first_share": orig, "seed_stable": stable}  # fmt: skip
        res[size] = {"units": len(units), "chunks": len(bom), "per_unit": summary}
        top = sorted(summary.items(), key=lambda kv: -(kv[1]["original_first_share"] or 0))[:3]
        line = "; ".join(f"{u} first {v['original_first_share']:.2f} original, "
                         f"{v['first_share_range_new']} new" for u, v in top)  # fmt: skip
        print(f"{size}: {line}")
    OUT.write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["run", "report"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "report":
        return report()
    if not a.size:
        ap.error("run needs a size")
    return run(a.size, a.micro_batch)


if __name__ == "__main__":
    sys.exit(main())
