"""Joseph Smith's later revelations against the sealed text (Amendment 54; post hoc deep dive).

The registered test uses only his 1828-29 revelations (3,039 training tokens). Revelation Book 1
is held whole (``data/private/candidates/raw/js-1828-1829-revelations/``); its sections after
March 1830 were set aside by rule 9. This takes those whose title begins "Revelation"
(``js_later.title_prefix``), masks King James spans (``python -m kjv_mask.run js_later``), drops
Book of Mormon quotations by Amendment 43's rule (every section postdates the dictation, so a
non-biblical, non-stock passage of at least 20 words shared with the book is a quotation), and:

- ``classic``, ``style <size>``: adds the unit (``UNIT``) to Amendment 44's references (which
  already hold his pooled non-revelatory prose) for Burrows' and Cosine Delta, General Imposters
  and the style encoders;
- ``alm <size>`` (on the H100 type that scored Amendments 43-51): one model on the whole unit as
  Amendment 43's, then up to ``js_later.slices_max`` equal-dose slices (the 1828-29 sample's
  length, evenly spread in book order), each scored on the sealed set; no weights kept;
- ``report``: Amendment 53's people-only ranking with the unit added (with and without the
  1828-29 revelations), and each slice's median rank in Amendment 51's equal-dose pool against the
  1828-29 revelation model, with the slice's date span.

Numbers only in ``data/blind/a54/``; section text stays in ``data/private/candidates/later/``.

Usage::

    python -m eval.js_later sections               # Mac: write the sections (private)
    python -m eval.js_later plan                   # Mac: mask, drop quotations, encode
    python -m eval.js_later classic                # Mac: classical methods
    python -m eval.js_later style base|mid         # Mac: style encoders
    python -m eval.js_later alm pilot|base|mid     # GPU: whole unit + equal-dose slices
    python -m eval.js_later report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from metadata.config import load as load_config
from metadata.config import stamp

UNIT = "cand__joseph-smith__revelations__post1830"
TEXTS = Path("data/private/candidates/later")  # Joseph Smith Papers text: private repo only
SPANS = Path("data/kjv_mask/js_later/spans.jsonl")
OUT = Path("data/blind/a54")
INPUTS = Path("data/corpus/alm/a54")
_YEAR = re.compile(r"\b(18[23]\d)\b")


def year_of(title: str) -> int | None:
    m = _YEAR.search(title)
    return int(m.group(1)) if m else None


def sections() -> int:
    """Each rule-9 section titled as a revelation, one text file per section (private)."""
    from ingest import candidate_words as cw
    from ingest import jsp

    c = load_config()["js_later"]
    sid = c["source"]
    chosen = {e["link_id"]: e for e in json.loads(cw.SELECTIONS.read_text())[sid]["entries"]}
    TEXTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, s in enumerate(jsp.sections(cw._records(sid), cw._toc(sid))):
        title = s["title"] or ""
        pick = chosen.get(s["link_id"])
        if (pick and pick["decision"] in ("pre1830", "other_author")) or not title.startswith(
            c["title_prefix"]
        ):
            continue
        words = [w for w, _ in jsp.transcript_words(s["html"] or "")]
        if not words:
            continue
        (TEXTS / f"{n:03d}.txt").write_text(" ".join(words) + "\n", encoding="utf-8")
        rows.append({"id": f"later:{n:03d}", "title": title, "link_id": s["link_id"],
                     "year": year_of(title), "words": len(words)})  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sections.json").write_text(json.dumps({**stamp(), "source": sid, "sections": rows},
                                                  indent=1) + "\n")  # fmt: skip
    by = defaultdict(int)
    for r in rows:
        by[r["year"]] += r["words"]
    print(f"{len(rows)} sections, {sum(by.values()):,} words: "
          + ", ".join(f"{y} {w:,}" for y, w in sorted(by.items(), key=lambda kv: kv[0] or 0))
          + f" -> {TEXTS}/, {OUT / 'sections.json'}")  # fmt: skip
    return 0


def docs() -> list[dict]:
    """The sections as ``kjv_mask.run`` reads documents (artifact-normalised, as candidates)."""
    from ocr_fix.normalize import artifacts

    return [{"id": f"later:{p.stem}", "words": len(t.split()), "load": lambda t=t: t}
            for p in sorted(TEXTS.glob("*.txt"))
            for t in [artifacts(p.read_text(encoding="utf-8"))[0]]]  # fmt: skip


def norm(t: str) -> list[str]:
    return re.findall(r"[a-z]+", t.lower())


def quotation_passages(w: list[str], bom: set, kjv: set, ctrl: set, q: dict) -> list[list[str]]:
    """Amendment 43's rule (``eval.bom_overlap``) for text written after the whole book was
    dictated: maximal runs of ``ngram`` words shared with the book, biblical runs set aside,
    runs within ``max_gap`` merged; a passage of at least ``min_words`` holding a run that is not
    stock phrasing (under half its windows in the control texts) is a quotation."""
    n = q["ngram"]
    hs = {i for i in range(len(w) - n + 1) if tuple(w[i : i + n]) in bom}
    runs, i = [], 0
    while i < len(w) - n + 1:
        if i not in hs:
            i += 1
            continue
        j = i
        while j + 1 in hs:
            j += 1
        grams = [tuple(w[k : k + n]) for k in range(i, j + 1)]
        if all(g in kjv for g in grams):
            cls = "biblical"
        elif sum(g in ctrl for g in grams) / len(grams) >= 0.5:
            cls = "stock"
        else:
            cls = "after"
        runs.append((i, j + n, cls))
        i = j + n
    passages: list[list] = []
    for a, b, cls in runs:
        if cls == "biblical":
            continue
        if passages and a - passages[-1][1] <= q["max_gap"]:
            passages[-1][1] = max(passages[-1][1], b)
            passages[-1][2].add(cls)
        else:
            passages.append([a, b, {cls}])
    return [w[a:b] for a, b, c in passages if b - a >= q["min_words"] and "after" in c]


def _sets(n: int) -> tuple[set, set, set]:
    """Book of Mormon narrative, King James and control-text ``n``-grams, as eval.bom_overlap."""
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    bw = [w for ln in open("data/bom/1830/edition_1830.jsonl")
          for r in [json.loads(ln)] if r.get("book") for w in norm(r.get("text", ""))]  # fmt: skip
    kjv = norm(" ".join(json.loads(ln)["text"] for ln in open("data/kjv/kjv.jsonl")))
    tok = Tokenizer.from_file(str(TOKENIZER))
    ctrl: list[str] = []
    for f in sorted(Path("data/corpus/alm/candidates/inputs").glob("ctrl__*.npz")):
        ctrl += norm(tok.decode(np.load(f)["train"].ravel().tolist()))

    def grams(x: list[str]) -> set:
        return {tuple(x[i : i + n]) for i in range(len(x) - n + 1)}

    return grams(bw), grams(kjv), grams(ctrl)


def words() -> list[tuple[str, list[str]]]:
    """[(section id, masked words less quotations)] in book order."""
    from alm.candidates import drop_quotations
    from segment.build import original_words

    q = load_config()["candidates"]["bom_quotation"]
    spans = {r["id"]: r["spans"] for r in map(json.loads, SPANS.read_text().splitlines())}
    sets = _sets(q["ngram"])
    out = []
    for d in docs():
        if d["id"] not in spans:
            raise SystemExit(f"{d['id']} not masked: run python -m kjv_mask.run js_later")
        text = d["load"]()
        passages = quotation_passages(norm(text), *sets, q)
        ws = original_words(text, spans[d["id"]])
        out.append((d["id"], drop_quotations(ws, passages, q["ngram"]) if passages else ws))
    return out


def plan() -> int:
    from tokenizers import Tokenizer

    from timelocked_lm.release import EOT, TOKENIZER

    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    meta = {r["id"]: r for r in json.loads((OUT / "sections.json").read_text())["sections"]}
    ids: list[int] = []
    rows = []
    for sid, ws in words():
        enc = [*tok.encode(" ".join(ws)).ids, eot]
        m = meta[sid]
        rows.append({"id": sid, "year": m["year"], "raw_words": m["words"], "kept_words": len(ws),
                     "token_start": len(ids), "tokens": len(enc)})  # fmt: skip
        ids += enc
    INPUTS.mkdir(parents=True, exist_ok=True)
    np.savez(INPUTS / f"{UNIT}.npz", train=np.array(ids, dtype=np.int32))
    raw = sum(r["raw_words"] for r in rows)
    kept = sum(r["kept_words"] for r in rows)
    (OUT / "plan.json").write_text(json.dumps({**stamp(), "unit": UNIT, "raw_words": raw,
                                               "kept_words": kept, "tokens": len(ids),
                                               "sections": rows}, indent=1) + "\n")  # fmt: skip
    print(f"{len(rows)} sections: {raw:,} words, {kept:,} after masking and quotations, "
          f"{len(ids):,} tokens -> {INPUTS / (UNIT + '.npz')}")  # fmt: skip
    return 0


def _refs() -> dict:
    """Amendment 44's references (his pooled prose included) plus the later revelations."""
    from classic.blind_score import references
    from classic.features import tokenize
    from eval.js_register import POOL, POOL_FROM

    refs = references()
    toks = [t for u in POOL_FROM for t in refs[u]["tokens"]]
    refs[POOL] = {**refs[POOL_FROM[0]], "sample": "nonrevelatory", "words": len(toks),
                  "flag": "", "tokens": toks}  # fmt: skip
    ws = [w for _, x in words() for w in x]
    refs[UNIT] = {**refs[POOL_FROM[0]], "sample": "revelations", "words": len(ws), "flag": "",
                  "tokens": tokenize(" ".join(ws))}  # fmt: skip
    return refs


