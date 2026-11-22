"""BOM-104, second attempt (post hoc): bigger samples, and the check scored before any target.

The first attempt (``lab.dictations``; ``data/lab/dictations/result.json``) missed its
known-answer check on every measure. This one, written after that miss and before anything else
was looked at, enlarges the candidates' known writing with text already on disk (Joseph Smith's
later letters; Sidney Rigdon's 1833-35 "Millennium" and "Gospel" series, attributed to him by the
sidneyrigdon.com editor), gives every candidate 20 training and 10 test chunks (a candidate who
cannot reach both is dropped), and runs in two passes: the check pass measures the candidates'
chunks only; the target pass (the Lectures, the dictated texts, the Book of Mormon) runs only for
measures that passed. Measures, word form, targets and bars are the first attempt's. The Book of
Mormon is scored only, never trained or tuned on. Card, written first:
``data/private/lab/owner/2026-11-21-other-dictations-2/card.md``; settings ``lab.dictations.v2``
(over ``lab.dictations``). Working files in ``data/corpus/lab/dictations/v2/``; the result holds
ids and numbers, no text.

Usage::

    python -m lab.dictations_v2 plan                     # candidates' words and chunks (seconds)
    python -m lab.dictations_v2 embed --stage check      # Mac GPU: candidate chunks, both encoders
    python -m lab.dictations_v2 train                    # Mac GPU: author models, check units only
    python -m lab.dictations_v2 check                    # -> data/lab/dictations/result_v2.json
    python -m lab.dictations_v2 embed --stage target     # Mac GPU: targets, passing encoders only
    python -m lab.dictations_v2 score                    # Mac GPU: targets, if both doses passed
    python -m lab.dictations_v2 run                      # -> data/lab/dictations/result_v2.json
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import time
from pathlib import Path

import numpy as np

from lab import dictations as dc
from lab import twovoices as tv
from lab.paths import out
from metadata import config

OUT = dc.OUT / "result_v2.json"
WORK = dc.WORK / "v2"
RIGDON = Path("data/private/lab/sources/rigdon")
T73 = Path("data/private/candidates")
FW = "function_words_burrows", "function_words_cosine"


def settings(cfg: dict) -> dict:
    t = {k: v for k, v in cfg["lab"]["dictations"].items() if k != "v2"}
    return {**t, **cfg["lab"]["dictations"]["v2"]}


# ------------------------------------------------------------------------------ texts


def series_text(raw: str) -> str:
    """The card's rule for the sidneyrigdon.com pages: text inside ``<blockquote>`` only (the
    editor's introductions and notes lie outside); mastheads (``<center>``) and centred headings
    removed, then tags; square- and curly-bracketed matter and "TO BE CONTINUED" removed."""
    parts = re.findall(r"(?is)<blockquote>(.*?)</blockquote>", raw)
    res = []
    for p in parts:
        p = re.sub(r"(?is)<center>.*?</center>", " ", p)
        p = re.sub(r"(?is)<p\s+align=center>.*?</p>", " ", p)
        p = re.sub(r"(?is)<small>(\w+)</small>", r"\1", p)  # small capitals inside a word
        p = html.unescape(re.sub(r"<[^>]+>", " ", p))
        p = re.sub(r"\[[^\]]*\]|\{[^}]*\}", " ", p)
        res.append(re.sub(r"TO BE CONTINUED\.?", " ", p))
    return "\n".join(res)


def smith_letters(kinds: list[str]) -> list[Path]:
    return sorted(f for k in kinds for f in T73.glob(f"t73-{k}*.jsonl"))


def candidate_streams(cfg: dict, vocab: set[str], grams: set[str]) -> tuple[dict, dict]:
    """The first attempt's streams, enlarged by the card's rule. Smith's new letters follow his
    first-attempt stream (so its start, and the cached models, are unchanged); Rigdon's series
    come first (date order)."""
    t = settings(cfg)
    toks, rec = dc.candidate_tokens(cfg, vocab, grams)
    files = smith_letters(t["smith_t73_kinds"])
    text = "\n".join(dc.strip_editorial("\n".join(r["text"] for r in dc._pages(f))) for f in files)
    add = dc.masked(text, vocab, grams)
    toks["joseph_smith"] = toks["joseph_smith"] + add
    rec["joseph_smith"]["added"] = {"files": [f.name for f in files], "words_masked": len(add)}
    raw = "\n".join(
        series_text((RIGDON / f).read_text(encoding="latin-1")) for f in t["rigdon_series"]
    )
    add = dc.masked(raw, vocab, grams)
    toks["sidney_rigdon"] = add + toks["sidney_rigdon"]
    rec["sidney_rigdon"]["added_before"] = {
        "files": t["rigdon_series"],
        "words_masked": len(add),
        "attribution": "the sidneyrigdon.com editor's; the articles are unsigned",
    }
    grams = scripture_grams(cfg, vocab, grams, t["quote_ngram"])
    for c in toks:
        before = len(toks[c])
        toks[c] = tv.drop_kjv(toks[c], grams, t["quote_ngram"])
        rec[c]["scripture_quote_tokens_dropped"] = before - len(toks[c])
        rec[c]["words_masked"] = len(toks[c])
    return toks, rec


def scripture_grams(cfg: dict, vocab: set[str], kjv: set[str], n: int) -> set[str]:
    """Word ``n``-grams of the King James-masked scripture targets (Book of Mormon, the
    revelations used here, Moses, Abraham): only the n-gram set is built, nothing measured."""
    groups, _ = dc.dictated(cfg, vocab, kjv)
    res: set[str] = set()
    for toks in [*groups.values(), dc.bom_tokens(vocab, kjv)]:
        res.update(" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1))
    return res


def build(cfg: dict, targets: bool) -> dict:
    """Candidates' train and test items always; target items only when ``targets``."""
    t, size = settings(cfg), cfg["lab"]["two_voices"]["chunk_words"]
    vocab, grams = tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
    streams, rec = candidate_streams(cfg, vocab, grams)
    need = t["train_chunks"] + t["test_chunks"]
    items: dict[str, list[str]] = {}
    meta: dict = {"candidates": {}, "dropped": {}, "lectures": {}, "groups": {},
                  "not_attempted": {}}  # fmt: skip
    rng = random.Random(t["seed"])
    cands = []
    for c in t["candidates"]:
        ch = tv.chunks(streams[c], size)
        if len(ch) < need:
            meta["dropped"][c] = (
                f"{len(ch)} masked chunks, under {need} "
                f"({t['train_chunks']} training + {t['test_chunks']} test)"
            )
            continue
        cands.append(c)
        held = ch[t["train_chunks"] :]
        pick = sorted(rng.sample(range(len(held)), t["test_chunks"]))
        for i in range(t["train_chunks"]):
            items[f"cand|{c}|train|{i}"] = ch[i]
        for j, i in enumerate(pick):
            items[f"cand|{c}|test|{j}"] = held[i]
        meta["candidates"][c] = {
            **rec[c],
            "chunks": len(ch),
            "test_chunk_index": [t["train_chunks"] + i for i in pick],
        }
    b = {"items": items, "whole": {}, "meta": meta, "cands": cands,
         "train_tokens_stream": {c: streams[c] for c in cands}}  # fmt: skip
    if targets:
        add_targets(cfg, b, vocab, grams)
    return b


