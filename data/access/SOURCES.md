# Access evidence index (BOM-33)

| File | Built by | What |
| --- | --- | --- |
| `wayne_sentinel_access.jsonl` | `python -m ingest.access_index build data/newspapers/wayne_sentinel --name wayne_sentinel` (2026-10-21) | 4,831 OCR-derived hits over 1,429 pages: date, page id, term group, matched term, raw snippet |
| `wayne_sentinel_verified.jsonl` | human reading of page scans (2026-10-21) | items confirmed by eye on the image. Separate file on purpose: these are *not* OCR-derived and must not be mixed into recall or precision figures for the index |

**The ceiling:** this records what was *demonstrably available in the area*, never that any
person read it. See `docs/access-evidence.md`, which states the limit and must be read with the
data.

**The index cannot support negative findings on this source.** The 26 June 1829 page carries the
Book of Mormon title page in clear print, and the OCR of that page returns zero for all ten
diagnostic terms — `Golden Bible` survives extraction as `gattlmbible`. The OCR hits are a
floor, not a census. Any claim about what a paper did *not* print must be made against page
images. Full reasoning in `docs/access-evidence.md`.

Matching squeezes whitespace and punctuation out of each page so NYSHN's fragmented OCR
(`t h e b o o k`) still matches. That trades word boundaries for recall, so every row carries
its snippet and the file is meant to be read, not counted.
