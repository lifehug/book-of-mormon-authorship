"""BOM-101: a style encoder trained against the voice (lab; exploratory).

The study's encoders find the kind of writing as much as the writer (lesson 1). This fine-tunes the
second encoder (``style_embed.v2``) on pairs where one writer in two registers counts as the same
and two writers in one register (same genre, same decade) count as different, so the fingerprint
should follow the person across voices. Registers are the second encoder's work genres; a
cross-register pair must pass three duplicate rules (the registry's duplicate groups, the title
keys, a shared-token-run check on the passages). BOM-99's writers found among encoder authors and
the two evaluation pools (the second encoder's validation split, BOM-30's held-out authors) are
left out of training; the Book of Mormon is in none of it. Card, written first:
``data/private/lab/owner/2026-11-21-voice-encoder/card.md``; settings ``lab.voice_encoder``.
Everything is written under ``data/corpus/lab/voice_encoder/`` (passage rows are licensed text in
another form; the tables hold ids and numbers). Evaluation: ``lab.voiceenc_eval``.

Usage::

    python -m lab.voiceenc pairs              # the pair table and check (1)
    python -m lab.voiceenc trial [--steps N]  # step 0: seconds per step on the Mac GPU
    python -m lab.voiceenc train              # the fine-tune; resumes from its checkpoint
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from lab.paths import out
from metadata import config

V2_WORKS = Path("data/style_embed/v2_works.parquet")
WORKS = Path("data/style_embed/works.parquet")
PASSAGES = Path("data/corpus/style_embed/v2")
REGISTRY = Path("data/lab/registry.parquet")
DUPES = Path("data/catalog/duplicates_combined.parquet")


def settings(cfg: dict) -> dict:
    return cfg["lab"]["voice_encoder"]


def home(cfg: dict) -> Path:
    return Path(settings(cfg)["out_dir"])


def held_out(author: str, prefixes: list[str]) -> bool:
    """True for an author whose catalog name begins with a held-out writer's name."""
    return any(author.startswith(p) for p in prefixes)


def title_alike(a: str, b: str, jmax: float) -> bool:
    """Two title keys that are the same book by the title rule: word Jaccard above ``jmax``, or
    one key's words all inside the other's."""
    x, y = set(a.split()), set(b.split())
    if not x or not y:
        return False
    if x <= y or y <= x:
        return True
    return len(x & y) / len(x | y) > jmax


def gram_hashes(rows: np.ndarray, n: int) -> np.ndarray:
    """(passages, positions) uint64 hashes of every ``n``-token run of each passage row."""
    r = rows.astype(np.uint64)
    k = r.shape[1] - n + 1
    h = np.zeros((r.shape[0], k), dtype=np.uint64)
    mult = np.uint64(1000003)
    with np.errstate(over="ignore"):
        for j in range(n):
            h = h * mult + r[:, j : j + k]
    return h


def shared_share(ha: np.ndarray, hb: np.ndarray) -> float:
    """Share of passages of A with at least one run found anywhere in B, and the reverse; the
    larger of the two."""
    ua, ub = np.unique(ha), np.unique(hb)
    a = np.isin(ha, ub).any(axis=1).mean()
    b = np.isin(hb, ua).any(axis=1).mean()
    return float(max(a, b))


def decade(year) -> int | None:
    return None if year is None else int(year) // 10 * 10


