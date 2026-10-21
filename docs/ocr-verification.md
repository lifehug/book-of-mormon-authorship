# Is the corpus OCR good enough? (BOM-14, BOM-50)

Verified 2026-10-21 against page images, which is the only way to answer it. The question arose
because the *Wayne Sentinel* access index returned zero hits on a page later confirmed by eye to
carry the Book of Mormon title page in clear print. If the same were true of Chronicling America,
every OCR figure in this project would be resting on nothing — Chronicling America is the
reference the BOM-14 proxy is calibrated against.

## Method

Fetch the page image, read it, pick phrases plainly visible in print, and search the OCR we hold
for them. Phrases are chosen from the image *before* looking at the text, so the test cannot be
tuned. Matching squeezes whitespace and punctuation, so a hit does not depend on spacing.

Images come from the IIIF service at `tile.loc.gov/image-services/iiif/...`, which answers
normally. The legacy `chroniclingamerica.loc.gov` paths 308-redirect and the PDF/JP2 derivatives
return a Cloudflare challenge, but IIIF and the ALTO XML under `storage-services` do not. Page
URLs are resolved through `www.loc.gov/item/<lccn>/<date>/ed-N/?fo=json`. Serial requests only.

## Result

| Page | Quality in our score | Exact phrase matches | Present at all |
| --- | --- | --- | --- |
| `sn87062070` 1830-03-31 seq-1 | typical | 8 / 10 | 10 / 10 |
| `sn84024710` 1809-04-14 seq-2 | **worst of 5,000 sampled** (lexicon 0.488) | 15 / 16 | 16 / 16 |
| *Wayne Sentinel* 1829-06-26 p3 | — | **0 / 10** | 0 / 10 |

Every Chronicling America miss is a single character:

    ...olonists either lied from europe like our new england ancestor to avoid...
                       ^^^^ "fled"                                   ^ "ancestors"

    ...havingpushedforwardthe95ehriecorpsand1stbattal...
                              ^^^^ "95th (rifle corps)"

The *Wayne Sentinel* is a different regime entirely. There, `Golden Bible` survives as
`gattlmbible` — not a character substitution but destruction, and nothing in the surrounding
text would let a reader rebuild it.

**Chronicling America's OCR is good enough.** Errors are single-character substitutions and
dropped letters, recoverable from context. Even the worst page in a 5,000-page sample reads
almost cleanly.

## Correcting an earlier conclusion in this repository

Before the images were available, this project measured OCR confidence from the NDNP ALTO and
found a mean word confidence of 0.493, with 53.2% of words below 0.50, and recorded in
`data/ocr_quality/SOURCES.md` that "the reference is a low bar".

The image test shows that reading was wrong. A corpus whose worst sampled page returns 15 of 16
phrases verbatim is not a low bar. **ALTO `WC` badly understates real phrase-level recall** and
must not be used as a proxy for it. It remains useful for *ranking* pages within a source, which
is what preregistration 4.3 asks for, but a `WC` figure may not be reported as a quality verdict.
That correction is applied in `data/ocr_quality/SOURCES.md`.

## What this means for each stage

| Stage | Verdict |
| --- | --- |
| Q1 attribution, word-frequency features (5.1) | fine. Single-character noise is spread thinly across millions of words and does not move a frequency vector |
| Q3 dating on grammatical features (5.3) | fine for the same reason |
| **Q2 borrowing, rare 4-grams (5.5)** | **degraded but safe.** One bad character kills a 4-gram, so `95th` → `95eh` removes every 4-gram containing it. The effect is lost matches, not invented ones — false negatives, never false positives. Real borrowing will be under-detected by some margin, and that margin should be estimated and published rather than assumed small |
| Access evidence on NYSHN titles (BOM-33) | **not usable.** Needs re-OCR from images before any term-level claim |

## Does anything need re-OCR?

No, for Chronicling America. Not even correction is required for the aggregate stylometry; an
LLM correction pass is still worth measuring for 5.5, where character-level accuracy converts
directly into recall.

Yes, for the *Wayne Sentinel* and anything else from NYS Historic Newspapers, if it is to support
term-level or phrase-level claims. 1,429 pages is a tractable re-OCR job against the page images,
unlike a blanket pass over 158,960.
