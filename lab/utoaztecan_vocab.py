"""BOM-117: their way from Stubbs's *Uto-Aztecan: A Comparative Vocabulary*.

The owner bought the book (2011; the copy held is the revised online edition (c) 2020, printed
page N = PDF page N + 5). It is his mainstream comparative vocabulary of the family: about 2,700
numbered sets, each a Proto-Uto-Aztecan (PUA) headword with its reflexes, and the PUA
correspondence tables (Table 6, p. 11). It has no Semitic or Egyptian comparisons; his 2015 book
cites its sets as "UACV-n". The card section "Their way from the Comparative Vocabulary
(2026-11-23)" in ``data/private/lab/owner/2026-11-22-uto-aztecan-redesign/card.md`` was written
and pushed before this ran; settings are ``lab.utoaztecan.vocabulary`` in the config.

1. Bridge: which vocabulary sets the 2015 sets cite, and in how many branches each is attested.
2. The 2026-11-22 sample of 150 sets rechecked with the vocabulary's own reconstruction.
3. His 2015 rules (Appendix A) between his PUA reconstructions and meaning-matched words of
   Hebrew, Arabic, Coptic and eight never-met lists: does a meaning-matched pair pass the rules
   more often than a shuffled one, and more for Semitic than for the controls?

Run as ``python -m lab.utoaztecan vocabulary``. Public output holds set numbers, language codes
and counts only; forms and glosses stay in the private card folder.
"""

from __future__ import annotations

import functools
import json
import re
import subprocess
import unicodedata
from collections import Counter

import numpy as np

from lab import utoaztecan as ua
from lab.paths import NOTES, out

VOCAB_PDF = NOTES / "sources" / "papers" / "stubbs2011_uto_aztecan_vocabulary.pdf"
VOCAB_TXT = ua.PRIV / "stubbs_vocabulary_2020.txt"
OUT_JSON = ua.OUT / "vocabulary.json"


def vocabulary_text() -> list[str]:
    """The private plain text of the vocabulary (made from the PDF on first use)."""
    if not VOCAB_TXT.exists():
        subprocess.run(["pdftotext", "-layout", str(VOCAB_PDF), str(out(VOCAB_TXT))], check=True)
    return VOCAB_TXT.read_text(encoding="utf-8").replace("\f", "").split("\n")


_VHEAD = re.compile(r"^\s{0,8}(\d{1,4})[a-z]?\. +(\S.*)$")
_STAR = re.compile(r"\*[^\s‘'’,;:]+")
_GLOSS = re.compile(r"[‘'](.+?)[’']")


def parse_vocabulary(lines: list[str]) -> dict[int, dict]:
    """Numbered sets of Part Three: number -> {form, gloss, body}. Numbers must run in order."""
    try:
        start = ua._find(lines, r"^\s*PART THREE: THE COMPARATIVE VOCABULARY\s*$", 200)
    except StopIteration:
        start = 0
    try:
        end = ua._find(lines, r"^\s*A UTO-AZTECAN BIBLIOGRAPHY", start)
    except StopIteration:
        end = len(lines)
    heads, last = [], 0
    for i in range(start, end):
        m = _VHEAD.match(lines[i])
        if m and last < int(m.group(1)) <= last + 5:
            last = int(m.group(1))
            heads.append((i, last))
    sets: dict[int, dict] = {}
    for j, (i, num) in enumerate(heads):
        if num in sets:
            continue
        stop = heads[j + 1][0] if j + 1 < len(heads) else end
        head = _VHEAD.match(lines[i]).group(2)
        before_gloss = _GLOSS.split(head, maxsplit=1)[0]
        star = _STAR.search(before_gloss)
        gloss = _GLOSS.search(head)
        sets[num] = {
            "set": num,
            "form": star.group(0) if star else None,
            "gloss": gloss.group(1) if gloss else None,
            "body": "\n".join(lines[i:stop]),
        }
    return sets


def branches_of(body: str, branches: dict[str, list[str]]) -> set[str]:
    """Branches whose languages are cited in a set (an abbreviation followed by a form)."""
    lang_branch = {lang: b for b, langs in branches.items() for lang in langs}
    alt = "|".join(sorted(map(re.escape, lang_branch), key=len, reverse=True))
    rx = re.compile(rf"(?<![\w.\-/])({alt})(?:\([A-Za-z]+\))?\s+(?=\S)")
    return {lang_branch[m.group(1)] for m in rx.finditer(body)}


def uacv_cited(body: str) -> list[int]:
    """UACV set numbers a 2015 set cites, in order, without repeats."""
    seen: list[int] = []
    for n in re.findall(r"UACV-(\d+)", body):
        if int(n) not in seen:
            seen.append(int(n))
    return seen


