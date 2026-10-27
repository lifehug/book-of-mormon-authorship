"""The BOM-17 boundary file: hand-overs land where the 1830 text marks them."""

import json
from pathlib import Path

from segment.boundaries import build

LABELS = {x["seq"]: x for x in build()[1]}


def test_handovers() -> None:
    assert LABELS[1315]["narrator"] == "Mormon"
    assert LABELS[1316]["narrator"] == "Moroni"  # "Behold I, Moroni, do finish the record..."
    assert LABELS[588]["narrator"] == "Amaleki"
    assert LABELS[700]["narrator"] == "Mormon"  # Mosiah: the abridgement
    assert LABELS[1320]["narrator"] == "Moroni"  # Ether


def test_dictation_and_scribe() -> None:
    assert LABELS[700]["dictation_phase"] == "first"
    assert LABELS[200]["dictation_phase"] == "last"
    assert {x["scribe"] for x in LABELS.values() if x["book"] == "Mosiah"} == {"not_extant"}


def test_file_is_current() -> None:
    on_disk = json.loads(Path("data/bom/segments/boundaries.json").read_text())
    assert on_disk == json.loads(json.dumps(build()[0], ensure_ascii=False))
