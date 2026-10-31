"""Result files hold numbers and labels, never corpus text (BOM-58).

On 2026-10-30 ``data/benchmark/repair.json`` was written holding 30 authors' reference texts
(117 MB, including Harvard Institutional Books text, which may never be published) where their
names were meant; GitHub's size limit stopped the push. Results under these directories are
small, so size is a cheap, reliable signal that text has leaked into one.
"""

from pathlib import Path

LIMIT = 2_000_000  # bytes; the largest result today is about 40 KB
DIRS = ("data/benchmark", "data/classic")
SUFFIXES = (".json",)


def test_result_files_are_small() -> None:
    big = [
        (str(p), p.stat().st_size)
        for d in DIRS
        for p in Path(d).rglob("*")
        if p.suffix in SUFFIXES and p.is_file() and p.stat().st_size > LIMIT
    ]
    assert not big, f"result files too large to be numbers and labels (corpus text?): {big}"
