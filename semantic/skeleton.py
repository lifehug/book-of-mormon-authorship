"""Story skeletons (BOM-25; plan ``docs/skeleton-plan.md``).

A model reads each block of a text (a chapter, or ``skeleton.block_words`` words) and lists at
most ``skeleton.max_events`` things that happen, names replaced by roles. Two texts are compared by
local alignment of their event sequences (events match when their bge-small cosine reaches the
threshold the extractor check sets), and order is tested by shuffling. Model-assisted extraction,
simulated.

Event lists are kept under ``data/corpus/semantic/skeleton/`` (not in git: they paraphrase
licensed volumes); results under ``data/semantic/skeleton/`` hold ids and numbers, plus the
event lists of public-domain King James chapters.

Usage::

    python -m semantic.skeleton check      # extractor check -> data/semantic/skeleton/check.json
    python -m semantic.skeleton controls   # retellings -> data/semantic/skeleton/controls.json
    python -m semantic.skeleton bom        # named sources and groups -> .../skeleton/bom.json

Recoverable when usage runs out: every answered block is appended to its text's event file at
once; a transient failure is never recorded as an answer; after ``STOP_AFTER`` failed calls in a
row the run stops and exits 1, and a rerun (``scripts/skeleton_loop.sh`` reruns every 15
minutes) reads only the blocks still unanswered. A reply that cannot be parsed ``MAX_UNPARSED``
times is recorded as unreadable (no events), so it cannot stall the loop.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from metadata.genre import _TRANSIENT, _log_parse_failure

OUT = Path("data/semantic/skeleton")
EVENTS = Path("data/corpus/semantic/skeleton/events")
# King James books that are narrative throughout (the check draws its chapters from these)
NARRATIVE = ("GEN", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "EST", "ACT")

PROMPT = """Read the passage below and list, in the order they happen, at most {n} events of its \
story: things that happen, not ideas or teachings. Write each event as one short plain sentence. \
Replace every personal name, people and place name with a role or description ("a prophet", \
"the king", "a family", "the city", "the wilderness"). If the passage tells no story (sermon, \
law, genealogy, list, poetry without events), reply with the single word NONE.

Reply with the events only, one per line, each line starting with "- ".

Passage:
{text}"""

SUPPORT = """Below is a passage and a numbered list of events someone said happen in it. For \
each event, answer Y if the passage tells that it happens (in any words, names replaced by \
roles is fine) and N if it does not. Reply with one line per event, "<number> Y" or \
"<number> N", and nothing else.

Passage:
{text}

Events:
{events}"""


# The call carries only the prompt: no Claude Code system prompt, tools, MCP servers, settings or
# commands. Same model and prompt; a default call read ~27,000 tokens, this one ~2,500 (measured
# 2026-11-01). Blocks read before the change (the first 620 control blocks, the 2026-11-01
# check) carry no "invocation" field; later ones carry "lean".
INVOCATION = "lean"
LEAN = ["--system-prompt", "You follow instructions exactly.", "--tools", "", "--strict-mcp-config",
        "--disable-slash-commands", "--setting-sources", ""]  # fmt: skip
_PACE = {"per_hour": 0.0, "next": 0.0}
_PACE_LOCK = threading.Lock()


def _wait_turn() -> None:
    """At most ``_PACE["per_hour"]`` call starts an hour, evenly spaced (0: no limit)."""
    if not _PACE["per_hour"]:
        return
    with _PACE_LOCK:
        now = time.monotonic()
        start = max(now, _PACE["next"])
        _PACE["next"] = start + 3600 / _PACE["per_hour"]
    time.sleep(start - now)


def _claude(prompt: str, model: str, retries: int = 3) -> str | None:
    """The model's reply, or None after transient failures (never recorded as an answer)."""
    for _ in range(retries):
        _wait_turn()
        try:
            done = subprocess.run(["claude", "-p", "--model", model, *LEAN, prompt],
                                  capture_output=True, text=True, timeout=300,
                                  stdin=subprocess.DEVNULL)  # fmt: skip
        except Exception as exc:  # noqa: BLE001
            _log_parse_failure(model, f"<{type(exc).__name__}: {exc}>")
            continue
        text = done.stdout.strip()
        if not text or done.returncode != 0 or (_TRANSIENT.search(text) and len(text) < 300):
            _log_parse_failure(model, text or f"<rc={done.returncode}>")
            continue
        return text
    return None


