"""4.2's contamination check (BOM-18 pools, BOM-27 training sets)."""

import json
from pathlib import Path

from metadata.sealed import contaminated

ROWS = [json.loads(ln) for ln in Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines()]


def test_a_12_token_extract_is_caught() -> None:
    body = next(r["text"] for r in ROWS if r["kind"] == "body" and len(r["text"].split()) > 40)
    extract = " ".join(body.split()[5:18])
    assert contaminated(f"An unrelated preface. {extract} And so the essay goes on.")


def test_short_overlap_is_not() -> None:
    assert not contaminated("And it came to pass that the people did go forth into the field.")
