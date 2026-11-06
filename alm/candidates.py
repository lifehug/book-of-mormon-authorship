"""Authorial language models for the candidates and control groups (BOM-28; pre-registration 3,
5.2, 6.1; Amendment 30, ``docs/alm-plan.md``).

One copy of the working time-locked model (``base`` or ``large``, chosen by the benchmark) is
fine-tuned per candidate sample and per control group, with Amendment 22's settings, and its
weights are kept: BOM-32 scores the sealed text with them. Nothing here reads the Book of Mormon.

* **Candidate units:** each candidate x sample type x period with text in an admitted provenance
  tier (Amendment 5: handwritten, dictated, printed by the author, posthumous; scribal copies
  are catalogued and left out), as the BOM-13 counts list them, King James spans masked (4.4).
  Pre-1830 units are the confirmatory ones (section 3); post-1830 units are Amendment 5's
  secondary analysis. Joseph Smith's dictated and handwritten samples are separate units.
* **Control units:** one per control group (pseudo-biblical, curated list; 1820s sermons and
  tracts; histories and Native American origin texts; general prose), each a seeded sample of
  about ``alm.control_words`` masked words: volumes in a seeded order, the middle of each, at
  least ``alm.control_passage_words`` from every volume used.
* **Held-out text:** as Amendment 22, a unit with at least 10 blocks of 1,000 words holds out
  its last max(5, ceil(n/4)) blocks; its tests are distinct 5,000-word windows in that tail (up
  to ``alm.max_tests``). The tail is never trained on, so it also supplies BOM-32's decoys. A
  shorter unit trains on everything and is not tested.

``plan`` (CPU, on the Mac) writes the units and their held-out positions (names and numbers
only) and the encoded inputs (licensed text in another form, under ``data/corpus/``). ``train``
fine-tunes each unit, keeps its weights and scores every unit's tests; it resumes per unit.
``validate`` writes the scores: closed set among all units and among candidates, and 6.1's
authorial-model score, the margin between a candidate's model and the best control model.

Usage::

    python -m alm.candidates plan                                 # -> alm_candidates_plan.json
    python -m alm.candidates train pilot|base|large [--micro-batch 8]   # weights, scores
    python -m alm.candidates validate pilot|base|large    # -> alm_candidates_<size>.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/benchmark")
PLAN = OUT / "alm_candidates_plan.json"
WORK = Path("data/corpus/alm/candidates")
INPUTS = WORK / "inputs"
ADMITTED = {"handwritten", "dictated", "printed_by_author", "posthumous"}  # Amendment 5
CONTROL_GROUPS = ("pseudo_biblical", "sermons_1820s", "history", "general_prose")
BLOCK = 1000


# ---- pure logic (tested) -----------------------------------------------------------------------


def slug(*parts: str) -> str:
    return "__".join(p.lower().replace(" ", "-").replace(".", "") for p in parts)


def holdout_blocks(n: int, k: int, min_ref: int, share: float) -> int | None:
    """Blocks held out of a unit of ``n`` 1,000-word blocks (Amendment 22): None if too short."""
    if n < k + min_ref:
        return None
    return max(k, math.ceil(n * share))


def window_starts(n: int, h: int, k: int, most: int, rng: random.Random) -> list[int]:
    """Start blocks of the distinct ``k``-block windows inside the held-out tail."""
    starts = list(range(n - h, n - k + 1))
    return sorted(rng.sample(starts, most)) if len(starts) > most else starts


def control_sample(vols: list[tuple[str, list[str]]], target: int, passage: int,
                   rng: random.Random) -> list[tuple[str, list[str]]]:  # fmt: skip
    """Volumes in a seeded order, the middle ``max(passage, ceil(target / len(vols)))`` words of
    each, until ``target`` words are taken."""
    if not vols:
        return []
    per = max(passage, math.ceil(target / len(vols)))
    order = rng.sample(range(len(vols)), len(vols))
    out, got = [], 0
    for i in order:
        w, toks = vols[i]
        n = min(per, target - got)
        s = max(0, len(toks) // 2 - n // 2)
        part = toks[s : s + n]
        if part:
            out.append((w, part))
            got += len(part)
        if got >= target:
            break
    return out


def margins(scores: dict[str, float], kinds: dict[str, str]) -> dict[str, float]:
    """6.1: for each candidate unit, the best (lowest) control score minus its own score; above
    zero means the candidate's model fits better than every control model."""
    best = min(scores[u] for u in scores if kinds[u] == "control")
    return {u: best - s for u, s in scores.items() if kinds[u] == "candidate"}


# ---- texts -------------------------------------------------------------------------------------