def parse_events(reply: str, n: int) -> list[str] | None:
    """Event sentences from a reply; [] for NONE; None when the reply has neither."""
    if reply.strip().strip(".").upper() == "NONE":
        return []
    ev = [ln.strip()[2:].strip() for ln in reply.splitlines() if ln.strip().startswith("- ")]
    return ev[:n] if ev else None


def extract(text: str, cfg: dict) -> dict:
    """{"status": "ok", "events": [...]} or {"status": "retry"} (transient) or "unparsed"."""
    s = cfg["skeleton"]
    reply = _claude(PROMPT.format(n=s["max_events"], text=text), s["extract_model"])
    if reply is None:
        return {"status": "retry"}
    ev = parse_events(reply, s["max_events"])
    if ev is None:
        _log_parse_failure(s["extract_model"], reply)
        return {"status": "unparsed"}
    return {"status": "ok", "events": ev}


def supported(text: str, events: list[str], cfg: dict) -> list[bool] | None:
    """Per event, whether a reader call finds it in the passage; None on failure."""
    if not events:
        return []
    listing = "\n".join(f"{i} {e}" for i, e in enumerate(events, 1))
    reply = _claude(SUPPORT.format(text=text, events=listing), cfg["skeleton"]["extract_model"])
    if reply is None:
        return None
    got = dict(re.findall(r"^\s*(\d+)\s*[.:)]?\s*([YN])\b", reply, re.M | re.I))
    if len(got) < len(events):
        _log_parse_failure(cfg["skeleton"]["extract_model"], reply)
        return None
    return [got.get(str(i), "N").upper() == "Y" for i in range(1, len(events) + 1)]