def work_table(cfg: dict) -> list[dict]:
    """One record per (author, work) of the second encoder's pool: split, register, year, decade,
    duplicate groups, passage rows; held-out writers and sealed works dropped."""
    v = settings(cfg)
    reg = pq.read_table(REGISTRY, columns=["work_id", "year", "sealed"]).to_pydict()
    year = dict(zip(reg["work_id"], reg["year"], strict=True))
    sealed = {w for w, s in zip(reg["work_id"], reg["sealed"], strict=True) if s}
    d = pq.read_table(DUPES, columns=["work_id", "group_id"]).to_pydict()
    group = dict(zip(d["work_id"], d["group_id"], strict=True))
    vols = {(r["author"], r["work"]): r["volumes"] for r in pq.read_table(WORKS).to_pylist()}
    idx = pq.read_table(PASSAGES / "passages.parquet", columns=["author", "work"]).to_pydict()
    rows: dict[tuple, list[int]] = defaultdict(list)
    for i, (a, w) in enumerate(zip(idx["author"], idx["work"], strict=True)):
        rows[a, w].append(i)
    res = []
    for r in pq.read_table(V2_WORKS).to_pylist():
        a, w = r["author"], r["work"]
        vs = vols.get((a, w), [])
        if held_out(a, v["held_out_writers"]) or any(x in sealed for x in vs):
            continue
        ys = [year[x] for x in vs if year.get(x) is not None]
        y = min(ys) if ys else None
        res.append({"author": a, "work": w, "split": r["split"], "genre": r["genre"],
                    "year": y, "decade": decade(y),
                    "groups": sorted({group[x] for x in vs if x in group}),
                    "rows": rows.get((a, w), [])})  # fmt: skip
    return res


def author_pairs(works: list[dict], data: np.ndarray, cfg: dict) -> tuple[list[dict], Counter]:
    """Every pair of one author's works with a full episode each, the rule each pair failed (or
    none), and counts. ``data`` is the passages memmap reshaped (rows, tokens)."""
    v = settings(cfg)
    per = cfg["style_embed"]["episode_passages"]
    bad = set(v["exclude_genres"])
    ok = [w for w in works if len(w["rows"]) >= per]
    hashes: dict[int, np.ndarray] = {}
    out_pairs, n = [], Counter()
    for i, j in combinations(range(len(ok)), 2):
        a, b = ok[i], ok[j]
        cross = a["genre"] != b["genre"] and a["genre"] not in bad and b["genre"] not in bad
        rule = None
        if set(a["groups"]) & set(b["groups"]):
            rule = "registry_duplicate_group"
        elif title_alike(a["work"], b["work"], v["title_jaccard_max"]):
            rule = "title"
        else:
            for k in (i, j):
                if k not in hashes:
                    hashes[k] = gram_hashes(data[np.array(ok[k]["rows"])], v["ngram"])
            share = shared_share(hashes[i], hashes[j])
            if share >= v["ngram_share_max"]:
                rule = "text_check"
        kind = "cross" if cross else "same"
        n[f"{kind}:{rule or 'kept'}"] += 1
        out_pairs.append({"author": a["author"], "split": a["split"], "w1": a["work"],
                          "w2": b["work"], "g1": a["genre"], "g2": b["genre"],
                          "d1": a["decade"], "d2": b["decade"], "cross": cross,
                          "rule": rule or "kept"})  # fmt: skip
    return out_pairs, n