def candidate_words() -> dict[tuple[str, str, str], list[tuple[str, list[str]]]]:
    """(candidate, sample, period) -> [(doc id, masked original words)], admitted tiers only."""
    from kjv_mask.run import _docs
    from ocr_fix.candidates import units
    from segment.build import original_words

    meta = {"cand:" + u["unit"].replace(":", "__"): (u["author"], u["sample"], u["period"])
            for u in units()}  # fmt: skip
    spans = {}
    for ln in Path("data/kjv_mask/candidates/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    out: dict[tuple[str, str, str], list] = defaultdict(list)
    for d in sorted(_docs("candidates"), key=lambda d: d["id"]):
        if d["id"] in meta:
            key = meta[d["id"]]
        else:  # Joseph Smith Papers samples: cand:<person>__<sample>__<period>
            person, sample, period = d["id"].removeprefix("cand:").split("__")
            key = (person.replace("-", " ").title(), sample, period)
        if key[1] in ADMITTED:
            out[key].append((d["id"], original_words(d["load"](), spans.get(d["id"], []))))
    return dict(out)


def control_words(cfg: dict) -> dict[str, list[tuple[str, list[str]]]]:
    """Control group -> [(volume, masked original words)] of its seeded sample."""
    from alm.benchmark import _words

    a = cfg["alm"]
    out = {}
    for g in CONTROL_GROUPS:
        if g == "pseudo_biblical" and cfg["controls"]["pseudo_biblical"] == "curated":
            ids = Path("data/controls/pseudo_biblical_curated.txt").read_text().split()
        else:
            ids = [json.loads(ln)["work_id"] for ln in
                   Path(f"data/controls/{g}.jsonl").read_text().splitlines()]  # fmt: skip
        ids = sorted(ids)
        rng = random.Random(derive_seed(f"{a['control_seed']}:{g}", cfg))
        # read twice as many volumes as the sample needs at the minimum passage, in a seeded
        # order (the curated pseudo-biblical list is small and read whole)
        need = 2 * math.ceil(a["control_words"] / a["control_passage_words"])
        pool = rng.sample(ids, min(need, len(ids)))
        got = _words(pool, [Path("data/kjv_mask/controls/spans.jsonl")])
        vols = [(w, got[w]) for w in sorted(got)]
        out[g] = control_sample(
            vols,
            a["control_words"],
            a["control_passage_words"],
            random.Random(derive_seed(f"{a['control_seed']}:{g}:order", cfg)),
        )
    return out


# ---- plan ----------------------------------------------------------------------------------------


def plan() -> int:
    from tokenizers import Tokenizer

    from timelocked_lm.release import EOT, TOKENIZER

    cfg = load_config()
    a, bm = cfg["alm"], cfg["benchmark"]
    k = bm["test_words"] // BLOCK
    floor = cfg["candidates"]["min_masked_words"]
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    units: list[tuple[str, dict, list[tuple[str, list[str]]]]] = []
    for (who, sample, period), docs in sorted(candidate_words().items()):
        units.append((slug("cand", who, sample, period),
                      {"kind": "candidate", "candidate": who, "sample": sample, "period": period,
                       "confirmatory": period == "pre1830"}, docs))  # fmt: skip
    for g, docs in control_words(cfg).items():
        units.append((slug("ctrl", g), {"kind": "control", "group": g}, docs))
    INPUTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, meta, docs in units:
        flat = [w for _, ws in docs for w in ws]
        n = len(flat) // BLOCK
        h = holdout_blocks(n, k, bm["min_reference_blocks"], a["holdout_share"])
        cut = len(flat) if h is None else (n - h) * BLOCK
        train, used = [], 0  # the first ``cut`` words, document boundaries kept
        for _, ws in docs:
            if used >= cut:
                break
            train.append(ws[: cut - used])
            used += len(train[-1])
        tests = []
        if h is not None:
            rng = random.Random(derive_seed(f"{a['test_seed']}:candidates:{key}", cfg))
            for s in window_starts(n, h, k, a["max_tests"], rng):
                words = flat[s * BLOCK : (s + k) * BLOCK]
                tests.append({"where": f"blocks {s}-{s + k - 1} of {n}",
                              "ids": tok.encode(" ".join(words)).ids})  # fmt: skip
        ids = np.array([i for ws in train for i in [*tok.encode(" ".join(ws)).ids, eot]],
                       dtype=np.int32)  # fmt: skip
        lens = [len(t["ids"]) for t in tests]
        np.savez(INPUTS / f"{key}.npz", train=ids,
                 tests=np.array([i for t in tests for i in t["ids"]], dtype=np.int32),
                 lens=np.array(lens, dtype=np.int64))  # fmt: skip
        words = len(flat)
        rows.append({"key": key, **meta, "docs": [d for d, _ in docs], "words": words,
                     "flag": "unreliable sample" if words < floor else "",
                     "train_words": used, "train_tokens": int(len(ids)),
                     "holdout": None if h is None else {
                         "blocks": h, "of": n, "first_word": (n - h) * BLOCK,
                         "tests": [t["where"] for t in tests]}})  # fmt: skip
        print(f"  {key}: {words:,} words, train {used:,}, "
              f"{'untested' if h is None else f'{len(tests)} tests'}", flush=True)  # fmt: skip
    PLAN.write_text(json.dumps({**stamp(), "block_words": BLOCK, "test_words": bm["test_words"],
                                "units": rows}, indent=1) + "\n")  # fmt: skip
    print(f"{len(rows)} units -> {PLAN}; inputs in {INPUTS}")
    return 0


# ---- train and validate ------------------------------------------------------------------------


def _tests(rows: list[dict]) -> list[tuple[str, int, list[int]]]:
    out = []
    for r in rows:
        z = np.load(INPUTS / f"{r['key']}.npz")
        pos = 0
        for i, n in enumerate(z["lens"].tolist()):
            out.append((r["key"], i, z["tests"][pos : pos + n].tolist()))
            pos += n
    return out


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def train(size: str, micro: int) -> int:
    import torch

    from alm.benchmark import _base, _device, finetune, window_loss

    cfg = load_config()
    a = cfg["alm"]
    rows = json.loads(PLAN.read_text())["units"]
    work = WORK / size
    work.mkdir(parents=True, exist_ok=True)
    dev = _device()
    tests = _tests(rows)
    model = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    path = work / "base.json"
    if not path.exists():
        path.write_text(json.dumps([window_loss(model, ids, a["score_window"], dev)
                                    for _, _, ids in tests]))  # fmt: skip
    print(f"{len(rows)} units, {len(tests)} tests ({size} on {dev})", flush=True)
    for r in rows:
        info_path = work / f"{r['key']}.json"
        if info_path.exists():
            continue
        ids = np.load(INPUTS / f"{r['key']}.npz")["train"]
        model.load_state_dict(state)
        seed = derive_seed(f"{a['train_seed']}:candidates:{r['key']}", cfg)
        torch.manual_seed(seed)
        info = finetune(model, ids, cfg, seed, micro, dev, cfg["timelocked_lm"]["finetune_lr"])
        wpath = work / f"{r['key']}.pt"
        tmp = wpath.with_suffix(".tmp")
        torch.save({k: v.cpu() for k, v in model.state_dict().items()}, tmp)
        tmp.replace(wpath)
        losses = [window_loss(model, x, a["score_window"], dev) for _, _, x in tests]
        rec = {"train_tokens": int(len(ids)), **info, "weights_sha256": _sha(wpath),
               "losses": losses}  # fmt: skip
        info_path.write_text(json.dumps(rec))
        print(f"  {size} {r['key']}: {len(ids):,} tokens, {info['steps']} steps, "
              f"{info['sec'] / 60:.1f} min", flush=True)  # fmt: skip
    return 0


def validate(size: str) -> int:
    rows = json.loads(PLAN.read_text())["units"]
    kinds = {r["key"]: r["kind"] for r in rows}
    work = WORK / size
    tests = _tests(rows)
    base = json.loads((work / "base.json").read_text())
    got = {r["key"]: json.loads((work / f"{r['key']}.json").read_text()) for r in rows}
    recs = []
    for t, (unit, i, _) in enumerate(tests):
        s = {
            u: float(np.mean(np.array(g["losses"][t]) - np.array(base[t]))) for u, g in got.items()
        }
        cands = {u: v for u, v in s.items() if kinds[u] == "candidate"}
        recs.append({"unit": unit, "test": i, "windows": len(base[t]), "scores": s,
                     "predicted": min(s, key=lambda u: (s[u], u)),
                     "predicted_candidate": min(cands, key=lambda u: (cands[u], u)),
                     "margins": margins(s, kinds)})  # fmt: skip
    per = {}
    for r in rows:
        mine = [x for x in recs if x["unit"] == r["key"]]
        if not mine:
            per[r["key"]] = {"tests": 0}
            continue
        per[r["key"]] = {
            "tests": len(mine),
            "closed_set_all": sum(x["predicted"] == r["key"] for x in mine) / len(mine),
        }
        if r["kind"] == "candidate":
            per[r["key"]]["closed_set_candidates"] = sum(
                x["predicted_candidate"] == r["key"] for x in mine
            ) / len(mine)
            per[r["key"]]["own_margin_mean"] = float(np.mean([x["margins"][r["key"]]
                                                              for x in mine]))  # fmt: skip
        else:  # a control's text: how far the best candidate model beats every control model
            per[r["key"]]["best_candidate_margin_mean"] = float(np.mean(
                [max(x["margins"].values()) for x in mine]))  # fmt: skip
    training = {u: {k: v for k, v in g.items() if k != "losses"} for u, g in got.items()}
    out = OUT / f"alm_candidates_{size}.json"
    out.write_text(json.dumps({**stamp(), "size": size, "units": per, "training": training,
                               "records": recs}, indent=1) + "\n")  # fmt: skip
    tested = [u for u, v in per.items() if v["tests"]]
    acc = sum(per[u]["closed_set_all"] * per[u]["tests"] for u in tested) / max(
        1, sum(per[u]["tests"] for u in tested)
    )
    print(
        f"{size}: {len(rows)} units, {len(tested)} tested; held-out closed set {acc:.3f} -> {out}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "train", "validate"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "large"])
    ap.add_argument("--micro-batch", type=int, default=8, help="memory only; same update")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        return plan()
    if not a.size:
        ap.error("train and validate need a size")
    return train(a.size, a.micro_batch) if a.cmd == "train" else validate(a.size)


if __name__ == "__main__":
    sys.exit(main())
