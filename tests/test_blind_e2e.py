"""Seal -> scorer outputs in the scorers' real format -> unblind -> synthesis, on synthetic data
(BOM-32, BOM-35). No Book of Mormon text."""

import json
import random
from pathlib import Path

from blind import seal as S
from blind import unblind as U

# BOM-17's real chunk ids, so the synthesis's discovery/confirmation split applies
CHUNKS = {"narrator:000:Nephi:5000:000": "discovery", "narrator:000:Nephi:5000:001": "discovery",
          "narrator:000:Nephi:5000:002": "confirmation",
          "narrator:000:Nephi:5000:003": "confirmation"}  # fmt: skip
PLAN = {"units": [
    {"key": "cand__alpha__printed__pre1830", "kind": "candidate", "candidate": "Alpha",
     "flag": "", "confirmatory": True},
    {"key": "cand__alpha__printed__post1830", "kind": "candidate", "candidate": "Alpha",
     "flag": "", "confirmatory": False},
    {"key": "cand__beta__printed__pre1830", "kind": "candidate", "candidate": "Beta", "flag": "",
     "confirmatory": True},
    {"key": "ctrl__history", "kind": "control"},
]}  # fmt: skip
UNITS = ["cand__alpha__printed__pre1830", "cand__alpha__printed__post1830",
         "cand__beta__printed__pre1830"]  # fmt: skip
OWNER = {"Alpha": UNITS[:2], "Beta": UNITS[2:]}


def _sealed() -> tuple[list[dict], dict]:
    bom = [{"chunk_id": c, "text": " ".join(f"b{c[-1]}w{j}" for j in range(50))} for c in CHUNKS]
    decoys = [{"author": a, "source": f"{a}-src", "start": 100 * k, "words": 50,
               "text": " ".join(f"{a}{k}w{j}" for j in range(50))}
              for k, a in enumerate(["Alpha", "Beta", "control:gamma", "Alpha"])]  # fmt: skip
    return S.seal(bom, decoys, random.Random(7))


def _records(key: dict) -> dict[str, dict]:
    """Per sealed id, each method's record as its scorer returns it, keyed by unit. Decoys look
    like their author; Book of Mormon chunks lean to Beta; the control decoy matches nobody."""
    out = {}
    for i, k in key.items():
        near = OWNER.get(k.get("author", "Beta"), [])  # control decoy: near no unit
        dist = {u: 0.2 if u in near else 0.8 for u in UNITS}
        gi = {u: 0.97 if u in near else 0.1 for u in UNITS}
        band = {u: "match" if u in near else "non_match" for u in UNITS}
        out[i] = {
            "classic": {"burrows_delta": dist, "cosine_delta": dist,
                        "burrows_first": min(dist, key=dist.get),
                        "cosine_first": min(dist, key=dist.get), "general_imposters": gi,
                        "gi_first": max(gi, key=gi.get), "gi_call": band,
                        "ensc": max(gi, key=gi.get), "ensc_posteriors": gi},
            "style": {"cosine": dist, "first": min(dist, key=dist.get), "general_imposters": gi,
                      "call": band},
            "alm": {"scores": {**dist, "ctrl__history": 0.5}, "first": min(dist, key=dist.get),
                    "first_candidate": min(dist, key=dist.get),
                    "margins": {u: 0.5 - v for u, v in dist.items()}, "call": band},
        }  # fmt: skip
    return out


def _outputs(tmp: Path, key: dict) -> list[str]:
    recs = _records(key)
    files = []
    for method, size in (("classic", None), ("style", None), ("alm", "base")):
        per = {i: r[method] for i, r in recs.items()}
        scores = {"ids": per} if method == "alm" else {"units": {}, "ids": per}
        p = tmp / (f"{method}_{size}.json" if size else f"{method}.json")
        p.write_text(json.dumps({"method": method, "size": size, "scores": scores}))
        files.append(str(p))
    dating = tmp / "dating.json"
    dating.write_text(
        json.dumps(
            {
                "method": "dating",
                "size": None,
                "scores": {i: {"grammar": [[1820, 1790, 1830]]} for i in key},
            }
        )
    )
    return [*files, str(dating)]


def test_seal_score_unblind_synthesise(tmp_path: Path, monkeypatch) -> None:
    rows, key = _sealed()
    assert {r["id"] for r in rows} == set(key)
    methods = U.unblind(_outputs(tmp_path, key), key, PLAN, CHUNKS, None)
    assert set(methods) == {"classic", "style", "alm_base", "dating"}
    # raw Book of Mormon records by chunk, as the synthesis reads them
    assert set(methods["classic"]["bom"]) == set(CHUNKS)
    for m, views in (("classic", ["burrows_delta", "cosine_delta", "general_imposters", "ensc"]),
                     ("style", ["style"]), ("alm_base", ["alm"])):  # fmt: skip
        assert set(views) <= set(methods[m]["views"])  # plus each "_achievable" twin
        for v in views:
            d = methods[m]["views"][v]["decoys"]
            assert d["closed_set"] == {"decoys": 3, "correct": 3, "accuracy": 1.0}
            loo = methods[m]["views"][v]["leave_one_candidate_out"]
            assert loo["Alpha"] == {"Beta": 4} and loo["Beta"] == {"Alpha": 4}
    ver = methods["style"]["views"]["style"]["decoys"]["verification"]
    assert ver == {"candidate": {"decoys": 3, "correct": 3}, "control": {"decoys": 1, "correct": 1}}
    assert methods["classic"]["views"]["cosine_delta"]["decoys"]["verification"] is None
    assert "views" not in methods["dating"]
    json.dumps(methods)

    # the synthesis reads the same unblinded format
    from synth import model as M

    out, bench = tmp_path / "synthesis", tmp_path / "bench"
    bench.mkdir()
    (bench / "alm_candidates_plan.json").write_text(json.dumps(PLAN))
    (bench / "imitation.json").write_text(
        json.dumps(
            {
                "methods": {
                    "general_imposters": {"weight": 0.5},
                    "style": {"weight": 1.0},
                    "alm": {"weight": 1.0},
                }
            }
        )
    )
    rates = {"pos": {"match": 0.6, "inconclusive": 0.3, "non_match": 0.1},
             "neg": {"match": 0.05, "inconclusive": 0.35, "non_match": 0.6}}  # fmt: skip
    out.mkdir()
    (out / "rates_base.json").write_text(
        json.dumps(
            {
                "families": {
                    f: {"accuracy": 0.8, **rates} for f in ("classical", "embedding", "authorial")
                }
            }
        )
    )
    monkeypatch.setattr(M, "OUT", out)
    monkeypatch.setattr(M, "BENCH", bench)
    monkeypatch.setattr(M, "PLAN", bench / "alm_candidates_plan.json")
    res = M.run_size("base", methods, M.load_config())
    prim = res["hypotheses"]["primary"]
    assert prim["candidates"] == ["Alpha", "Beta"]
    assert prim["chunks"]["discovery"] == {"classical": 2, "embedding": 2, "authorial": 2}
    p = prim["main"]["both"]["posterior"]
    assert max(p, key=p.get) == "Beta"  # every chunk was made to look like Beta