def classic() -> int:
    from classic.blind_score import pool, score
    from eval.js_register import A43, _rows

    cfg = load_config()
    th = json.loads((A43 / "thresholds.json").read_text())["thresholds"]
    res = score(_rows(), cfg, _refs(), pool(cfg), th)
    (OUT / "classic.json").write_text(json.dumps({"unit": UNIT, "ids": res}))
    print(f"classic: {len(res)} ids -> {OUT / 'classic.json'}")
    return 0


def style(size: str) -> int:
    from classic.blind_score import pool
    from eval.js_register import A43, _rows
    from style_embed.blind_score import score

    cfg = load_config()
    th = json.loads((A43 / "thresholds.json").read_text())["thresholds"]
    res = score(_rows(), cfg, _refs(), pool(cfg), th, size=size)
    (OUT / f"style_{size}.json").write_text(json.dumps({"unit": UNIT, "ids": res}))
    print(f"style {size}: {len(res)} ids -> {OUT / f'style_{size}.json'}")
    return 0


def alm(size: str, micro: int) -> int:
    """The whole unit, then equal-dose slices; scores saved after every model (resumes)."""
    import torch

    from alm.benchmark import finetune, window_loss
    from alm.candidates import PLAN as A43_PLAN
    from eval.js_register import REVELATION, _rows
    from eval.part2_decoys import _setup, slice_starts
    from metadata.config import derive_seed

    cfg, dev, model, state, tok = _setup(size)
    a, lr = cfg["alm"], cfg["timelocked_lm"]["finetune_lr"]
    n = next(u for u in json.loads(A43_PLAN.read_text())["units"]
             if u["key"] == REVELATION)["train_tokens"]  # fmt: skip
    ids = np.load(INPUTS / f"{UNIT}.npz")["train"]
    rows = sorted(_rows(), key=lambda r: r["id"])
    texts = [tok.encode(r["text"]).ids for r in rows]
    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in texts]
    out = OUT / f"alm_{size}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    res = json.loads(out.read_text()) if out.exists() else {"unit": UNIT, "size": size,
                                                            "dose": n, "models": {}}  # fmt: skip
    jobs = [("whole", 0, len(ids), f"{a['train_seed']}:candidates:{UNIT}")]
    jobs += [
        (f"grid{j}", s, n, f"{a['train_seed']}:a54-slices:{UNIT}#grid{j}")
        for j, s in enumerate(slice_starts(len(ids), n, cfg["js_later"]["slices_max"]))
    ]
    for name, start, length, tag in jobs:
        if name in res["models"]:
            continue
        model.load_state_dict(state)
        seed = derive_seed(tag, cfg)
        torch.manual_seed(seed)
        info = finetune(model, ids[start : start + length], cfg, seed, micro, dev, lr)
        with torch.no_grad():
            loss = [window_loss(model, x, a["score_window"], dev) for x in texts]
        res["models"][name] = {"start": int(start), "tokens": int(length), **info, "scores": {
            r["id"]: float(np.mean(np.array(loss[i]) - np.array(base[i])))
            for i, r in enumerate(rows)}}  # fmt: skip
        out.write_text(json.dumps(res))
        print(f"  a54 {size} {name}: tokens {start}-{start + length}", flush=True)
    return 0