def add_targets(cfg: dict, b: dict, vocab: set[str], grams: set[str]) -> None:
    """The first attempt's targets, cut the same way (``lab.dictations.build``)."""
    t, size = settings(cfg), cfg["lab"]["two_voices"]["chunk_words"]
    items, meta = b["items"], b["meta"]
    try:
        for n, d in dc.lectures(cfg, vocab, grams).items():
            ps = dc.pieces(d["body"], size, t["min_piece_words"])
            for i, p in enumerate(ps):
                items[f"lec|{n}|{i}"] = p
            b["whole"][f"lecw|{n}"] = d["body"]
            for i, p in enumerate(dc.pieces(d["qa"], size, t["min_piece_words"])):
                items[f"qa|{n}|{i}"] = p
            meta["lectures"][n] = {"body_words_masked": len(d["body"]), "pieces": len(ps),
                                   "qa_words_masked": len(d["qa"])}  # fmt: skip
    except OSError as e:
        meta["not_attempted"]["lectures"] = str(e)
    try:
        groups, grec = dc.dictated(cfg, vocab, grams)
        for g, x in groups.items():
            ch = tv.chunks(x, size)
            for i, c in enumerate(ch):
                items[f"grp|{g}|{i}"] = c
            meta["groups"][g] = {**grec[g], "words_masked": len(x), "chunks": len(ch)}
    except OSError as e:
        meta["not_attempted"]["dictated"] = str(e)
    try:
        for i, c in enumerate(tv.chunks(dc.bom_tokens(vocab, grams), size)):
            items[f"bom|{i}"] = c
        meta["book_of_mormon"] = {"chunks": sum(k.startswith("bom|") for k in items),
                                  "use": "scored only; never trained or tuned"}  # fmt: skip
    except OSError as e:
        meta["not_attempted"]["book_of_mormon"] = str(e)


