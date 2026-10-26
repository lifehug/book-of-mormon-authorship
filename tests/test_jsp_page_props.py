import json

import pytest

from ingest import jsp


def _page(summary: dict) -> str:
    data = {"props": {"pageProps": {"summary": summary, "tableOfContents": []}}}
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'


def test_transcript_page_parses():
    assert jsp.page_props(_page({"clearText": "<p>x</p>"}))["summary"]["clearText"]


def test_outage_page_is_transient_not_saved():
    with pytest.raises(jsp.TransientError):
        jsp.page_props(_page({"status": 500, "error": True}))