def span_years(start: int, length: int, secs: list[dict]) -> list[int]:
    """First and last year of the sections a token range touches."""
    ys = [s["year"] for s in secs if s["token_start"] < start + length
          and s["token_start"] + s["tokens"] > start and s["year"]]  # fmt: skip
    return [min(ys), max(ys)] if ys else []


def report() -> int:
    from eval.js_register import A43, KEY, POOL, REVELATION
    from eval.js_register import OUT as A44
    from eval.part2_decoys import BLIND, _dose, _placebo_ranks, _revelation

    cfg = load_config()
    key = json.loads(KEY.read_text())
    bom = sorted(i for i, k in key.items() if k["kind"] == "bom")
    secs = json.loads((OUT / "plan.json").read_text())["sections"]
    methods: dict[str, tuple[dict, bool]] = {}
    if (OUT / "classic.json").exists():
        c = json.loads((OUT / "classic.json").read_text())["ids"]
        for m, lower in (("cosine_delta", True), ("burrows_delta", True),
                         ("general_imposters", False)):  # fmt: skip
            methods[m] = ({i: c[i][m] for i in bom}, lower)
    for size in ("base", "mid"):
        p = OUT / f"style_{size}.json"
        if p.exists():
            st = json.loads(p.read_text())["ids"]
            methods[f"style_{size}"] = ({i: st[i]["cosine"] for i in bom}, True)
    res: dict = {"unit": UNIT, "chunks": len(bom), "people": {}, "slices": {}}
    for size in ("pilot", "base", "mid"):
        p = OUT / f"alm_{size}.json"
        if not p.exists():
            continue
        mine = json.loads(p.read_text())["models"]
        prior = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        pooled = json.loads((A44 / f"alm_{size}.json").read_text())["scores"]
        if "whole" in mine:
            methods[f"alm_{size}"] = ({i: {**prior[i]["scores"], POOL: pooled[i],
                                           UNIT: mine["whole"]["scores"][i]} for i in bom},
                                      True)  # fmt: skip
        pool = {**_dose(size), **{m: v["scores"] for m, v in json.loads(
            (BLIND / f"placebo_{size}.json").read_text())["models"].items()}}  # fmt: skip
        rev = _revelation(size, bom)
        per = []
        for name, v in sorted(mine.items(), key=lambda kv: kv[1]["start"]):
            if name == "whole":
                continue
            r = _placebo_ranks({**pool, f"later#{name}": v["scores"]}, rev, bom)
            per.append({"slice": name, "years": span_years(v["start"], v["tokens"], secs),
                        "median_rank": r["median_rank"]["later"],
                        "revelation_median_rank": r["revelation_median_rank"],
                        "models_ranked": r["models_ranked"]})  # fmt: skip
        k = sum(x["median_rank"] <= x["revelation_median_rank"] for x in per)
        res["slices"][size] = {"slices": len(per), "at_or_better": k,
                               "slice_stable": k / len(per) > cfg["js_later"]["slice_majority"]
                               if per else None, "per_slice": per}  # fmt: skip
    for m, (per_id, lower) in methods.items():
        res["people"][m] = {}
        for label, drop in (("with_revelations", ()), ("without_revelations", (REVELATION,))):
            ranks: dict[str, list[int]] = defaultdict(list)
            for sc in per_id.values():
                c = {u: v for u, v in sc.items() if u.startswith("cand__") and u not in drop}
                for r, u in enumerate(sorted(c, key=lambda u: c[u] if lower else -c[u]), 1):
                    ranks[u].append(r)
            res["people"][m][label] = {
                u: {"mean_rank": float(np.mean(v)), "first": sum(r == 1 for r in v)}
                for u, v in sorted(ranks.items(), key=lambda kv: np.mean(kv[1]))}  # fmt: skip
    (OUT / "report.json").write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    for m, v in res["people"].items():
        line = []
        for label, rk in v.items():
            order = list(rk)
            line.append(f"{label}: later {order.index(UNIT) + 1}/{len(order)} "
                        f"(mean {rk[UNIT]['mean_rank']:.1f}, first {rk[UNIT]['first']}); "
                        f"top {order[0].removeprefix('cand__')[:32]}")  # fmt: skip
        print(f"{m:18s} " + " | ".join(line))
    for size, v in res["slices"].items():
        print(f"{size} slices: {v['at_or_better']}/{v['slices']} at or above the 1828-29 "
              f"revelation model; slice-stable {v['slice_stable']}")  # fmt: skip
    print(f"-> {OUT / 'report.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["sections", "plan", "classic", "style", "alm", "report"])
    ap.add_argument("size", nargs="?")
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "style":
        return style(a.size)
    if a.cmd == "alm":
        return alm(a.size, a.micro_batch)
    return {"sections": sections, "plan": plan, "classic": classic, "report": report}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
