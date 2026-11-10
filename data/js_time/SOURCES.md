# data/js_time: sources for BOM-73 (Joseph Smith's prose over time)

Plan and attribution rule: `docs/js-over-time-plan.md`; research: `docs/js-over-time-research.md`.

| File | What | Where it came from | How to rebuild |
| --- | --- | --- | --- |
| `sources.json` | 21 Joseph Smith Papers documents of 1833-1844 in his hand or recorded as dictated (ids `t73-`), with tier and date | https://www.josephsmithpapers.org/ paper-summary pages (each entry's `url`); JSP "Documents in Joseph Smith's Handwriting" and each document's source note | hand-built from the JSP source notes; fetch with `python -m ingest.candidates --manifest data/js_time/sources.json` (browser User-Agent, 2.5-7.5 s; owner's decision of 2026-10-25). Transcripts are copyrighted (Intellectual Reserve): private repo `lifehug/bom-authorship-data`, `candidates/t73-*.jsonl`; steps to obtain them in `docs/replication.md` |
| `controls.json` | 158 Internet Archive items, 1831-1844: the unexposed group (*Methodist Magazine and Quarterly Review*, *Evangelical Magazine and Gospel Advocate*, *Religious Intelligencer*: the first issue of each quarter; Finney and Beecher books) and Alexander Campbell's *Millennial Harbinger* (a separate line) | https://archive.org/details/<identifier> (each entry's `url`); issue lists from the Archive's advanced search, years from the issue dates in the identifiers | `python -m ingest.js_time` writes `data/corpus/js_time/text/<id>.txt` (public domain; local, checksummed in `data/manifests/js_time_controls.jsonl`) |
