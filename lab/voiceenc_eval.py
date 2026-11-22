"""BOM-101 evaluation: the voice-trained encoder beside the study's two encoders (lab; exploratory).

Three measures, all three encoders on the same inputs (card:
``data/private/lab/owner/2026-11-21-voice-encoder/card.md``):

- ``six``: BOM-99's six writers exactly as ``lab.twovoices_enc`` measured the existing encoders
  (same chunks, one 8 x 128-token episode each, cosine): within-voice check, cross-voice
  attribution, gap index; plus the card's primary measure, the cross-voice macro rate, with a
  paired resampling interval (chunks drawn again within writer and voice, the same draws for all
  encoders). The existing encoders' chunk vectors are ``lab.twovoices_enc``'s own files.
- ``heldout``: cross-register author verification on BOM-30's held-out authors (never trained on
  by any of the three): AUC of true cross-register pairs against the same author's register-A
  episode paired with other authors' episodes in the true partner's register.
- ``nobody``: the "none of these" pairs of ``eval.nobody`` (200 known books, true author and 10
  others, closest episode), with the book's genre group from ``data/sweep/coverage.json``. The
  existing encoders' vectors are the sweep's (``episodes_gpu``: BOM-30's; ``episodes_v2``).

``report`` applies the card's rule and writes the result. The Book of Mormon is not read here;
the card allows an exploratory side-by-side only when the rule says the new encoder is better.

Usage::

    python -m lab.voiceenc_eval six        # Mac GPU, a few minutes
    python -m lab.voiceenc_eval heldout    # Mac GPU, about 15 minutes (three encoders)
    python -m lab.voiceenc_eval nobody     # Mac GPU, about 30 minutes (new encoder only)
    python -m lab.voiceenc_eval report     # -> data/lab/two_voices/result_voice_encoder.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from lab import twovoices as tv
from lab import twovoices_enc as te
from lab import voiceenc as ve
from lab.paths import out
from metadata import config

RESULT = tv.OUT / "result_voice_encoder.json"
COVERAGE = Path("data/sweep/coverage.json")
NOBODY_PAIRS = Path("data/corpus/nobody/pairs.json")
SWEEP_TAGS = {"bom30": "_gpu", "v2": "_v2"}  # the sweep's episode vectors per existing encoder
NEW = "voice"


def encoders(cfg: dict) -> dict[str, Path]:
    """Name -> weights: the two existing encoders and the new one."""
    paths = {k: Path(p) for k, p in cfg["lab"]["two_voices_enc"]["encoders"].items()}
    return {**paths, NEW: ve.home(cfg) / "run" / "style.pt"}


def evaldir(cfg: dict) -> Path:
    return ve.home(cfg) / "eval"


def _load(path: Path, cfg: dict):
    from style_embed.train import load_encoder

    if not path.exists():
        raise OSError(f"encoder weights missing: {path}")
    return load_encoder(path, cfg).to(ve.device())


# ---------------------------------------------------------------- six writers


def embed_six(cfg: dict) -> Path:
    """The new encoder's vector for every chunk of the six writers (``lab.twovoices_enc.embed``'s
    steps, written under this test's folder)."""
    from tokenizers import Tokenizer

    from sweep.index import episode_vectors
    from timelocked_lm.release import TOKENIZER

    t, s = cfg["lab"]["two_voices"], cfg["style_embed"]
    enc = _load(encoders(cfg)[NEW], cfg)
    vocab, _ = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    _, texts = tv.build_set(cfg, vocab)
    tok = Tokenizer.from_file(str(TOKENIZER))
    n, per = s["passage_tokens"], s["episode_passages"]
    arrays, short = {}, {}
    for w, by in texts.items():
        for v in tv.VOICES:
            vs, lens = [], []
            for ch in tv.chunks(by[v], t["chunk_words"]):
                ids = te.chunk_ids(tok.encode(" ".join(ch)).ids, n, per)
                lens.append(len(ids))
                vs.append(episode_vectors(enc, ids, n, per, ve.device())[0][0])
            arrays[f"{w}|{v}"] = np.stack(vs).astype(np.float32)
            short[f"{w}|{v}"] = sum(x < n * per for x in lens)
    p = out(evaldir(cfg) / f"six_{NEW}.npz")
    np.savez(p, _short=np.array(json.dumps(short)), **arrays)
    return p