# ------------------------------------------------------------------------------ function words


def fw_vectors(cfg: dict, b: dict) -> tuple[dict, dict]:
    vecs, info = dc.fw_vectors(cfg, b)
    info.pop("_z", None)
    return vecs, info


# ------------------------------------------------------------------------------ encoders


def embed(cfg: dict, name: str, stage: str) -> None:
    """Encoder vectors of the candidates' chunks (check) or of the targets (target)."""
    import torch
    from tokenizers import Tokenizer

    from lab.twovoices_enc import chunk_ids
    from style_embed.train import load_encoder
    from sweep.index import episode_vectors
    from timelocked_lm.release import TOKENIZER

    s = cfg["style_embed"]
    path = Path(cfg["lab"]["two_voices_enc"]["encoders"][name])
    if not path.exists():
        raise OSError(f"encoder weights missing: {path}")
    b = build(cfg, targets=stage == "target")
    keys = sorted(k for k in b["items"] if (k.startswith("cand|")) == (stage == "check"))
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    enc = load_encoder(path, cfg).to(dev)
    tok = Tokenizer.from_file(str(TOKENIZER))
    n, per = s["passage_tokens"], s["episode_passages"]
    arr = [episode_vectors(enc, chunk_ids(tok.encode(" ".join(b["items"][k])).ids, n, per),
                           n, per, dev)[0][0] for k in keys]  # fmt: skip
    p = out(WORK / f"vectors_{name}_{stage}.tmp.npz")
    np.savez(p, keys=np.array(keys), vecs=np.stack(arr).astype(np.float32))
    p.replace(WORK / f"vectors_{name}_{stage}.npz")
    print(f"{name} {stage}: {len(keys)} items on {dev}", flush=True)


def enc_vectors(name: str, b: dict, stages: tuple[str, ...]) -> dict:
    vecs: dict = {}
    for stage in stages:
        p = WORK / f"vectors_{name}_{stage}.npz"
        if not p.exists():
            raise OSError(f"{p} missing: run embed --stage {stage}")
        z = np.load(p)
        vecs.update(
            {str(k): v.astype(np.float64) for k, v in zip(z["keys"], z["vecs"], strict=True)}
        )
    want = {k for k in b["items"] if "target" in stages or k.startswith("cand|")}
    if set(vecs) != want:
        raise OSError(f"vectors for {name} were built from other items: embed again")
    for w in b["whole"]:
        n = w.split("|")[1]
        ps = [v for k, v in vecs.items() if k.startswith(f"lec|{n}|")]
        if ps:
            vecs[w] = np.mean(ps, axis=0)
    return vecs


# ------------------------------------------------------------------------------ author models


def _ids(b: dict, keys: list[str]) -> list[list[int]]:
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    tok = Tokenizer.from_file(str(TOKENIZER))
    allw = {**b["items"], **b["whole"]}
    return [tok.encode(" ".join(allw[k])).ids for k in keys]


def _digest(keys: list[str], ids: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps([keys, ids]).encode()).hexdigest()


def train_ids(cfg: dict, b: dict) -> tuple[dict, dict]:
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    t, seq = settings(cfg), cfg["alm"]["seq"]
    size = cfg["lab"]["two_voices"]["chunk_words"]
    tok = Tokenizer.from_file(str(TOKENIZER))
    res, short = {}, {}
    for c, words in b["train_tokens_stream"].items():
        enc = tok.encode(" ".join(words))
        limit = len(" ".join(words[: t["train_chunks"] * size]))
        for dose, s in t["doses"].items():
            n = s * seq
            if len(enc.ids) < n or enc.offsets[n - 1][1] > limit:
                short[f"{dose}|{c}"] = "training slice longer than the training part"
                continue
            res[f"{dose}|{c}"] = enc.ids[:n]
    return res, short


def _scorer(model, cfg: dict, dev: str):
    from alm.benchmark import window_losses
    from lab.dictations_alm import SCORE_ROWS

    def score(tests):
        got = window_losses(model, tests, cfg["alm"]["score_window"], dev, rows=SCORE_ROWS)
        return np.array([np.mean(w) if w else np.nan for w in got], dtype=np.float64)

    return score