def cut(words: list[str], n: int) -> list[str]:
    """Consecutive blocks of at most ``n`` words, as equal as possible."""
    k = max(1, -(-len(words) // n))
    size = -(-len(words) // k)
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def kjv_chapters() -> dict[str, str]:
    """``BOOK c`` -> chapter text, in canonical order."""
    out: dict[str, list[str]] = {}
    for ln in Path("data/kjv/kjv.jsonl").read_text().splitlines():
        r = json.loads(ln)
        out.setdefault(f"{r['book']} {r['chapter']}", []).append(r["text"])
    return {k: " ".join(v) for k, v in out.items()}


def bom_text() -> str:
    """The 1830 text, books only, in order."""
    src = Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines()
    rs = [json.loads(ln) for ln in src]
    return " ".join(r["text"] for r in rs if r["book"])


def kjv_range(books: list[str], chapters: tuple[int, int] | None = None) -> str:
    """King James text of ``books`` in order (``chapters`` limits a single book)."""
    out = []
    for ln in Path("data/kjv/kjv.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if r["book"] in books and (chapters is None or chapters[0] <= r["chapter"] <= chapters[1]):
            out.append(r["text"])
    return " ".join(out)


_MODEL: list = []


def embed(texts: list[str], cfg: dict) -> np.ndarray:
    from semantic.index import _model

    if not _MODEL:
        _MODEL.append(_model(cfg))
    if not texts:
        return np.zeros((0, 384), np.float32)
    v = _MODEL[0].encode(texts, batch_size=cfg["semantic"]["batch_size"],
                         normalize_embeddings=True, show_progress_bar=False)  # fmt: skip
    return np.asarray(v, dtype=np.float32)


def sw_score(match: np.ndarray, cfg: dict) -> float:
    """Best Smith-Waterman score of a boolean match matrix (rows: text A, cols: text B), with a
    linear gap: each row is solved in numpy by a running maximum, so no inner Python loop."""
    s = cfg["skeleton"]
    m = match.shape[1]
    idx = np.arange(1, m + 1) * s["gap_score"]
    prev = np.zeros(m + 1)
    best = 0.0
    for row in match:
        diag = prev[:-1] + np.where(row, s["match_score"], s["mismatch_score"])
        d = np.maximum(0.0, np.maximum(diag, prev[1:] + s["gap_score"]))
        h = np.maximum.accumulate(d - idx) + idx  # left gaps: H[j] = max_k D[k] + gap*(j-k)
        prev = np.concatenate(([0.0], h))
        best = max(best, float(h.max()))
    return best


def sw_align(match: np.ndarray, cfg: dict) -> dict:
    """Score, matched events and spans of the best local alignment (full traceback)."""
    s = cfg["skeleton"]
    n, m = match.shape
    h = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sc = s["match_score"] if match[i - 1, j - 1] else s["mismatch_score"]
            h[i, j] = max(0.0, h[i - 1, j - 1] + sc, h[i - 1, j] + s["gap_score"],
                          h[i, j - 1] + s["gap_score"])  # fmt: skip
    i, j = np.unravel_index(int(h.argmax()), h.shape)
    score, end = float(h[i, j]), (int(i), int(j))
    matched = 0
    while i > 0 and j > 0 and h[i, j] > 0:
        sc = s["match_score"] if match[i - 1, j - 1] else s["mismatch_score"]
        if np.isclose(h[i, j], h[i - 1, j - 1] + sc):
            matched += bool(match[i - 1, j - 1])
            i, j = i - 1, j - 1
        elif np.isclose(h[i, j], h[i - 1, j] + s["gap_score"]):
            i -= 1
        else:
            j -= 1
    return {"score": score, "matched": matched, "a_span": [int(i), end[0]],
            "b_span": [int(j), end[1]]}  # fmt: skip


def check(workers: int = 4, out_name: str = "check.json") -> int:
    """The extractor check: 20 seeded narrative chapters, extracted twice, events judged.
    ``check_lean.json`` repeats it with the lean call; the registered threshold stays the one in
    ``check.json``."""
    cfg = load_config()
    s = cfg["skeleton"]
    chapters = kjv_chapters()
    pool = sorted(k for k in chapters if k.split()[0] in NARRATIVE)
    rng = random.Random(derive_seed(s["check_seed"], cfg))
    keys = rng.sample(pool, s["check_chapters"])
    jobs = [(k, run) for k in keys for run in (1, 2)]
    with ThreadPoolExecutor(workers) as ex:
        got = dict(zip(jobs, ex.map(lambda j: extract(chapters[j[0]], cfg), jobs), strict=True))
    bad = [j for j, g in got.items() if g["status"] != "ok"]
    if bad:
        print(f"{len(bad)} extractions failed ({bad[:3]}); rerun", flush=True)
        return 1
    ev = {j: g["events"] for j, g in got.items()}
    with ThreadPoolExecutor(workers) as ex:
        sup = dict(zip(keys, ex.map(lambda k: supported(chapters[k], ev[(k, 1)], cfg), keys),
                       strict=True))  # fmt: skip
    if any(v is None for v in sup.values()):
        print("support judging failed; rerun", flush=True)
        return 1

    # the event-match threshold: cosines between run-1 events of chapters in different books
    vec = {j: embed(e, cfg) if e else np.zeros((0, 384), np.float32) for j, e in ev.items()}
    unrelated = [(vec[(a, 1)] @ vec[(b, 1)].T).ravel() for a in keys for b in keys
                 if a.split()[0] != b.split()[0] and a < b]  # fmt: skip
    cos = np.concatenate(unrelated)
    thr = float(np.quantile(cos, s["event_match_quantile"]))

    rows, agree = [], []
    for k in keys:
        a, b = vec[(k, 1)], vec[(k, 2)]
        if len(a) and len(b):
            al = sw_align((a @ b.T) >= thr, cfg)
            share = al["matched"] / min(len(a), len(b))
        else:
            al, share = None, float(len(a) == len(b) == 0)
        agree.append(share)
        rows.append({"chapter": k, "events_run1": ev[(k, 1)], "events_run2": ev[(k, 2)],
                     "agreement": share, "supported": sup[k]})  # fmt: skip
    n_ev = sum(len(v) for v in sup.values())
    n_sup = sum(sum(v) for v in sup.values())
    out = {
        "model": s["extract_model"], "chapters": keys, "event_match": thr,
        "unrelated_pairs": int(len(cos)), "median_agreement": float(np.median(agree)),
        "events_judged": n_ev, "supported_share": n_sup / n_ev if n_ev else None,
        "passes": bool(np.median(agree) >= s["check_min_agreement"]
                       and n_ev and n_sup / n_ev >= s["check_min_supported"]),
        "rows": rows,
    }  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    out["invocation"] = INVOCATION
    (OUT / out_name).write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"threshold {thr:.3f}; median agreement {out['median_agreement']:.2f}; "
          f"supported {n_sup}/{n_ev}; passes {out['passes']}")  # fmt: skip
    return 0


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


STOP_AFTER = 20  # failed calls in a row: usage ran out or the service is down
MAX_UNPARSED = 3


def _rows(name: str) -> dict[int, dict]:
    """Answered blocks of a text: "ok", or unparseable ``MAX_UNPARSED`` times (no events)."""
    path = EVENTS / f"{_safe(name)}.jsonl"
    out: dict[int, dict] = {}
    bad: dict[tuple[int, int], int] = {}
    if path.exists():
        for ln in path.read_text().splitlines():
            r = json.loads(ln)
            if r["status"] == "ok":
                out[r["block"]] = r
            elif r["status"] == "unparsed":
                k = (r["block"], r["blocks"])
                bad[k] = bad.get(k, 0) + 1
                if bad[k] >= MAX_UNPARSED and r["block"] not in out:
                    out[r["block"]] = {**r, "events": [], "unreadable": True}
    return out


def extract_all(texts: dict[str, str], cfg: dict, workers: int) -> dict[str, list[list[str]]]:
    """Events of every block of every text, resuming from ``EVENTS``; a text is returned only
    when all its blocks are answered (a failed call stays unanswered for the next run)."""
    EVENTS.mkdir(parents=True, exist_ok=True)
    blocks = {n: cut(t.split(), cfg["skeleton"]["block_words"]) for n, t in texts.items()}
    done = {n: _rows(n) for n in texts}
    jobs = [(n, i) for n, bs in blocks.items() for i in range(len(bs))
            if i not in done[n] or done[n][i]["blocks"] != len(bs)]  # fmt: skip
    print(f"{len(jobs)} blocks to read ({sum(map(len, blocks.values()))} in all)", flush=True)
    failed = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(extract, blocks[n][i], cfg): (n, i) for n, i in jobs}
        for k, f in enumerate(as_completed(futs), 1):
            n, i = futs[f]
            failed = failed + 1 if f.result()["status"] == "retry" else 0
            if failed >= STOP_AFTER:
                print(f"{failed} failed calls in a row (usage limit?); stopping, rerun resumes",
                      flush=True)  # fmt: skip
                for g in futs:
                    g.cancel()
                break
            r = {"block": i, "blocks": len(blocks[n]), "words": len(blocks[n][i].split()),
                 "invocation": INVOCATION,
                 **f.result()}  # fmt: skip
            with (EVENTS / f"{_safe(n)}.jsonl").open("a") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            if r["status"] in ("ok", "unparsed"):
                done[n] = _rows(n) if r["status"] == "unparsed" else {**done[n], i: r}
            if k % 100 == 0:
                print(f"  {k}/{len(jobs)}", flush=True)
    out = {}
    for n, bs in blocks.items():
        if all(i in done[n] and done[n][i]["blocks"] == len(bs) for i in range(len(bs))):
            out[n] = [done[n][i]["events"] for i in range(len(bs))]
        else:
            print(f"  {n}: incomplete, rerun to finish", flush=True)
    return out


def _flat(ev: list[list[str]]) -> tuple[list[str], list[int]]:
    return [e for b in ev for e in b], [i for i, b in enumerate(ev) for _ in b]


def compare(job: tuple) -> dict:
    """Alignment of A's events with B's, and the order test (B shuffled within its span)."""
    a, b, thr, seed, cfg = job
    s = cfg["skeleton"]
    if not len(a) or not len(b):
        return {"score": 0.0, "matched": 0, "order_p": None}
    match = (a @ b.T) >= thr
    al = sw_align(match, cfg)
    lo, hi = al["b_span"]
    rng = np.random.default_rng(seed)
    hits = 0
    if al["score"] > 0 and hi - lo > 1:
        cols = np.arange(match.shape[1])
        for _ in range(s["shuffles"]):
            perm = cols.copy()
            perm[lo:hi] = rng.permutation(perm[lo:hi])
            hits += sw_score(match[:, perm], cfg) >= al["score"]
        al["order_p"] = (hits + 1) / (s["shuffles"] + 1)
    else:
        al["order_p"] = 1.0
    return al


def _compare_many(pairs: list[tuple[str, str]], vec: dict, blk: dict, thr: float, cfg: dict,
                  workers: int) -> dict[tuple[str, str], dict]:  # fmt: skip
    from concurrent.futures import ProcessPoolExecutor

    jobs = [(vec[a], vec[b], thr, derive_seed(f"{cfg['skeleton']['shuffle_seed']}:{a}:{b}", cfg),
             cfg) for a, b in pairs]  # fmt: skip
    with ProcessPoolExecutor(workers) as ex:
        res = dict(zip(pairs, ex.map(compare, jobs), strict=True))
    for (a, b), r in res.items():
        r["events_a"], r["events_b"] = len(vec[a]), len(vec[b])
        if "a_span" in r:  # event spans -> block spans (block i covers words 2000i..)
            r["a_blocks"] = [blk[a][r["a_span"][0]], blk[a][r["a_span"][1] - 1]]
            r["b_blocks"] = [blk[b][r["b_span"][0]], blk[b][r["b_span"][1] - 1]]
            r["share"] = r["matched"] / min(len(vec[a]), len(vec[b]))
    return res


RETELLINGS = {  # key in data/known_answer/set.jsonl -> (volume, King James range)
    "josephus": ("institutional_books:HN26TQ", ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG"],
                 None),
    "twelve_patriarchs": ("internet_archive:bim_eighteenth-century_the-testament-of-the-twe_1791",
                          ["GEN"], (37, 50)),
    "jasher": ("internet_archive:bookofjasherwith00iliv",
               ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS"], None),
}  # fmt: skip


def unrelated(key: str, year: int, words: int, cfg: dict) -> list[tuple[str, str]]:
    """``skeleton.control_unrelated`` story-telling volumes from the retelling's window, not
    Bibles, not its own copies, within a factor of 2 of ``words`` long: (work id, path)."""
    import pyarrow.parquet as pq

    from ocr_fix.normalize import norm_path
    from reuse.exact import BIBLE, eligible_any_year, own_copies, targets

    rows = eligible_any_year(cfg)
    genre = {r["work_id"]: (r["genre"] or "").split(",")[0]
             for r in pq.read_table("data/catalog/genre.parquet").to_pylist()}  # fmt: skip
    own = own_copies(key, targets(cfg)[key], rows)
    w = cfg["reuse"]["window_years"]
    pool = sorted((r for r in rows if year - w <= r["year"] < year and r["work_id"] not in own
                   and not BIBLE.search(r["title"] or "")
                   and genre.get(r["work_id"]) in ("fiction_narrative", "history_chronicle")),
                  key=lambda r: r["work_id"])  # fmt: skip
    rng = random.Random(derive_seed(f"{cfg['skeleton']['shuffle_seed']}:unrelated:{key}", cfg))
    rng.shuffle(pool)
    f = cfg["semantic"]["null_length_factor"]
    out = []
    for r in pool:
        try:
            n = len(Path(norm_path(r)).read_text(encoding="utf-8", errors="replace").split())
        except OSError:
            continue
        if words / f <= n <= words * f:
            out.append((r["work_id"], str(norm_path(r))))
            if len(out) == cfg["skeleton"]["control_unrelated"]:
                break
    return out


def _vectors(events: dict[str, list[list[str]]], cfg: dict) -> tuple[dict, dict]:
    vec, blk = {}, {}
    for n, ev in events.items():
        flat, bi = _flat(ev)
        vec[n], blk[n] = embed(flat, cfg), bi
    return vec, blk


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def controls(workers: int, procs: int) -> int:
    """The retelling positive controls -> data/semantic/skeleton/controls.json."""
    import pyarrow.parquet as pq

    from metadata.pseudo_biblical import CATALOG
    from ocr_fix.normalize import norm_path
    from reuse.exact import targets

    cfg = load_config()
    thr = json.loads((OUT / "check.json").read_text())["event_match"]
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    tg = targets(cfg)
    texts, plan = {}, {}
    for key, (wid, books, chs) in RETELLINGS.items():
        bible = kjv_range(books, chs)
        rel = f"kjv:{books[0]}-{books[-1]}" + (f":{chs[0]}-{chs[1]}" if chs else "")
        texts[key] = _read(str(norm_path(cat[wid])))
        texts[rel] = bible
        un = unrelated(key, tg[key]["year"], len(bible.split()), cfg)
        print(f"{key}: {len(texts[key].split())} words; {rel} {len(bible.split())}; "
              f"{len(un)} unrelated", flush=True)  # fmt: skip
        for w, p in un:
            texts[w] = _read(p)
        plan[key] = (rel, [w for w, _ in un])
    events = extract_all(texts, cfg, workers)
    if set(events) != set(texts):
        return 1
    vec, blk = _vectors(events, cfg)
    pairs = [(k, o) for k, (rel, un) in plan.items() for o in [rel, *un]]
    res = _compare_many(pairs, vec, blk, thr, cfg, procs)
    s = cfg["skeleton"]
    out: dict = {"event_match": thr, "controls": {}}
    for k, (rel, un) in plan.items():
        r = res[(k, rel)]
        others = sorted(({"id": w, "title": (cat[w]["title"] or "")[:100], **res[(k, w)]}
                         for w in un), key=lambda x: -x["score"])  # fmt: skip
        ok = (r["score"] > max(o["score"] for o in others)
              and (r["order_p"] or 1) <= s["max_order_p"])  # fmt: skip
        out["controls"][k] = {"biblical": rel, **r, "unrelated": others,
                              "rank": 1 + sum(o["score"] >= r["score"] for o in others),
                              "passes": bool(ok) if k != "jasher" else None}  # fmt: skip
        print(f"{k} vs {rel}: score {r['score']:.1f}, matched {r['matched']}, order p "
              f"{r['order_p']}; best unrelated {others[0]['score']:.1f}; passes {ok}")  # fmt: skip
    out["shown_to_work"] = bool(out["controls"]["josephus"]["passes"]
                                and out["controls"]["twelve_patriarchs"]["passes"])  # fmt: skip
    (OUT / "controls.json").write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"shown to work: {out['shown_to_work']} -> {OUT / 'controls.json'}")
    return 0


def bom(workers: int, procs: int) -> int:
    """The Book of Mormon against the named sources and their control groups
    -> data/semantic/skeleton/bom.json."""
    from semantic.search import NAMED, NAPOLEON, control_groups

    cfg = load_config()
    thr = json.loads((OUT / "check.json").read_text())["event_match"]
    groups = control_groups()
    texts = {"bom": bom_text()}
    for members in groups.values():
        for w, (_, path) in members.items():
            texts[w] = _read(path)
    events = extract_all(texts, cfg, workers)
    if set(events) != set(texts):
        return 1
    vec, blk = _vectors(events, cfg)
    pairs = [("bom", w) for members in groups.values() for w in members]
    res = _compare_many(pairs, vec, blk, thr, cfg, procs)
    s = cfg["skeleton"]
    out: dict = {"event_match": thr, "bom_events": len(vec["bom"]), "groups": {}}
    for g, members in groups.items():
        rows = sorted(({"id": w, "title": t[:100], **res[("bom", w)]}
                       for w, (t, _) in members.items()), key=lambda x: -x["score"])  # fmt: skip
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        out["groups"][g] = {"members": len(rows), "ranking": rows}
    out["named"] = {}
    for g, v in out["groups"].items():
        for r in v["ranking"]:
            if r["id"] in [*NAMED, NAPOLEON]:
                out["named"][r["id"]] = {
                    "group": g,
                    "rank": r["rank"],
                    "of": v["members"],
                    "score": r["score"],
                    "matched": r["matched"],
                    "order_p": r["order_p"],
                    "stands_out": r["rank"] == 1 and (r["order_p"] or 1) <= s["max_order_p"],
                }
                print(
                    f"{r['id']}: rank {r['rank']} of {v['members']} ({g}), score "
                    f"{r['score']:.1f}, matched {r['matched']}, order p {r['order_p']}"
                )
    (OUT / "bom.json").write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"-> {OUT / 'bom.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "controls", "bom"):
        c = sub.add_parser(name)
        c.add_argument("--workers", type=int, default=6, help="concurrent model calls")
        c.add_argument("--procs", type=int, default=6, help="alignment processes")
        c.add_argument("--per-hour", type=float, default=0, help="most model calls an hour")
        c.add_argument("--out", default="check.json", help="check: output file name")
    a = ap.parse_args(argv)
    _PACE["per_hour"] = a.per_hour
    if a.cmd == "check":
        return check(a.workers, a.out)
    return {"controls": controls, "bom": bom}[a.cmd](a.workers, a.procs)


if __name__ == "__main__":
    sys.exit(main())