def load_six(cfg: dict, name: str) -> dict:
    if name == NEW:
        p = evaldir(cfg) / f"six_{NEW}.npz"
        if not p.exists():
            raise OSError(f"{p} missing: run six")
        z = np.load(p)
        res: dict = {}
        for k in z.files:
            if k != "_short":
                w, v = k.split("|")
                res.setdefault(w, {})[v] = z[k].astype(np.float64)
        return res
    z = te.load_vectors(name)
    z.pop("_short", None)
    return z


def cross_macro(z: dict, cap: int, rng: np.random.Generator) -> tuple[float, dict]:
    """Nearest-centroid cross-voice attribution (cosine; centroids from at most ``cap`` chunks of
    the other voice, drawn by ``rng``), both directions; mean of the 12 own-writer rates."""
    names = sorted(z)
    rates = {}
    for src, dst in (("ordinary", "prophetic"), ("prophetic", "ordinary")):
        cents = []
        for w in names:
            arr = z[w][src]
            if len(arr) > cap:
                arr = arr[np.sort(rng.choice(len(arr), cap, replace=False))]
            c = arr.mean(axis=0)
            cents.append(c / np.linalg.norm(c))
        C = np.stack(cents)
        for i, w in enumerate(names):
            x = z[w][dst]
            x = x / np.linalg.norm(x, axis=1, keepdims=True)
            rates[f"{w}|{src}_to_{dst}"] = float((np.argmax(x @ C.T, axis=1) == i).mean())
    return float(np.mean(list(rates.values()))), rates


def paired_resamples(zs: dict[str, dict], cfg: dict) -> dict:
    """Cross-voice macro for each encoder over ``resamples`` paired draws of chunks (with
    replacement, within writer and voice; the same indices for every encoder)."""
    v, t = ve.settings(cfg), cfg["lab"]["two_voices"]
    rng = np.random.default_rng(config.derive_seed(f"{v['seed']}:resample", cfg))
    first = next(iter(zs.values()))
    names = sorted(first)
    draws = {e: [] for e in zs}
    unseen = {e: [] for e in zs}
    keep = [w for w in names if w not in ("joanna_southcott", "elias_smith")]
    for _ in range(v["resamples"]):
        idx = {(w, vv): rng.integers(0, len(first[w][vv]), len(first[w][vv]))
               for w in names for vv in tv.VOICES}  # fmt: skip
        cap_seed = int(rng.integers(2**31))
        for e, z in zs.items():
            zb = {w: {vv: z[w][vv][idx[w, vv]] for vv in tv.VOICES} for w in names}
            m, rates = cross_macro(zb, t["train_chunks"], np.random.default_rng(cap_seed))
            draws[e].append(m)
            unseen[e].append(float(np.mean([r for k, r in rates.items()
                                            if k.split("|")[0] in keep])))  # fmt: skip

    def q(x):
        return [round(float(np.percentile(x, p)), 4) for p in (2.5, 50, 97.5)]

    res = {"resamples": v["resamples"], "macro": {e: q(d) for e, d in draws.items()},
           "macro_four_unseen": {e: q(d) for e, d in unseen.items()}, "difference": {}}  # fmt: skip
    if NEW in zs:
        for e in zs:
            if e != NEW:
                res["difference"][f"{NEW}-{e}"] = q(np.array(draws[NEW]) - np.array(draws[e]))
                res["difference"][f"{NEW}-{e} (four unseen)"] = q(
                    np.array(unseen[NEW]) - np.array(unseen[e])
                )
    return res