def build_pairs(cfg: dict) -> dict:
    t0 = time.time()
    works = work_table(cfg)
    print(f"{len(works):,} works read in {time.time() - t0:.0f}s", flush=True)
    data = np.memmap(PASSAGES / "passages.bin", dtype=np.uint16, mode="r").reshape(
        -1, cfg["style_embed"]["passage_tokens"]
    )
    by: dict[str, list[dict]] = defaultdict(list)
    for w in works:
        by[w["author"]].append(w)
    pairs, counts = [], Counter()
    for k, (_a, ws) in enumerate(sorted(by.items()), 1):
        p, c = author_pairs(ws, data, cfg)
        pairs += p
        counts += c
        if k % 1000 == 0:
            print(f"  {k:,}/{len(by):,} authors, {len(pairs):,} pairs, "
                  f"{time.time() - t0:.0f}s", flush=True)  # fmt: skip
    d = home(cfg) / "pairs"
    keep = ["author", "work", "split", "genre", "year", "decade", "groups", "rows"]
    table = pa.Table.from_pylist([{k: w[k] for k in keep} for w in works])
    pq.write_table(table, out(d / "works.parquet"))
    pq.write_table(pa.Table.from_pylist(pairs), out(d / "pairs.parquet"))
    summary = summarise(pairs, counts, cfg)
    summary["works"] = len(works)
    summary["seconds"] = round(time.time() - t0)
    out(d / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def summarise(pairs: list[dict], counts: Counter, cfg: dict) -> dict:
    """Check (1): authors, pairs and registers per split, what each duplicate rule removed, the
    text check's share among pairs that passed the registry and title rules, a spot sample."""
    v = settings(cfg)
    rel = set(v["religious_genres"])
    kept = [p for p in pairs if p["cross"] and p["rule"] == "kept"]
    per_split = {}
    for s in ("train", "validation", "heldout"):
        ks = [p for p in kept if p["split"] == s]
        per_split[s] = {
            "authors_with_cross_pair": len({p["author"] for p in ks}),
            "cross_pairs": len(ks),
            "religious_pairs": sum((p["g1"] in rel) != (p["g2"] in rel) for p in ks),
            "authors_with_religious_pair": len(
                {p["author"] for p in ks if (p["g1"] in rel) != (p["g2"] in rel)}
            ),
            "register_pairs": dict(
                Counter("|".join(sorted((p["g1"], p["g2"]))) for p in ks).most_common()
            ),
        }
    cross_all = [p for p in pairs if p["cross"]]
    after_reg_title = [p for p in cross_all if p["rule"] in ("kept", "text_check")]
    flagged = sum(p["rule"] == "text_check" for p in after_reg_title)
    rng = random.Random(config.derive_seed(f"{v['seed']}:spot", cfg))
    spot = rng.sample(kept, min(v["spot_sample"], len(kept)))
    share = round(flagged / len(after_reg_title), 4) if after_reg_title else None
    train_auth = per_split["train"]["authors_with_cross_pair"]
    return {
        "exploratory": True,
        "counts_by_rule": dict(sorted(counts.items())),
        "cross_candidate_pairs": len(cross_all),
        "cross_removed": {
            r: sum(p["rule"] == r for p in cross_all)
            for r in ("registry_duplicate_group", "title", "text_check")
        },
        "text_check_share_after_registry_and_title": share,
        "per_split": per_split,
        "registers": sorted({p["g1"] for p in kept} | {p["g2"] for p in kept}),
        "check": {
            "train_authors": train_auth,
            "bar_train_authors": v["min_train_authors"],
            "text_flag_share": share,
            "bar_text_flag_share": v["max_text_flag_share"],
            "passed": train_auth >= v["min_train_authors"]
            and share is not None
            and share < v["max_text_flag_share"],
        },
        "spot_sample": [{k: p[k] for k in ("author", "w1", "w2", "g1", "g2")} for p in spot],
    }


class Draws:
    """Episodes for training and validation; a step's draw depends only on (seed, step)."""

    def __init__(self, cfg: dict, data: np.ndarray | None = None, d: Path | None = None):
        s, v = cfg["style_embed"], settings(cfg)
        d = d or home(cfg) / "pairs"
        self.p, self.v, self.cfg = s["episode_passages"], v, cfg
        if data is None:
            data = np.memmap(PASSAGES / "passages.bin", dtype=np.uint16, mode="r")
        self.data = data.reshape(-1, s["passage_tokens"])
        self.rows = {(w["author"], w["work"]): np.array(w["rows"])
                     for w in pq.read_table(d / "works.parquet").to_pylist()}  # fmt: skip
        pairs = [p for p in pq.read_table(d / "pairs.parquet").to_pylist() if p["rule"] == "kept"]
        self.pairs: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for p in pairs:
            self.pairs[p["split"]][p["author"]].append(p)
        # cells of the training split: (register A, register B, decade of A) -> {author: pairs}
        self.cells: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.loose: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for a, ps in self.pairs["train"].items():
            for p in ps:
                if not p["cross"]:
                    continue
                sides = ((p["g1"], p["w1"], p["d1"], p["g2"], p["w2"]),
                         (p["g2"], p["w2"], p["d2"], p["g1"], p["w1"]))  # fmt: skip
                for g1, w1, d1, g2, w2 in sides:
                    self.cells[g1, g2, d1][a].append((w1, w2))
                    self.loose[g1, g2, None][a].append((w1, w2))
        self.authors = sorted(self.pairs["train"])
        self.seed = config.derive_seed(v["seed"], cfg)

    def _episode(self, rng, a: str, w: str) -> np.ndarray:
        r = self.rows[a, w]
        return self.data[np.sort(rng.choice(r, self.p, replace=False))]

    def plan(self, step: int, n: int) -> tuple[str, list[tuple[str, str, str]]]:
        """(kind of step, [(author, first work, second work)]) for ``step``."""
        rng = np.random.default_rng([self.seed, step])
        v = self.v
        if rng.random() < v["cross_step_share"]:
            rel = set(v["religious_genres"])
            want_rel = rng.random() < v["religious_step_share"]
            for pool, kind in ((self.cells, "cross_decade"), (self.loose, "cross_any_decade")):
                keys = sorted((k for k, au in pool.items() if len(au) >= n
                               and (k[0] in rel) == want_rel), key=str)  # fmt: skip
                if keys:
                    sizes = np.array([len(pool[k]) for k in keys], dtype=float)
                    k = keys[rng.choice(len(keys), p=sizes / sizes.sum())]
                    au = sorted(pool[k])
                    chosen = rng.choice(len(au), size=n, replace=False)
                    picks = []
                    for i in chosen:
                        ws = pool[k][au[i]]
                        w1, w2 = ws[rng.integers(len(ws))]
                        picks.append((au[i], w1, w2))
                    return f"{kind}:{'religious' if want_rel else 'any'}", picks
        chosen = rng.choice(len(self.authors), size=min(n, len(self.authors)), replace=False)
        picks = []
        for i in chosen:
            ps = self.pairs["train"][self.authors[i]]
            p = ps[rng.integers(len(ps))]
            picks.append((p["author"], p["w1"], p["w2"]))
        return "random", picks

    def draw(self, step: int, n: int):
        import torch

        kind, picks = self.plan(step, n)
        rng = np.random.default_rng([self.seed, step, 9])
        eps = [self._episode(rng, a, w) for a, w1, w2 in picks for w in (w1, w2)]
        return kind, torch.from_numpy(np.stack(eps).astype(np.int64))

    def verification_set(self, split: str, n_auth: int, n_neg: int, salt: str) -> dict:
        """A fixed cross-register verification set from ``split``: per author one cross pair
        (episode A, episode B); false pairs are A against other authors' B-side episodes in the
        same register as the true B, same decade when at least ``n_neg`` such authors exist."""
        rng = np.random.default_rng(config.derive_seed(f"{self.v['seed']}:{salt}", self.cfg))
        auth = sorted(a for a, ps in self.pairs[split].items() if any(p["cross"] for p in ps))
        auth = [auth[i] for i in sorted(rng.choice(len(auth), min(n_auth, len(auth)), False))]
        rel = set(self.v["religious_genres"])
        items = []
        for a in auth:
            ps = [p for p in self.pairs[split][a] if p["cross"]]
            p = ps[rng.integers(len(ps))]
            items.append({"author": a, "wa": p["w1"], "ga": p["g1"], "da": p["d1"],
                          "wb": p["w2"], "gb": p["g2"], "db": p["d2"],
                          "religious": (p["g1"] in rel) != (p["g2"] in rel)})  # fmt: skip
        eps_a = [self._episode(rng, it["author"], it["wa"]) for it in items]
        eps_b = [self._episode(rng, it["author"], it["wb"]) for it in items]
        neg = []
        for i, it in enumerate(items):
            same = [j for j, o in enumerate(items) if j != i and o["gb"] == it["gb"]]
            near = [j for j in same if items[j]["db"] == it["db"]]
            pool = near if len(near) >= n_neg else same
            pick = rng.choice(pool, size=min(n_neg, len(pool)), replace=False) if pool else []
            neg.append([int(j) for j in pick])
        return {"items": items, "a": np.stack(eps_a), "b": np.stack(eps_b), "neg": neg}


def auc(pos: np.ndarray, neg: np.ndarray) -> float | None:
    if not len(pos) or not len(neg):
        return None
    from scipy.stats import rankdata

    r = rankdata(np.concatenate([pos, neg]))  # ties share their mean rank
    return float((r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def verification_scores(za: np.ndarray, zb: np.ndarray, neg: list[list[int]]) -> tuple:
    """Cosine of each true pair and of every false pair (A_i against B_j, j in ``neg[i]``)."""
    pos = (za * zb).sum(axis=1)
    negs = np.array([float(za[i] @ zb[j]) for i, js in enumerate(neg) for j in js])
    return pos, negs


def device():
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


def embed_episodes(enc, x: np.ndarray, dev: str, batch: int = 16) -> np.ndarray:
    """(episodes, passages, tokens) token arrays -> unit vectors, no gradient."""
    import torch

    enc.eval()
    res = []
    with torch.no_grad():
        for i in range(0, len(x), batch):
            t = torch.from_numpy(x[i : i + batch].astype(np.int64)).to(dev)
            res.append(enc(t).float().cpu().numpy())
    return np.concatenate(res)


def validate(enc, vs: dict, dev: str) -> dict:
    za, zb = embed_episodes(enc, vs["a"], dev), embed_episodes(enc, vs["b"], dev)
    pos, neg = verification_scores(za, zb, vs["neg"])
    sim = za @ zb.T
    top1 = float((sim.argmax(axis=1) == np.arange(len(za))).mean())
    return {"auc": round(auc(pos, neg), 4), "cross_top1": round(top1, 4)}


def lr_scale(step: int, v: dict) -> float:
    if step < v["warmup_steps"]:
        return (step + 1) / v["warmup_steps"]
    prog = min(1.0, (step - v["warmup_steps"]) / max(1, v["steps"] - v["warmup_steps"]))
    return v["min_lr_share"] + (1 - v["min_lr_share"]) * 0.5 * (1 + math.cos(math.pi * prog))


def _atomic_save(obj, path: Path) -> None:
    import torch

    tmp = path.with_suffix(".tmp")
    torch.save(obj, out(tmp))
    tmp.replace(path)


def train(cfg: dict, run: Path, max_steps: int | None, n_auth: int | None) -> dict:
    """The fine-tune. Resumes from ``run/checkpoint.pt``; a weights snapshot is kept at every
    validation (``step_XXXXX.pt``) and the best by validation AUC is copied to ``best.pt``;
    ``style.pt`` appears only when training ends."""
    import torch

    from style_embed.train import info_nce, load_encoder

    v, s, t = settings(cfg), cfg["style_embed"], cfg["timelocked_lm"]
    dev = device()
    torch.manual_seed(config.derive_seed(v["seed"], cfg))
    enc = load_encoder(Path(v["base"]), cfg).to(dev)
    enc.ckpt = True
    opt = torch.optim.AdamW([
        {"params": enc.backbone.parameters(), "lr": v["lr_encoder"], "base": v["lr_encoder"]},
        {"params": enc.head.parameters(), "lr": v["lr_head"], "base": v["lr_head"]}],
        weight_decay=s["weight_decay"])  # fmt: skip
    dr = Draws(cfg)
    vs = dr.verification_set("validation", v["validation_authors"], v["negatives_per_positive"],
                             "validation")  # fmt: skip
    run = Path(run)
    out(run / "x").parent.mkdir(parents=True, exist_ok=True)
    ck, step, best = run / "checkpoint.pt", 0, -1.0
    if ck.exists():
        st = torch.load(ck, map_location=dev)
        enc.load_state_dict(st["model"])
        opt.load_state_dict(st["optimizer"])
        step, best = st["step"], st["best"]
        print(f"resumed at step {step}", flush=True)
    steps = max_steps or v["steps"]
    n = n_auth or v["authors_per_step"]
    info = {**config.stamp(), "exploratory": True, "device": dev, "steps": steps,
            "authors_per_step": n, "precision": v["precision"], "base": v["base"],
            "train_authors": len(dr.authors), "validation_items": len(vs["items"])}  # fmt: skip
    out(run / "run.json").write_text(json.dumps(info, indent=1) + "\n")
    log = out(run / "log.jsonl").open("a")
    if step == 0:  # the starting weights' validation, for comparison
        rec = {"step": 0, **{f"validation_{k}": x for k, x in validate(enc, vs, dev).items()}}
        print(json.dumps(rec), flush=True)
        log.write(json.dumps(rec) + "\n")
        log.flush()
    amp = v["precision"] == "bf16" and dev != "cpu"
    last, t0 = time.time(), time.time()
    sched = {**v, "steps": steps}
    enc.train()
    while step < steps:
        for g in opt.param_groups:
            g["lr"] = g["base"] * lr_scale(step, sched)
        kind, x = dr.draw(step, n)
        x = x.to(dev)
        with torch.autocast(dev, dtype=torch.bfloat16, enabled=amp):
            loss = info_nce(enc(x), s["temperature"])
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(enc.parameters(), t["grad_clip"])
        opt.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        rec = {"step": step, "kind": kind, "loss": round(float(loss.detach()), 5),
               "sec": round(time.time() - t0, 1)}  # fmt: skip
        if step % v["validate_every"] == 0 or step == steps:
            val = validate(enc, vs, dev)
            enc.train()
            rec.update({f"validation_{k}": x for k, x in val.items()})
            _atomic_save(enc.state_dict(), run / f"step_{step:05d}.pt")
            if val["auc"] > best:
                best = val["auc"]
                rec["kept"] = True
                _atomic_save(enc.state_dict(), run / "best.pt")
            print(json.dumps(rec), flush=True)
        log.write(json.dumps(rec) + "\n")
        log.flush()
        if time.time() - last > v["checkpoint_minutes"] * 60 or step == steps:
            _atomic_save({"model": enc.state_dict(), "optimizer": opt.state_dict(),
                          "step": step, "best": best}, ck)  # fmt: skip
            last = time.time()
    if max_steps is None:
        import shutil

        shutil.copyfile(run / "best.pt", out(run / "style.tmp"))
        (run / "style.tmp").replace(run / "style.pt")
    return {"steps": step, "best_validation_auc": best}


def trial(cfg: dict, steps: int, n_auth: int | None) -> dict:
    """Step 0: ``steps`` training steps into ``trial/`` (its own folder, never resumed into the
    real run); seconds per step measured after the first ten."""
    v = settings(cfg)
    run = home(cfg) / f"trial_{n_auth or v['authors_per_step']}"
    t0 = time.time()
    train(cfg, run, steps, n_auth)
    recs = [json.loads(x) for x in (run / "log.jsonl").read_text().splitlines()]
    recs = [r for r in recs if "sec" in r][-steps:]
    secs = [b["sec"] - a["sec"] for a, b in zip(recs, recs[1:], strict=False)][10:]
    secs = [x for i, x in enumerate(secs) if "validation_auc" not in recs[i + 11]]
    per = float(np.median(secs)) if secs else None
    res = {
        "steps": steps,
        "authors_per_step": n_auth or v["authors_per_step"],
        "sec_per_step_median": round(per, 2) if per else None,
        "sec_per_step_mean": round(float(np.mean(secs)), 2) if secs else None,
        "wall_seconds": round(time.time() - t0),
        "projected_hours_for_config_steps": round(per * v["steps"] / 3600, 2) if per else None,
    }
    out(run / "trial.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["pairs", "trial", "train"])
    ap.add_argument(
        "--steps", type=int, help="trial: steps (default lab.voice_encoder.trial_steps)"
    )
    ap.add_argument("--authors", type=int, help="trial: authors per step (default the config's)")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "pairs":
        res = build_pairs(cfg)
        print(json.dumps({k: res[k] for k in ("cross_removed", "check")}, indent=1))
        for sp, r in res["per_split"].items():
            print(sp, {k: r[k] for k in r if k != "register_pairs"})
        return 0
    if a.cmd == "trial":
        print(json.dumps(trial(cfg, a.steps or settings(cfg)["trial_steps"], a.authors)))
        return 0
    print(json.dumps(train(cfg, home(cfg) / "run", None, None)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
