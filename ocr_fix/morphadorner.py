"""Run MorphAdorner's Early Modern English adorner on the pre-1700 texts (BOM-15).

4.3 registers MorphAdorner EME for text printed before 1700. MorphAdorner does not apply its
spelling table blind: it tags parts of speech first, and a word-class table settles the
ambiguous forms (``part`` as a noun stays, as an adverb becomes ``partly``; ``ye`` is ``the``
as a determiner and ``you`` as a pronoun). An earlier version of ``ocr_fix.normalize`` applied
the merged pairs table token by token without tagging, which got exactly those words wrong
(about a million nouns ``part`` became ``partly``). This runs the real thing, unchanged:
MorphAdorner 2.0.1's ``adornplainemetext`` configuration from the distributed zip, under the
local Java 17 that passim already uses.

Its tabular output -- token, spelling, part of speech, standard spelling, lemma, end of
sentence -- is kept whole in ``data/corpus/morphadorner_adorned/<id>.txt`` (the tags may serve
later stages), and ``rebuild`` puts the standard spellings back into the original text so its
lines and paragraphs survive. MorphAdorner's standard spellings are applied as produced, with
three exceptions Amendment 6 registers (``spelling_normalization.morphadorner_keep_printed``):
it maps the article ``an`` to ``and``, ``whether`` to ``whither`` and ``fall`` to ``fallen``,
replacing a word rather than a spelling, so those keep their printed form. The adorned output
itself is kept unaltered.

Usage::

    python -m ocr_fix.morphadorner adorn [--jobs 4] [--batch 100]   # resumable
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import load as load_config

APP = Path("data/corpus/morphadorner/app")
OUT = Path("data/corpus/morphadorner_adorned")
SCRATCH = Path("data/corpus/morphadorner_tmp")  # per-batch output; a killed run leaves it here
CATALOG = Path("data/catalog/catalog.parquet")
JAVA = Path(os.environ.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17")) / "bin" / "java"
HEAP = "2g"
# the arguments of the distributed adornplainemetext script
ARGS = [
    "edu.northwestern.at.morphadorner.MorphAdorner",
    "-p", "emeplaintext.properties",
    "-l", "data/emelexicon.lex",
    "-t", "data/emetransmat.mat",
    "-u", "data/emesuffixlexicon.lex",
    "-a", "data/ememergedspellingpairs.tab",
    "-s", "data/standardspellings.txt",
    "-w", "data/spellingsbywordclass.txt",
]  # fmt: skip
SEARCH = 200  # characters ahead in which an adorned token must be found in the original
_LETTER = re.compile(r"[^\W\d_]")
# a word of the original: a whitespace-delimited chunk holding a letter (combining marks, as in
# the macron of "ſon̄es", would split a letters-only pattern)
_WORDS = re.compile(r"\S*[^\W\d_]\S*")


def adorned_path(row: dict) -> Path:
    return OUT / Path(row["text_path"]).name


def read_adorned(path: Path) -> list[tuple[str, str]]:
    """(token, standard spelling) for every adorned word."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) >= 4:
            out.append((cols[0], cols[3]))
    return out


def _inside_word(text: str, at: int, token: str) -> bool:
    """True if a match at ``at`` would cut a word: a letter edge of the token touches a letter."""
    end = at + len(token)
    before = token[0].isalpha() and at > 0 and text[at - 1].isalpha()
    after = token[-1].isalpha() and end < len(text) and text[end].isalpha()
    return before or after


CONFIRM = 3  # word tokens that must follow a resynchronising match directly


def _find(text: str, pos: int, token: str, skip: int, window: int, start: int = -1) -> int:
    """First match of ``token`` after ``start`` that skips at most ``skip`` words of text."""
    at = max(pos, start + 1)
    while True:
        at = text.find(token, at, pos + window + len(token))
        if at < 0 or len(_WORDS.findall(text, pos, at)) > skip:
            return -1
        if not _inside_word(text, at, token):
            return at
        at += 1


def _confirmed(text: str, pos: int, following: list[tuple[str, str]]) -> bool:
    for token, _ in following:
        at = _find(text, pos, token, 0, SEARCH)
        if at < 0:
            return False
        pos = at + len(token)
    return True


