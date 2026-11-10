# ingest/

Download source texts and write raw text plus a manifest per source.

Issues: BOM-05 to BOM-11, BOM-13 (`candidates.py`: candidate author texts from `data/candidates/sources.json`; `signed_items.py`: signed items in the periodical runs; `candidate_words.py`: word counts and samples under the counting rule; inventory and rules in `docs/candidates.md`). BOM-73 (`js_time.py`: the comparison writers for Joseph Smith's prose over time, from `data/js_time/controls.json`; his own documents go through `candidates.py` with `--manifest data/js_time/sources.json`; plan in `docs/js-over-time-plan.md`).
