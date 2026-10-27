"""Choose passim's settings on planted quotations, never on the Book of Mormon (BOM-16).

``kjv_mask.passim`` is unregistered. 4.2 seals the Book of Mormon from threshold setting, so the
settings are chosen on a test set where the truth is known by construction: passages of
non-religious period prose (TCP Evans texts labelled ``scientific_medical`` or
``legal_political``, where real scripture is rare) with KJV verses planted at known places.

Per document, ``PLANTS`` insertions, in equal numbers:

``verbatim``    one or two consecutive verses copied exactly
``paraphrase``  verses with tokens replaced at random to a target identity of 0.75, inside
                4.4's 0.60-0.90 band
``decoy``       verses replaced to 0.40 identity, below the band: these must come back original

Scoring is per token of the test documents against the planted truth, with decoys and
background both counting as ``original``. Background passages are screened first: any with a
verbatim hit of its own at a sensitive setting is real scripture and is dropped, so a true
detection is never scored as a false positive.

**Selection rule, fixed before the grid was run:** the setting with the highest *masking* F1
wins -- a token is masked if it is labelled verbatim or paraphrase, and both are what
attribution removes. Per-class figures are reported but not optimised: a planted 0.75
paraphrase that keeps ten words intact legitimately contains a verbatim span under 4.4, so
scoring the planted class exactly would penalise the registered rule. Ties go to the larger
``n``, then the larger ``min_align`` (fewer chance seeds). (A first draft optimised the mean of
the two class F1s; it was replaced before any grid result existed, for the reason above.) The
winner goes into the amendment that registers ``kjv_mask.passim``; the full grid is published
beside it.

Usage::

    python -m kjv_mask.evaluate build            # -> data/kjv_mask/eval_docs.jsonl
    python -m kjv_mask.evaluate grid             # -> data/kjv_mask/eval_grid.jsonl
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import mask
from metadata.config import load as load_config
from metadata.config import sha256_of_config

KJV = Path("data/kjv/kjv.jsonl")
DOCS = Path("data/kjv_mask/eval_docs.jsonl")
GRID = Path("data/kjv_mask/eval_grid.jsonl")
WORK = Path("data/corpus/kjv_mask_eval")

N_DOCS = 40
DOC_WORDS = 3000
PLANTS = 6  # per document, two of each kind
IDENTITY = {"verbatim": 1.0, "paraphrase": 0.75, "decoy": 0.40}
MIN_VERSE_TOKENS = 12
# a deliberately sensitive setting for screening background passages for real scripture
SCREEN = {"n": 3, "min_match": 1, "min_align": 20, "gap": 100, "max_df": 100}

GRID_AXES = {
    "n": [3, 4, 5],
    "min_match": [1, 2, 3],
    "min_align": [20, 40],
    "gap": [100, 600],
    "max_df": [100],
}

_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def _perturb(words: list[str], identity: float, pool: list[str], rng: random.Random) -> list[str]:
    out = list(words)
    k = round(len(words) * (1 - identity))
    for i in rng.sample(range(1, len(words) - 1), min(k, len(words) - 2)):
        out[i] = rng.choice(pool)
    return out


def build() -> int:
    cfg = load_config()
    rng = random.Random(cfg["seed"])
    genre = {
        r["work_id"]: r["genre"]
        for r in pq.read_table(
            "data/catalog/genre.parquet", columns=["work_id", "genre"]
        ).to_pylist()
        if r["work_id"].startswith("tcp:")
    }
    cat = pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "genre_src", "text_path"]
    ).to_pylist()
    bg = [
        r["text_path"]
        for r in cat
        if r["genre_src"] == "evans"
        and r["text_path"]
        and (genre.get(r["work_id"]) or "").split(",")[0]
        in ("scientific_medical", "legal_political")
    ]
    bg.sort()
    rng.shuffle(bg)
    # Candidate background passages, twice as many as needed, screened for real scripture.
    passages = []
    for path in bg:
        words = Path(path).read_text(encoding="utf-8", errors="replace").replace("ſ", "s")
        words = words.split()
        if len(words) < DOC_WORDS:
            continue
        start = rng.randrange(0, len(words) - DOC_WORDS + 1)
        passages.append((path, words[start : start + DOC_WORDS]))
        if len(passages) >= 2 * N_DOCS:
            break
    screen = mask(
        [{"id": f"bg:{i}", "text": " ".join(w)} for i, (_, w) in enumerate(passages)],
        WORK / "screen",
        SCREEN,
    )
    clean = [p for i, p in enumerate(passages) if not any(
        s.kind == "verbatim" for s in screen[f"bg:{i}"])]  # fmt: skip
    print(f"{len(passages)} background passages, {len(clean)} with no verbatim scripture")

    verses = [json.loads(ln) for ln in KJV.read_text().splitlines()]
    verses = [v for v in verses if len(_WORD.findall(v["text"])) >= MIN_VERSE_TOKENS]
    DOCS.parent.mkdir(parents=True, exist_ok=True)
    kinds = ["verbatim", "paraphrase", "decoy"] * (PLANTS // 3)
    n = 0
    with DOCS.open("w") as fh:
        for path, body in clean[:N_DOCS]:
            cuts = sorted(rng.sample(range(100, DOC_WORDS - 100), PLANTS))
            pieces, truth, pos, prev = [], [], 0, 0
            rng.shuffle(kinds)
            for cut, kind in zip(cuts, kinds, strict=True):
                pieces.append(" ".join(body[prev:cut]) + " ")
                pos += len(pieces[-1])
                v = rng.randrange(len(verses) - 1)
                text = verses[v]["text"]
                if rng.random() < 0.5:
                    text += " " + verses[v + 1]["text"]
                planted = " ".join(_perturb(text.split(), IDENTITY[kind], body, rng))
                truth.append({"start": pos, "end": pos + len(planted), "kind": kind,
                              "ref": verses[v]["ref"]})  # fmt: skip
                pieces.append(planted + " ")
                pos += len(planted) + 1
                prev = cut
            pieces.append(" ".join(body[prev:]))
            fh.write(json.dumps({"id": f"eval:{n}", "source": path, "text": "".join(pieces),
                                 "truth": truth}) + "\n")  # fmt: skip
            n += 1
    print(f"{n} test documents, {n * PLANTS} plants -> {DOCS}")
    return 0


def _labels(text: str, spans: list[dict], decoy_as_original: bool) -> list[str]:
    out = []
    for m in _WORD.finditer(text):
        lab = "original"
        for s in spans:
            if s["start"] <= m.start() < s["end"]:
                lab = s["kind"]
                break
        if decoy_as_original and lab == "decoy":
            lab = "original"
        out.append(lab)
    return out


def score(docs: list[dict], spans: dict) -> dict:
    tally: dict[tuple[str, str], int] = {}
    for d in docs:
        truth = _labels(d["text"], d["truth"], True)
        pred = _labels(d["text"], [s.__dict__ for s in spans[d["id"]]], False)
        for t, p in zip(truth, pred, strict=True):
            tally[(t, p)] = tally.get((t, p), 0) + 1
    out = {}
    for k in ("verbatim", "paraphrase"):
        tp = tally.get((k, k), 0)
        fp = sum(v for (t, p), v in tally.items() if p == k and t != k)
        fn = sum(v for (t, p), v in tally.items() if t == k and p != k)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out[k] = {
            "precision": prec,
            "recall": rec,
            "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
        }
    orig = sum(v for (t, _), v in tally.items() if t == "original")
    out["original_masked_rate"] = (
        sum(v for (t, p), v in tally.items() if t == "original" and p != "original") / orig
    )
    tp = sum(v for (t, p), v in tally.items() if t != "original" and p != "original")
    fp = sum(v for (t, p), v in tally.items() if t == "original" and p != "original")
    fn = sum(v for (t, p), v in tally.items() if t != "original" and p == "original")
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    out["mask"] = {
        "precision": prec,
        "recall": rec,
        "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
    }
    out["objective"] = out["mask"]["f1"]
    return out


def grid() -> int:
    docs = [json.loads(ln) for ln in DOCS.read_text().splitlines()]
    done = {}
    if GRID.exists():
        for ln in GRID.read_text().splitlines():
            r = json.loads(ln)
            done[json.dumps(r["params"], sort_keys=True)] = r
    keys = list(GRID_AXES)
    combos = [dict(zip(keys, vals, strict=True)) for vals in itertools.product(*GRID_AXES.values())]
    stamp = sha256_of_config()
    for params in combos:
        k = json.dumps(params, sort_keys=True)
        if k in done:
            continue
        result = score(docs, mask(docs, WORK, params))
        rec = {"params": params, **result, "config_sha256": stamp}
        with GRID.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        done[k] = rec
        m = result["mask"]
        print(
            f"{params}  mask P {m['precision']:.3f} R {m['recall']:.3f} F1 {m['f1']:.3f}  "
            f"verbatim F1 {result['verbatim']['f1']:.3f}",
            flush=True,
        )
    best = max(
        done.values(),
        key=lambda r: (r["objective"], r["params"]["n"], r["params"]["min_align"]),
    )
    print(f"selected: {best['params']}  objective {best['objective']:.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("grid")
    a = ap.parse_args(argv)
    return build() if a.cmd == "build" else grid()


if __name__ == "__main__":
    sys.exit(main())