def six(cfg: dict) -> dict:
    """All three encoders on the six writers; written to ``eval/six.json``."""
    t = cfg["lab"]["two_voices"]
    if not (evaldir(cfg) / f"six_{NEW}.npz").exists():
        embed_six(cfg)
    vocab, _ = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    the_set, _ = tv.build_set(cfg, vocab)
    groups = {w: r["group"] for w, r in the_set["writers"].items()}
    zs, res = {}, {"encoders": {}, "not_attempted": {}}
    for name in encoders(cfg):
        try:
            z = load_six(cfg, name)
        except OSError as e:
            res["not_attempted"][name] = str(e)
            continue
        zs[name] = {w: z[w] for w in groups}
    counts = {e: {w: {v: len(z[w][v]) for v in tv.VOICES} for w in z} for e, z in zs.items()}
    if len({json.dumps(c, sort_keys=True) for c in counts.values()}) != 1:
        raise SystemExit(f"chunk counts differ between encoders: {counts}")
    for name, z in zs.items():
        r = te.score(z, groups, cfg)
        cv = r.get("cross_voice")
        if cv:
            rates = [cv[k][w]["rate"] for k in ("ordinary_to_prophetic", "prophetic_to_ordinary")
                     for w in groups]  # fmt: skip
            r["cross_voice_macro"] = round(float(np.mean(rates)), 4)
        res["encoders"][name] = r
    res["paired"] = paired_resamples(zs, cfg)
    out(evaldir(cfg) / "six.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


# ---------------------------------------------------------------- held-out library authors


def heldout(cfg: dict) -> dict:
    """Cross-register verification on BOM-30's held-out authors, all three encoders, the same
    episodes; written to ``eval/heldout.json`` (ids and numbers)."""
    v = ve.settings(cfg)
    dr = ve.Draws(cfg)
    vs = dr.verification_set("heldout", v["test_authors"], v["negatives_per_positive"], "test")
    items = vs["items"]
    rel = np.array([it["religious"] for it in items])
    res = {"items": len(items), "religious_items": int(rel.sum()), "encoders": {},
           "not_attempted": {}}  # fmt: skip
    scores = {}
    for name, path in encoders(cfg).items():
        try:
            enc = _load(path, cfg)
        except OSError as e:
            res["not_attempted"][name] = str(e)
            continue
        za = ve.embed_episodes(enc, vs["a"], ve.device())
        zb = ve.embed_episodes(enc, vs["b"], ve.device())
        scores[name] = (za, zb)
        del enc
    rng = np.random.default_rng(config.derive_seed(f"{v['seed']}:heldout-boot", cfg))
    boots = [rng.integers(0, len(items), len(items)) for _ in range(v["resamples"])]
    per_boot = {}
    for name, (za, zb) in scores.items():
        row = {}
        for label, keep in (("all", np.ones(len(items), bool)), ("religious", rel),
                            ("not_religious", ~rel)):  # fmt: skip
            ii = np.flatnonzero(keep)
            pos = (za[ii] * zb[ii]).sum(axis=1)
            neg = np.array([float(za[i] @ zb[j]) for i in ii for j in vs["neg"][i]])
            a = ve.auc(pos, neg)
            row[label] = {"true_pairs": len(pos), "false_pairs": len(neg),
                          "auc": None if a is None else round(a, 4)}  # fmt: skip
        sim = za @ zb.T
        row["cross_top1"] = round(float((sim.argmax(axis=1) == np.arange(len(za))).mean()), 4)
        res["encoders"][name] = row
        pb = []
        for bi in boots:
            pos = (za[bi] * zb[bi]).sum(axis=1)
            neg = np.array([float(za[i] @ zb[j]) for i in bi for j in vs["neg"][i]])
            pb.append(ve.auc(pos, neg))
        per_boot[name] = np.array(pb)
    if NEW in per_boot:
        res["auc_difference_by_author_resampling"] = {
            f"{NEW}-{e}": [round(float(np.percentile(per_boot[NEW] - per_boot[e], p)), 4)
                           for p in (2.5, 50, 97.5)]
            for e in per_boot if e != NEW
        }  # fmt: skip
    out(evaldir(cfg) / "heldout.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


# ---------------------------------------------------------------- "none of these"


def embed_nobody(cfg: dict) -> Path:
    """The new encoder's episode vectors of the 400 units the ``eval.nobody`` pairs use."""
    from tokenizers import Tokenizer

    from sweep.index import _read, episode_vectors
    from timelocked_lm.release import TOKENIZER

    s = cfg["style_embed"]
    pairs = json.loads(NOBODY_PAIRS.read_text())
    units = sorted({f"calib_profile:{p['candidate']}" for p in pairs}
                   | {f"calib_query:{p['book']}:0" for p in pairs})  # fmt: skip
    enc = _load(encoders(cfg)[NEW], cfg)
    tok = Tokenizer.from_file(str(TOKENIZER))
    vs = [episode_vectors(enc, tok.encode(" ".join(_read(u))).ids, s["passage_tokens"],
                          s["episode_passages"], ve.device())[0] for u in units]  # fmt: skip
    p = out(evaldir(cfg) / f"nobody_{NEW}.npz")
    np.savez(p, units=np.array(units), counts=np.array([len(v) for v in vs]),
             V=np.concatenate(vs))  # fmt: skip
    return p


def _nobody_eps(cfg: dict, name: str) -> dict:
    if name == NEW:
        p = evaldir(cfg) / f"nobody_{NEW}.npz"
        if not p.exists():
            raise OSError(f"{p} missing")
        z = np.load(p)
        cuts = np.cumsum(z["counts"])[:-1]
        vs = np.split(z["V"], cuts)
        return {u: v.astype(np.float32) for u, v in zip(z["units"].tolist(), vs, strict=True)}
    from sweep.episodes import load

    eps, _ = load(SWEEP_TAGS[name])
    if not eps:
        raise OSError(f"no sweep episode vectors for {name}")
    return eps


def nobody(cfg: dict) -> dict:
    """``eval.nobody``'s verifier for each encoder, all books and by genre group."""
    from eval.nobody import verifier
    from sweep.episodes import padded, topk_scores

    if not (evaldir(cfg) / f"nobody_{NEW}.npz").exists():
        embed_nobody(cfg)
    pairs = json.loads(NOBODY_PAIRS.read_text())
    group = {r["author"]: r["genre"] for r in json.loads(COVERAGE.read_text())["records"]}
    res = {"pairs": len(pairs), "encoders": {}, "not_attempted": {}}
    for name in encoders(cfg):
        try:
            eps = _nobody_eps(cfg, name)
        except OSError as e:
            res["not_attempted"][name] = str(e)
            continue
        v, t, g = [], [], []
        for book in sorted({p["book"] for p in pairs}):
            cands = [p for p in pairs if p["book"] == book]
            G, M = padded([eps[f"calib_profile:{p['candidate']}"] for p in cands])
            s = topk_scores(eps[f"calib_query:{book}:0"], G, M, [1])[1]
            v += s.tolist()
            t += [p["target"] for p in cands]
            g += [group.get(book, "unknown")] * len(cands)
        v, t, g = np.array(v), np.array(t), np.array(g)
        row = {"all": verifier(v[t], v[~t])}
        for gg in sorted(set(g)):
            k = g == gg
            if (t & k).any():
                row[f"genre_{gg}"] = verifier(v[t & k], v[~t & k])
        res["encoders"][name] = row
    out(evaldir(cfg) / "nobody.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


# ---------------------------------------------------------------- the rule and the report


def verdict(six_res: dict, held: dict | None, cfg: dict) -> dict:
    """The card's rule: (A) cross-voice macro above both existing encoders, the paired
    difference's 2.5th percentile above 0; (B) within-voice macro at least the bar in each voice
    and not below the better existing encoder's by more than the tolerance; (C) held-out AUC not
    below the second encoder's. Yes / cannot tell / no."""
    v = ve.settings(cfg)
    enc = six_res["encoders"]
    if NEW not in enc or "cross_voice_macro" not in enc[NEW]:
        return {"answer": "not attempted", "why": "the new encoder was not scored"}
    olds = [e for e in enc if e != NEW]
    diff = six_res["paired"]["difference"]
    a_point = all(enc[NEW]["cross_voice_macro"] > enc[e]["cross_voice_macro"] for e in olds)
    a_int = all(diff[f"{NEW}-{e}"][0] > 0 for e in olds)
    ka = {e: {vv: enc[e]["known_answer"]["cosine"][vv]["macro"] for vv in tv.VOICES} for e in enc}
    bar = cfg["lab"]["two_voices"]["known_bar"]
    b = all(ka[NEW][vv] >= bar and ka[NEW][vv] >= max(ka[e][vv] for e in olds)
            - v["within_voice_tolerance"] for vv in tv.VOICES)  # fmt: skip
    c = None
    if held and NEW in held["encoders"] and "v2" in held["encoders"]:
        c = held["encoders"][NEW]["all"]["auc"] >= held["encoders"]["v2"]["all"]["auc"]
    if a_point and a_int and b and c:
        answer = "yes"
    elif a_point and not a_int and b and c is not False:
        answer = "cannot tell"
    else:
        answer = "no"
    return {"answer": answer, "A_point_above_both": a_point, "A_interval_above_both": a_int,
            "B_within_voice_not_worse": b, "C_heldout_auc_not_below_v2": c,
            "within_voice": ka}  # fmt: skip


def _read(p: Path):
    try:
        return json.loads(p.read_text())
    except OSError:
        return None


def report(cfg: dict) -> dict:
    d = evaldir(cfg)
    home = ve.home(cfg)
    six_res, held, nob = _read(d / "six.json"), _read(d / "heldout.json"), _read(d / "nobody.json")
    res = {
        "exploratory": True,
        "issue": "BOM-101",
        "card": "data/private/lab/owner/2026-11-21-voice-encoder/card.md",
        "settings": ve.settings(cfg),
        "encoders": {k: str(p) for k, p in encoders(cfg).items()},
        "pairs": _read(home / "pairs" / "summary.json"),
        "trial": {p.parent.name: _read(p) for p in sorted(home.glob("trial_*/trial.json"))},
        "training": _read(home / "run" / "run.json"),
        "training_log_validations": [
            json.loads(x)
            for x in (
                (home / "run" / "log.jsonl").read_text().splitlines()
                if (home / "run" / "log.jsonl").exists()
                else []
            )
            if "validation_auc" in x
        ],  # fmt: skip
        "six_writers": six_res,
        "heldout_verification": held,
        "none_of_these": nob,
        "not_run": {
            "727_known_books_cross_genre_row": "needs every swept unit re-embedded with the new "
            "encoder (sweep.index episodes: about 23 h on the Mac GPU, under 1 h on an H100); "
            "the card runs it only if the rule says better and the owner wants it",
        },
        "training_overlap": "the six writers and both evaluation pools are out of the new "
        "training; the starting weights are the second encoder's, which trained on Southcott "
        "and Elias Smith",
    }
    if six_res:
        res["verdict"] = verdict(six_res, held, cfg)
        res["book_of_mormon"] = (
            "not read or scored: the card scores it only when the rule says better"
            if res["verdict"]["answer"] != "yes"
            else "allowed by the card as an exploratory side-by-side; not yet run"
        )
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                   text=True).stdout.strip()  # fmt: skip
    out(RESULT).write_text(json.dumps(res, indent=1) + "\n")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["six", "heldout", "nobody", "report"])
    a = ap.parse_args(argv)
    cfg = config.load()
    res = {"six": six, "heldout": heldout, "nobody": nobody, "report": report}[a.cmd](cfg)
    if a.cmd == "six":
        for e, r in res["encoders"].items():
            print(e, r.get("cross_voice_macro"),
                  {vv: r["known_answer"]["cosine"][vv]["macro"] for vv in tv.VOICES})  # fmt: skip
        print(json.dumps(res["paired"], indent=1))
    elif a.cmd == "report":
        print(json.dumps(res.get("verdict"), indent=1), "->", RESULT)
    else:
        print(json.dumps(res["encoders"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
