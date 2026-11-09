"""Where each style encoder's files live (no torch, so scorers and the synthesis can import it)."""

from __future__ import annotations

from pathlib import Path

DATA = Path("data/corpus/style_embed")
SIZES = ("base", "mid")  # every size runs every model-based test (Amendment 37); 125M not used


def tag(size: str) -> str:
    """The name an encoder's results go under: ``style`` for the registered 297M encoder (BOM-30),
    ``style_<size>`` for another backbone, so the registered encoder's files never change."""
    return "style" if size == "base" else f"style_{size}"


def run_dir(size: str) -> Path:
    return DATA / "runs" / tag(size)


def bench_name(size: str) -> str:
    """Its benchmark and imitation result file stem."""
    return "style_embed" if size == "base" else f"style_embed_{size}"
