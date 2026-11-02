import importlib

PACKAGES = [
    "ingest",
    "metadata",
    "ocr_fix",
    "kjv_mask",
    "segment",
    "classic",
    "reuse",
    "semantic",
    "timelocked_lm",
    "alm",
    "dating",
    "style_embed",
    "eval",
    "paper",
]


def test_every_pipeline_package_imports() -> None:
    for name in PACKAGES:
        assert importlib.import_module(name).__doc__