def _norm(form: str | None) -> str:
    f = (form or "").lstrip("*").split("/")[0].strip()
    f = "".join(c for c in unicodedata.normalize("NFD", f) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w’']", "", f.lower())


def outputs_outside(table: dict, inventory: list[str]) -> dict[str, list[str]]:
    """Appendix A outputs (per stratum) that are not among his own PUA consonants.

    His PUA liquid *L covers l and r ("whether r or l or both is yet unclear", p. 11); ø is loss.
    """
    inv = {"l" if s == "L" else s for s in inventory} | {"r", "ø"}
    res = {}
    for stratum, column in table.items():
        outs = {s for refl in column.values() for w in refl.values() for s in w}
        res[stratum] = sorted(outs - inv)
    return res


# ---------------------------------------------------------------------------------------------
# Step 3: his rules on meaning-matched words


_MODS = set("ːˑʰʲʷˀ͈̪̻̞̃̚ʼ̥̩̯")


def ipa_symbols(segments: str, mapping: dict[str, str]) -> list[str] | None:
    """Consonants of an IPA segment string as his Semitic symbols; None if one is unmapped."""
    syms: list[str] = []
    for seg in segments.split():
        if seg in ("+", "_", "#"):
            continue
        seg = seg.split("/")[-1]
        if ua.ipa_class(seg) == "V":
            continue
        base = "".join(c for c in unicodedata.normalize("NFD", seg) if c not in _MODS)
        base = unicodedata.normalize("NFC", base)
        sym = mapping.get(base) or mapping.get(base[:2]) or mapping.get(base[:1])
        if sym is None:
            return None
        syms.append(sym)
    return syms


def word_lists(spec: str, data: ua.Data, mapping: dict[str, str]) -> dict[str, list[str]]:
    """One word per Concepticon meaning, as his symbols (first usable form in dataset order)."""
    src, _, lang = spec.partition(":")
    if src in ("oshl", "cdo"):
        return {cid: e["symbols"] for cid, e in data.lexicon_map(src).items()}
    if src == "nel":
        forms, params = data.nel()
        drop = None
    elif src == "wold":
        forms, params, _ = data.wold()
        loans = set(data.cfg["lab"]["utoaztecan"]["loan_values"])
        drop = lambda r: r.get("Borrowed") in loans  # noqa: E731
    else:
        raise KeyError(src)
    res: dict[str, list[str]] = {}
    for r in forms:
        if r["Language_ID"] != lang or r["Parameter_ID"] not in params:
            continue
        cid = params[r["Parameter_ID"]]
        if cid in res or (drop and drop(r)):
            continue
        syms = ipa_symbols(r.get("Segments") or "", mapping)
        if syms:
            res[cid] = syms
    return res


@functools.cache
def _obeys_cached(rows: tuple, uas: tuple, column_key: str) -> bool:
    return ua.obeys(list(rows), list(uas), _COLUMNS[column_key])


_COLUMNS: dict[str, dict] = {}


def passes(symbols: list[str], ua_syms: list[str], columns: list[str], table: dict,
           max_positions: int) -> bool:  # fmt: skip
    """His rule check under any of ``columns``: a column that cannot read a consonant fails."""
    for col in columns:
        key = str(id(table[col]))  # the stored reference keeps this id unique
        _COLUMNS.setdefault(key, table[col])
        rows = [ua.table_row(s, table[col]) for s in symbols][:max_positions]
        if None in rows:
            continue
        if _obeys_cached(tuple(rows), tuple(ua_syms), key):
            return True
    return False


def shuffle_excess(m: np.ndarray, shuffles: int, rng: np.random.Generator) -> dict:
    """Real rate = mean of the diagonal; null = the words shuffled among the pairs."""
    n = m.shape[0]
    real = float(np.mean(np.diag(m))) if n else 0.0
    idx = np.arange(n)
    null = np.empty(shuffles)
    for s in range(shuffles):
        null[s] = m[idx, rng.permutation(n)].mean()
    return {
        "pairs": int(n),
        "matches": int(np.trace(m)),
        "rate": round(real, 4),
        "shuffled_mean": round(float(null.mean()), 4),
        "excess": round(real - float(null.mean()), 4),
        "p": round(float((1 + np.sum(null >= real - 1e-12)) / (1 + shuffles)), 5),
    }


def score_list(pairs: list[tuple[int, str, list[str]]], words: dict[str, list[str]],
               columns: list[str], table: dict, v: dict, max_positions: int,
               shuffles: int, seed: int) -> dict:  # fmt: skip
    """Meaning-matched pairs of one list: the match matrix and its shuffle test."""
    rows = [
        (s, cid, syms) for s, cid, syms in pairs if len(words.get(cid, [])) >= v["min_consonants"]
    ]
    m = np.zeros((len(rows), len(rows)), dtype=bool)
    for i, (_, _, uas) in enumerate(rows):
        for j, (_, cid, _) in enumerate(rows):
            m[i, j] = passes(words[cid], uas, columns, table, max_positions)
    res = shuffle_excess(m, shuffles, np.random.default_rng(seed))
    res["matched_sets"] = sorted({rows[i][0] for i in range(len(rows)) if m[i, i]})
    return res


def verdict(primary: dict, controls: dict[str, dict], alpha: float) -> str:
    top = max((c["excess"] for c in controls.values()), default=float("-inf"))
    if primary["p"] < alpha and primary["excess"] > top:
        return "his rules pick it out"
    return "his rules find look-alikes in never-met languages as often"


# ---------------------------------------------------------------------------------------------


def run(cfg: dict) -> tuple[dict, list[dict]]:
    u = cfg["lab"]["utoaztecan"]
    v = u["vocabulary"]
    vocab = parse_vocabulary(vocabulary_text())
    lines15 = ua.stubbs_text()
    sets15 = ua.parse_sets(lines15)
    table = ua.parse_table(lines15)

    # 1. Bridge
    branch_n = {n: len(branches_of(s["body"], v["branches"])) for n, s in vocab.items()}
    cites = {n: uacv_cited("\n".join(s["lines"])) for n, s in sets15.items()}
    cited = sorted({c for cs in cites.values() for c in cs})
    cited_in_vocab = [c for c in cited if c in vocab]

    def one_branch_share(nums):
        xs = [branch_n[n] for n in nums if n in branch_n]
        return {
            "sets": len(xs),
            "one_branch": sum(x == 1 for x in xs),
            "share_one_branch": round(sum(x == 1 for x in xs) / len(xs), 3) if xs else None,
            "no_branch_read": sum(x == 0 for x in xs),
            "median_branches": float(np.median(xs)) if xs else None,
        }

    heads_init = Counter(
        (_norm(s["form"])[:1] if s["form"] else "") for s in vocab.values() if s["form"]
    )
    bridge = {
        "vocabulary_sets_found": len(vocab),
        "vocabulary_last_number": max(vocab) if vocab else None,
        "vocabulary_with_starred_headword": sum(bool(s["form"]) for s in vocab.values()),
        "sets_2015": len(sets15),
        "sets_2015_citing_uacv": sum(bool(c) for c in cites.values()),
        "uacv_numbers_cited": len(cited),
        "uacv_numbers_cited_found_in_vocabulary": len(cited_in_vocab),
        "branches_all_vocabulary": one_branch_share(list(vocab)),
        "branches_cited_by_2015": one_branch_share(cited_in_vocab),
        "headwords_with_initial_liquid": sum(heads_init[c] for c in "lr"),
        "appendix_a_outputs_not_in_his_pua_consonants": outputs_outside(table, v["pua_consonants"]),
    }

    # 2. The 150-set sample with his own reconstruction
    sample_path = ua.PRIV / "his_way_sample.jsonl"
    records = [json.loads(x) for x in sample_path.read_text(encoding="utf-8").splitlines() if x]
    private, per_set = [], []
    for r in records:
        if not r.get("machine_readable"):
            continue
        c = cites.get(r["set"], [])
        vform = vocab[c[0]]["form"] if c and c[0] in vocab else None
        col = table.get(r["stratum"] or "", {})
        obeys_v = ua.obeys(r["ne_rows"], ua.ua_symbols(vform), col) if vform and col else None
        same = bool(vform) and _norm(vform) == _norm(r["ua"])
        per_set.append(
            {
                "set": r["set"],
                "uacv": c[0] if c else None,
                "obeys_2015_form": r["obeys_table"],
                "obeys_vocabulary_form": obeys_v,
                "same_form": same,
            }
        )
        private.append({**per_set[-1], "form_2015": r["ua"], "form_vocabulary": vform})
    with_v = [p for p in per_set if p["obeys_vocabulary_form"] is not None]
    sample = {
        "readable_sets": len(per_set),
        "obey_with_2015_form": sum(p["obeys_2015_form"] for p in per_set),
        "cite_a_uacv_set": sum(p["uacv"] is not None for p in per_set),
        "with_vocabulary_form": len(with_v),
        "obey_with_vocabulary_form": sum(p["obeys_vocabulary_form"] for p in with_v),
        "obey_with_2015_form_same_sets": sum(p["obeys_2015_form"] for p in with_v),
        "same_form_as_vocabulary": sum(p["same_form"] for p in per_set),
        "per_set": per_set,
    }

    # 3. His rules on meaning-matched words
    data = ua.Data(cfg)
    pairs = []
    for n, s in sorted(vocab.items()):
        if not s["form"] or not s["gloss"]:
            continue
        syms = ua.ua_symbols(s["form"])
        if not syms:
            continue
        for cid in {
            data.concept_keys[k] for k in ua.gloss_keys(s["gloss"]) if k in data.concept_keys
        }:
            pairs.append((n, cid, syms))
    lists = load_lists(v, data)
    scores = score_blocks(pairs, lists, table, cfg, "vocab")
    test = {
        "vocabulary_pairs": len(pairs),
        "vocabulary_sets_paired": len({p[0] for p in pairs}),
        "meanings_paired": len({p[1] for p in pairs}),
        "scores": scores,
        "missing": data.missing,
    }
    return {"bridge": bridge, "sample": sample, "rules_on_meaning_matched_words": test}, private


def load_lists(v: dict, data: ua.Data) -> dict[str, dict | None]:
    """Every list of the card (Semitic, Egyptian, controls) as his symbols; None if missing."""
    lists: dict[str, dict | None] = {}
    for spec in v["semitic_lists"] + v["egyptian_lists"] + v["control_lists"]:
        try:
            lists[spec] = word_lists(spec, data, v["ipa_symbols"])
        except (OSError, KeyError) as exc:
            lists[spec] = None
            data.missing.append(f"{spec}: {type(exc).__name__}")
    return lists


def score_blocks(pairs, lists: dict, table: dict, cfg: dict, tag: str) -> dict[str, dict]:
    """Semitic and Egyptian rules over every list, with the card's verdict per block."""
    u = cfg["lab"]["utoaztecan"]
    v = u["vocabulary"]
    maxpos = u["his_way"]["max_positions"]
    scores: dict[str, dict] = {}
    for rules, columns, targets in (
        ("semitic", v["semitic_columns"], v["semitic_lists"]),
        ("egyptian", v["egyptian_columns"], v["egyptian_lists"]),
    ):
        block: dict = {}
        for spec in targets + v["control_lists"]:
            if lists.get(spec) is None:
                block[spec] = {"state": "not attempted (list missing)"}
                continue
            block[spec] = score_list(pairs, lists[spec], columns, table, v, maxpos,
                                     u["shuffles"], ua._seed(tag, rules, spec))  # fmt: skip
            block[spec]["meanings_in_list"] = len(lists[spec])
        ctrl = {k: block[k] for k in v["control_lists"] if "excess" in block[k]}
        prim = block[targets[0]]
        block["verdict"] = verdict(prim, ctrl, u["alpha"]) if "excess" in prim else "not attempted"
        block["verdict_each"] = {
            k: verdict(block[k], ctrl, u["alpha"]) for k in targets if "excess" in block[k]
        }
        block["controls_below_alpha"] = sorted(k for k, c in ctrl.items() if c["p"] < u["alpha"])
        block["largest_control_excess"] = max((c["excess"] for c in ctrl.values()), default=None)
        scores[rules] = block
    return scores


def one_pair_per_meaning(
    vocab: dict[int, dict],
    branch_n: dict[int, int],
    concept_keys: dict[str, str],
    min_branches: int,
) -> list[tuple]:
    """One (set, meaning, UA symbols) per meaning: multi-branch sets only; the set in the most
    branches stands for the meaning, ties to the lowest number. Chosen before any list is read."""
    best: dict[str, tuple] = {}
    for n, s in sorted(vocab.items()):
        if branch_n.get(n, 0) < min_branches or not s["form"] or not s["gloss"]:
            continue
        syms = ua.ua_symbols(s["form"])
        if not syms:
            continue
        for cid in {concept_keys[k] for k in ua.gloss_keys(s["gloss"]) if k in concept_keys}:
            key = (-branch_n[n], n)
            if cid not in best or key < best[cid][0]:
                best[cid] = (key, (n, cid, syms))
    return [best[c][1] for c in sorted(best, key=ua._mkey)]


def merged(symbols: list[str], merge: dict[str, str], k: int) -> tuple[str, ...]:
    """First ``k`` consonants with Modern Hebrew's mergers applied (š kept apart from s)."""
    return tuple(merge.get(x, x) for x in symbols[:k])


def biblical_era(word: list[str], meaning: str, entries: list[dict], merge: dict[str, str],
                 k: int) -> bool:  # fmt: skip
    """A Strong's entry with the same merged first consonants and a gloss sharing a content
    word with the meaning's name."""
    target = merged(word, merge, k)
    want = ua.content_words(meaning)
    for e in entries:
        if merged(e["symbols"], merge, k) != target:
            continue
        if any(ua.content_words(g) & want for g in e["glosses"]):
            return True
    return False


def rerun(cfg: dict) -> dict:
    """The stated rerun: multi-branch sets, one pair per meaning; the Modern Hebrew decision."""
    u = cfg["lab"]["utoaztecan"]
    v = u["vocabulary"]
    r = v["rerun"]
    vocab = parse_vocabulary(vocabulary_text())
    table = ua.parse_table(ua.stubbs_text())
    branch_n = {n: len(branches_of(s["body"], v["branches"])) for n, s in vocab.items()}
    data = ua.Data(cfg)
    pairs = one_pair_per_meaning(vocab, branch_n, data.concept_keys, r["min_branches"])
    lists = load_lists(v, data)
    scores = score_blocks(pairs, lists, table, cfg, "vocab-rerun")
    sem = scores["semitic"]
    lead = sem.get(r["lead"], {})
    ctrl = {k: sem[k] for k in v["control_lists"] if "excess" in sem[k]}
    holds = None
    if "excess" in lead:
        holds = verdict(lead, ctrl, u["alpha"]) == "his rules pick it out"
    check: dict = {"state": "not attempted"}
    if lists.get(r["lead"]) and "matched_sets" in lead:
        entries = ua.strong_entries()
        by_set = {}
        for n, cid, _ in pairs:
            by_set.setdefault(n, []).append(cid)
        era = Counter()
        for n in lead["matched_sets"]:
            for cid in by_set[n]:
                word = lists[r["lead"]].get(cid)
                if not word or len(word) < v["min_consonants"]:
                    continue
                name = data.concept_names.get(cid, "")
                k = min(len(word), u["his_way"]["max_positions"])
                era["biblical_era" if biblical_era(word, name, entries, r["modern_merge"], k)
                    else "not_found_in_strongs"] += 1  # fmt: skip
        check = dict(era)
    return {
        "pairs": len(pairs),
        "sets_used": len({p[0] for p in pairs}),
        "multi_branch_sets": sum(x >= r["min_branches"] for x in branch_n.values()),
        "scores": scores,
        "modern_hebrew_holds": holds,
        "modern_hebrew_matches_biblical_era_check": check,
        "missing": data.missing,
    }


def main_rerun() -> int:
    from metadata import config

    cfg = config.load()
    res = rerun(cfg)
    res["source"] = (
        "Stubbs, Uto-Aztecan: A Comparative Vocabulary (2011), revised online edition (c) 2020"
    )
    res["settings"] = cfg["lab"]["utoaztecan"]["vocabulary"]["rerun"]
    out(ua.OUT / "vocabulary_rerun.json").write_text(
        json.dumps(ua._stamp(res), indent=1, ensure_ascii=False) + "\n"
    )
    brief = {k: x for k, x in res.items() if k not in ("scores", "settings")}
    brief["scores"] = {
        b: {k: _drop_sets(x) for k, x in blk.items()} for b, blk in res["scores"].items()
    }
    print(json.dumps(brief, indent=1, ensure_ascii=False))
    return 0


def _drop_sets(x):
    return {k: v for k, v in x.items() if k != "matched_sets"} if isinstance(x, dict) else x


def main() -> int:
    from metadata import config

    cfg = config.load()
    res, private = run(cfg)
    res["source"] = (
        "Stubbs, Uto-Aztecan: A Comparative Vocabulary (2011), revised online edition (c) 2020"
    )
    res["settings"] = cfg["lab"]["utoaztecan"]["vocabulary"]
    rows = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in private)
    out(ua.PRIV / "vocabulary_sample.jsonl").write_text(rows, encoding="utf-8")
    out(OUT_JSON).write_text(json.dumps(ua._stamp(res), indent=1, ensure_ascii=False) + "\n")
    brief = {k: v for k, v in res["bridge"].items()}
    brief["sample"] = {k: v for k, v in res["sample"].items() if k != "per_set"}
    sc = res["rules_on_meaning_matched_words"]["scores"]
    brief["scores"] = {r: {k: _drop_sets(x) for k, x in b.items()} for r, b in sc.items()}
    print(json.dumps(brief, indent=1, ensure_ascii=False))
    return 0