def smith_same(cfg: dict, ids: list[int]) -> bool:
    """True when Smith's training ids equal the first attempt's (the two-voices slice), so the
    cached two-voices model was trained on exactly these tokens."""
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    vocab, kjv = tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
    first, _ = dc.candidate_tokens(cfg, vocab, kjv)
    tok = Tokenizer.from_file(str(TOKENIZER))
    return tok.encode(" ".join(first["joseph_smith"])).ids[: len(ids)] == list(ids)


def train(cfg: dict) -> int:
    """Check pass: fine-tune (or reuse) every candidate's model at each dose, keep the weights,
    and score the candidates' held-out chunks only. Resumes per model."""
    import torch

    from alm.benchmark import _base, _device, finetune
    from lab.dictations_alm import MICRO, _cached, _sha
    from lab.twovoices_alm import free

    a, t = cfg["alm"], settings(cfg)
    lr = cfg["timelocked_lm"]["finetune_lr"]
    b = build(cfg, targets=False)
    tr, short = train_ids(cfg, b)
    keys = sorted(k for k in b["items"] if "|test|" in k)
    tests = _ids(b, keys)
    work = WORK / "alm"
    meta = {"keys": keys, "digest": _digest(keys, tests), "not_attempted": short}
    old = work / "check_items.json"
    if old.exists() and json.loads(old.read_text())["digest"] != meta["digest"]:
        raise SystemExit(f"{old}: the check units changed; move {work} aside (never delete)")
    out(old).write_text(json.dumps(meta))
    dev = _device()
    model = _base(t["size"], cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    score = _scorer(model, cfg, dev)
    t0 = time.time()
    if not (work / "check_base.npy").exists():
        np.save(out(work / "check_base.tmp.npy"), score(tests))
        (work / "check_base.tmp.npy").replace(work / "check_base.npy")
    for key, ids in sorted(tr.items()):
        dose, c = key.split("|")
        name = f"{dose}__{c}"
        if (work / f"{name}.json").exists():
            continue
        t1 = time.time()
        model.load_state_dict(state)
        cached = _cached(dose, cfg) if c == "joseph_smith" and smith_same(cfg, ids) else None
        if cached:
            wpath = cached[0]
            model.load_state_dict(torch.load(wpath, map_location="cpu"))
            info = {"reused": str(wpath), "steps": cached[1].get("steps"),
                    "seed": cached[1].get("seed")}  # fmt: skip
        else:
            seed = config.derive_seed(f"{a['train_seed']}:{t['seed']}:v2:{key}", cfg)
            torch.manual_seed(seed)
            info = finetune(model, np.array(ids, dtype=np.int32), cfg, seed, MICRO, dev, lr)
            info["seed"] = seed
            wpath = work / f"{name}.pt"
            torch.save({x: v.cpu() for x, v in model.state_dict().items()},
                       out(work / f"{name}.pt.tmp"))  # fmt: skip
            (work / f"{name}.pt.tmp").replace(wpath)
        free(dev)
        np.save(out(work / f"{name}.check.tmp.npy"), score(tests))
        (work / f"{name}.check.tmp.npy").replace(work / f"{name}.check.npy")
        rec = {"train_tokens": len(ids), **info, "lr": lr, "weights": str(wpath),
               "weights_sha256": _sha(wpath), "digest": meta["digest"],
               "sec": round(time.time() - t1, 1)}  # fmt: skip
        out(work / f"{name}.json").write_text(json.dumps(rec))  # written last: the done mark
        print(f"  {name}: {time.time() - t1:.0f} s (total {(time.time() - t0) / 60:.1f} min)",
              flush=True)  # fmt: skip
    return 0


def alm_scores(cfg: dict, b: dict, stage: str) -> dict:
    """{dose: {unit: {candidate: model loss minus base}}} for the check or target units."""
    work, t = WORK / "alm", settings(cfg)
    meta_f = work / f"{stage}_items.json"
    if not meta_f.exists():
        raise OSError(f"{meta_f} missing: run {'train' if stage == 'check' else 'score'}")
    keys = json.loads(meta_f.read_text())["keys"]
    base = np.load(work / f"{stage}_base.npy")
    res = {}
    for dose in t["doses"]:
        cols = {}
        for c in b["cands"]:
            f = work / f"{dose}__{c}.{stage}.npy"
            if not f.exists():
                raise OSError(f"{f} missing")
            cols[c] = np.load(f) - base
        sc = {k: {c: float(cols[c][i]) for c in b["cands"]} for i, k in enumerate(keys)}
        res[dose] = {k: v for k, v in sc.items() if not any(np.isnan(x) for x in v.values())}
    return res


def alm_check(cfg: dict, b: dict) -> dict:
    t = settings(cfg)
    s = alm_scores(cfg, b, "check")
    doses = {
        d: {
            "train_tokens": t["doses"][d] * cfg["alm"]["seq"],
            "known_answer": dc.known_answer(x, b["cands"], t),
        }
        for d, x in s.items()
    }
    passed = [d for d, r in doses.items() if r["known_answer"]["passed"]]
    both = len(passed) == len(t["doses"])
    models = {}
    for d in t["doses"]:
        for c in b["cands"]:
            j = json.loads((WORK / "alm" / f"{d}__{c}.json").read_text())
            models[f"{d}|{c}"] = {k: j.get(k) for k in ("train_tokens", "steps", "seed",
                                                         "reused")}  # fmt: skip
    return {"doses": doses, "models": models, "passed_both": both,
            "known_answer": {"passed": both, "passed_doses": passed}}  # fmt: skip


def score_targets(cfg: dict) -> int:
    """Target pass for the author models: refused unless both doses passed the check."""
    import torch

    from alm.benchmark import _base, _device

    t = settings(cfg)
    b = build(cfg, targets=True)
    chk = alm_check(cfg, b)
    if not chk["passed_both"]:
        raise SystemExit("the author models missed the check at a dose: targets not scored")
    keys = sorted([k for k in b["items"] if not k.startswith("cand|")] + list(b["whole"]))
    tests = _ids(b, keys)
    work = WORK / "alm"
    out(work / "target_items.json").write_text(
        json.dumps({"keys": keys, "digest": _digest(keys, tests)})
    )
    dev = _device()
    model = _base(t["size"], cfg).to(dev).eval()
    score = _scorer(model, cfg, dev)
    if not (work / "target_base.npy").exists():
        np.save(out(work / "target_base.tmp.npy"), score(tests))
        (work / "target_base.tmp.npy").replace(work / "target_base.npy")
    for d in t["doses"]:
        for c in b["cands"]:
            f = work / f"{d}__{c}.target.npy"
            if f.exists():
                continue
            j = json.loads((work / f"{d}__{c}.json").read_text())
            model.load_state_dict(torch.load(j["weights"], map_location="cpu"))
            np.save(out(work / f"{d}__{c}.target.tmp.npy"), score(tests))
            (work / f"{d}__{c}.target.tmp.npy").replace(f)
            print(f"  {d} {c} targets scored", flush=True)
    return 0


def alm_targets(cfg: dict, b: dict, chk: dict) -> dict:
    t = settings(cfg)
    cands, groups = b["cands"], list(b["meta"]["groups"])
    s = alm_scores(cfg, b, "target")
    res = dict(chk)
    for d, sc in s.items():
        r = res["doses"][d]
        r["lectures"] = dc.lecture_table(sc, cands, sc.keys())
        r["chunk_nearest_candidate"] = dc.group_votes(sc, groups, cands)
    lec = {}
    for n in map(str, range(1, 8)):
        w = {d: res["doses"][d]["lectures"].get(n, {}).get("winner") for d in t["doses"]}
        same = len(set(w.values())) == 1 and None not in w.values()
        lec[n] = {"by_dose": w, "both_doses": next(iter(w.values())) if same else "no answer"}
    res["lectures"] = lec
    agree = {}
    for g in [*groups, "book_of_mormon", "lectures_pooled"]:
        tops = {}
        for d in t["doses"]:
            v = res["doses"][d]["chunk_nearest_candidate"].get(g, {})
            tops[d] = max(sorted(v), key=v.get) if v else None
        same = len(set(tops.values())) == 1 and None not in tops.values()
        agree[g] = {
            "most_chunks_by_dose": tops,
            "both_doses": next(iter(tops.values())) if same else "no answer",
        }
    res["groups_both_doses"] = agree
    return res


# ------------------------------------------------------------------------------ the passes


def check(cfg: dict) -> dict:
    """Check pass: candidates only; nothing is computed for any target."""
    t = settings(cfg)
    b = build(cfg, targets=False)
    res: dict = {"exploratory": True, "post_hoc_design": True, "stage": "check",
                 "settings": t, "candidates": b["meta"]["candidates"],
                 "dropped": b["meta"]["dropped"], "measures": {}, "not_attempted": {}}  # fmt: skip
    fw, info = fw_vectors(cfg, b)
    res["function_words_background"] = info
    for m, dist in zip(FW, (tv.delta, tv.cosine_delta), strict=True):
        sc = dc.centroid_scores(fw, b["cands"], dist)
        res["measures"][m] = {
            "known_answer": dc.known_answer(
                {k: v for k, v in sc.items() if "|test|" in k}, b["cands"], t
            )
        }
    for name in cfg["lab"]["two_voices_enc"]["encoders"]:
        try:
            v = enc_vectors(name, b, ("check",))
        except OSError as e:
            res["not_attempted"][f"encoder_{name}"] = str(e)
            continue
        sc = dc.centroid_scores(v, b["cands"], tv.cosine_delta)
        res["measures"][f"encoder_{name}"] = {
            "known_answer": dc.known_answer(
                {k: v for k, v in sc.items() if "|test|" in k}, b["cands"], t
            )
        }
    try:
        res["measures"]["author_models"] = alm_check(cfg, b)
    except OSError as e:
        res["not_attempted"]["author_models"] = str(e)
    res["passed_check"] = [m for m, r in res["measures"].items() if r["known_answer"]["passed"]]
    return res


def run(cfg: dict) -> dict:
    """Target pass, for the measures that passed the check only."""
    t = settings(cfg)
    res = check(cfg)
    passed = res["passed_check"]
    if res["not_attempted"]:
        res["stopped"] = f"check not complete: {sorted(res['not_attempted'])}"
        return res
    if not passed:
        res["stopped"] = (
            "every measure missed the known-answer bar: neither question is "
            "answered, no target was computed, and no further redesign is made"
        )
        return res
    res["stage"] = "target"
    b = build(cfg, targets=True)
    res["texts"] = {
        k: b["meta"][k]
        for k in ("lectures", "groups", "book_of_mormon", "not_attempted")
        if k in b["meta"]
    }
    res["left_out"] = dc.LEFT_OUT
    if any(m in passed for m in FW):
        fw, _ = fw_vectors(cfg, b)
        for m, dist in zip(FW, (tv.delta, tv.cosine_delta), strict=True):
            if m in passed:
                res["measures"][m] = dc.measure(fw, b, dist, t, False)
    for name in cfg["lab"]["two_voices_enc"]["encoders"]:
        m = f"encoder_{name}"
        if m in passed:
            res["measures"][m] = dc.measure(enc_vectors(name, b, ("check", "target")), b,
                                            tv.cosine_delta, t, False)  # fmt: skip
    if "author_models" in passed:
        res["measures"]["author_models"] = alm_targets(cfg, b, res["measures"]["author_models"])
    res["question_b"] = dc.combined(res["measures"], res["measures"].get("author_models"))
    res["question_b"]["measures_passed"] = passed
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "embed", "train", "check", "score", "run"])
    ap.add_argument("--stage", choices=["check", "target"], default="check")
    ap.add_argument("--encoder", help="embed: one encoder (default: every one in the config)")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plan":
        b = build(cfg, targets=False)
        print(json.dumps({"candidates": {c: {k: m[k] for k in ("words_masked", "chunks")}
                                         for c, m in b["meta"]["candidates"].items()},
                          "dropped": b["meta"]["dropped"]}, indent=1))  # fmt: skip
        return 0
    if a.cmd == "embed":
        names = [a.encoder] if a.encoder else list(cfg["lab"]["two_voices_enc"]["encoders"])
        if a.stage == "target":
            passed = check(cfg)["passed_check"]
            names = [n for n in names if f"encoder_{n}" in passed]
            print("encoders that passed the check:", names or "none")
        for name in names:
            embed(cfg, name, a.stage)
        return 0
    if a.cmd == "train":
        return train(cfg)
    if a.cmd == "score":
        return score_targets(cfg)
    res = check(cfg) if a.cmd == "check" else run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = dc._commit()
    out(OUT).write_text(json.dumps(res, indent=1) + "\n")
    for m, r in res["measures"].items():
        ka = r["known_answer"]
        print(m, ka.get("macro", ka.get("passed_doses")), ka["passed"])
    print("dropped:", res["dropped"], "| not attempted:", res["not_attempted"] or "none")
    if res.get("question_b"):
        print(json.dumps(res["question_b"]["per_lecture"], indent=1))
    print(res.get("stopped", ""), "->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
