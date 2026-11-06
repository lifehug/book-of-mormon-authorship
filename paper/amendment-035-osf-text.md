# Amendment 35: manuscript evidence and 6.3's comparison (BOM-34)

*Filed 2026-11-06. Evidence: `docs/manuscript-evidence.md`, `manuscript/corrections.py`,
`eval/scribes.py`.*

---

**Amendment 35, filed 2026-11-06, before 6.3's narrator, scribe and dictation-order comparison is run.**
Section 6.3 names the comparison without fixing its measure; BOM-34 adds a correction catalog of
the manuscripts. Decision rules are unchanged.

**Correction catalog** (descriptive; no hypothesis rests on it). Every correction the Joseph Smith
Papers transcripts mark in the original and printer's manuscripts is typed automatically
(substitution, false start, deletion, insertion; a one-word substitution as a listed homophone,
same Soundex code, close spelling, or other). Primary contrast: homophone substitutions as a share
of substitutions, original against printer's, on all pages, on the same passages, and with the
scribe (Oliver Cowdery) held fixed; Fisher's exact test.

**6.3's measure.** Each segmentation's whole 2,000-word chunks (narrator; scribe without
non-extant text; dictation order), labels with at least 3 chunks, classified by leave-one-out
nearest centroid under Cosine Delta on the middle registered MFW count (vocabulary, culling and
z-scores from the other chunks only). The benchmark accuracy is Cosine Delta's at 2,000 words in the
power analysis, averaged over the benchmark corpora. Narrators are separable if their accuracy
reaches it and neither other segmentation is more accurate (6.3 as worded); label-permutation
nulls (1,000, seeded) and chance-corrected accuracies are reported beside it, since the
segmentations have different numbers of labels.
