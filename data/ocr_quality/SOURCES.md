# OCR quality scores (BOM-14)

Built by `python -m ocr_fix.score run <text dir> --name <source>`, one row per page. The
Chronicling America row is a seeded random sample (`baseline --sample 5000`, seed 20261017)
serving as the same-era reference. Compare with `python -m ocr_fix.score report`.

**These are proxies, not character error rates.** Pre-registration 4.3 excludes volumes above
`corpus.ocr_max_cer` (0.10), but CER needs hand-corrected pages, which BOM-14 has not yet
produced. Nothing here applies that cutoff; pages are ranked, not excluded.

| Source | Pages | Empty | lexicon median | garbage median | single-letter median |
| --- | --- | --- | --- | --- | --- |
| Chronicling America (reference) | 5,000 | 0 | 0.784 | 0.012 | 0.041 |
| Wayne Sentinel | 1,429 | 9 | 0.800 | 0.009 | 0.300 |
| Lake Light | 168 | 0 | 0.743 | 0.003 | 0.028 |

**Reading this.** On genuine OCR quality all three are comparable, and the Wayne Sentinel is at
or slightly better than the Library of Congress's own OCR of the same era and medium. The
Sentinel's striking number is the single-letter rate, 0.300 against 0.041: NYS Historic
Newspapers' Veridian text view fragments words into lone characters. That is how the page is
delivered, not how well it was read, which is why it is its own metric and deliberately outside
`garbage_rate` — folded in, it made the Sentinel look six times worse than the reference.

**Consequence for later issues.** The fragmentation has to be repaired before any phrase- or
n-gram-level work touches the Sentinel: a 4-gram over `t h e b o o k` is noise. That is a BOM-14
cleaning task, and BOM-23, BOM-24 and BOM-33 all depend on it.

The nine empty Wayne Sentinel pages are the nine listed in
`data/newspapers/wayne_sentinel/SOURCES.md`; the scorer flags them rather than dropping them.

## The reference is itself poor (measured 2026-10-21, BOM-50)

Chronicling America is the baseline every other source here is read against, and it had never
been checked against anything. It has now been, using the producer's own per-word confidence
from the NDNP ALTO. 400 pages from batch `arhi_elvis_ver01`, 1,568,012 words, seed 20261017:

| metric | value |
| --- | --- |
| mean word confidence | 0.493 |
| median | 0.481 |
| p10 / p25 / p75 | 0.222 / 0.333 / 0.611 |
| words below 0.50 | 53.2% |
| words below 0.80 | 92.4% |
| per-page mean, worst / median / best | 0.328 / 0.494 / 0.743 |

**Corrected 2026-10-21, same day, after testing against page images.** The paragraph that stood
here said this made the reference "a low bar". That was wrong, and `docs/ocr-verification.md` has
the evidence: the worst-scoring page in this entire 5,000-page sample returns **15 of 16** phrases
verbatim when checked against its scan, and the only miss is `95th` read as `95eh`. A corpus that
survives that test is not a low bar.

So `WC` badly understates phrase-level recall and **may not be reported as a quality verdict**.
It stays useful for *ranking* pages within a source, which is what 4.3 asks for, but the number
above says much less about usability than it appears to. The lesson is the one this project keeps
relearning: a producer's own confidence metric is not ground truth, and neither is a proxy — only
an image is.

Only one batch could be measured, because the extractor discarded the ALTO for the other 75 and
deleted the tarballs. BOM-50 recovers it.