def rebuild(
    text: str, words: list[tuple[str, str]], keep: frozenset[str] = frozenset()
) -> tuple[str, Counter, int]:
    """Replace each token in ``text`` by its standard spelling, keeping everything between.

    Only tokens with a letter are aligned: punctuation and numbers are never respelled, and
    MorphAdorner joins some of them (``. .`` across a line break becomes ``..``), which once
    sent the search to a later ``..`` and from there drifted it to the end of the text. A token
    is accepted only if the text skipped to reach it holds no more words than the tokens missed
    since the last match; after a miss, a match must also be followed directly by the next
    ``CONFIRM`` tokens, or a common word further on (where a word broken by a TCP gap marker
    had stalled it) would pull the search ahead. Returns the text, the replacements made as
    (lowercase token, lowercase standard) counts, and the number of word tokens not found.
    Tokens whose lowercase form is in ``keep`` keep their printed form.
    """
    parts: list[str] = []
    applied: Counter = Counter()
    pos = missed = behind = 0
    words = [w for w in words if _LETTER.search(w[0])]
    for i, (token, standard) in enumerate(words):
        window = SEARCH * (1 + behind)
        at = _find(text, pos, token, behind, window)
        if behind:
            following = words[i + 1 : i + 1 + CONFIRM]
            while at >= 0 and not _confirmed(text, at + len(token), following):
                at = _find(text, pos, token, behind, window, at)
        if at < 0:
            missed += 1
            behind += 1
            continue
        behind = 0
        parts.append(text[pos:at])
        if standard and standard.lower() != token.lower() and token.lower() not in keep:
            parts.append(standard)
            applied[token.lower(), standard.lower()] += 1
        else:
            parts.append(token)
        pos = at + len(token)
    parts.append(text[pos:])
    return "".join(parts), applied, missed


def _rows() -> list[dict]:
    from ocr_fix.normalize import regime

    cfg = load_config()
    pre = cfg["corpus"]["spelling_normalization"]["pre_1700"]
    return [
        r
        for r in pq.read_table(
            CATALOG, columns=["work_id", "source", "year", "text_path"]
        ).to_pylist()
        if r["text_path"] and r["source"] == "tcp" and regime(r["year"], cfg) == pre
    ]


def _adorn_batch(paths: list[str]) -> tuple[int, str]:
    """One JVM over a batch; outputs land in a scratch dir and move into place per file."""
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        files = [str(Path(p).resolve()) for p in paths]
        cmd = [str(JAVA), f"-Xmx{HEAP}", "-Xss1m", "-cp", ".:bin/:dist/*:lib/*", *ARGS,
               "-o", str(Path(tmp).resolve()), *files]  # fmt: skip
        r = subprocess.run(cmd, cwd=APP, capture_output=True, text=True)
        done = 0
        for p in paths:
            got = Path(tmp) / Path(p).name
            if got.exists() and got.stat().st_size:
                shutil.move(got, OUT / Path(p).name)
                done += 1
        err = "" if r.returncode == 0 else r.stderr[-500:]
        return done, err


def adorn(jobs: int, batch: int) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    rows = _rows()
    todo = [r["text_path"] for r in rows if not adorned_path(r).exists()]
    # largest first, so the long tail is short files
    todo.sort(key=lambda p: -Path(p).stat().st_size)
    batches = [todo[i : i + batch] for i in range(0, len(todo), batch)]
    print(f"{len(rows):,} pre-1700 texts, {len(todo):,} to adorn in {len(batches):,} batches")
    start, done, failed = time.time(), 0, 0
    with ThreadPoolExecutor(jobs) as pool:
        futs = [pool.submit(_adorn_batch, b) for b in batches]
        for i, f in enumerate(as_completed(futs), 1):
            n, err = f.result()
            done += n
            if err:
                failed += 1
                print(f"  batch error (files not written are retried next run): {err}", flush=True)
            if i % 10 == 0 or i == len(batches):
                el = time.time() - start
                print(f"  {i}/{len(batches)} batches, {done:,} texts, {el / 60:.0f}m", flush=True)
    left = sum(1 for r in rows if not adorned_path(r).exists())
    print(f"adorned {done:,}; {left:,} still missing; {failed} batches reported errors")
    return 0 if not left else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("adorn")
    a.add_argument("--jobs", type=int, default=4)
    a.add_argument("--batch", type=int, default=100)
    args = ap.parse_args(argv)
    if args.cmd == "adorn":
        return adorn(args.jobs, args.batch)
    return 1


if __name__ == "__main__":
    sys.exit(main())
