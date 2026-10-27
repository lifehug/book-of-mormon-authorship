# Datasheet: Book of Mormon authorship corpus, v1.0 (BOM-19)

*Draft, 2026-10-27. Figures marked **[pending]** are filled in when the jobs that produce them
finish; everything else is measured and committed. Structure follows Gebru et al., "Datasheets
for Datasets".*

## Motivation

Built for an open, pre-registered study of the authorship, borrowing and dating of the earliest
Book of Mormon text (https://osf.io/6ugxc/). The study identifies close candidates or their
absence, with the evidence; it takes no position on the book's origin. One person (Dave
Taylor) with AI assistance; every review step that assumed a second person is simulated by an AI
model and labelled as such (Amendment 1).

## Composition

| Part | What | Size | Where |
| --- | --- | --- | --- |
| Catalog | one row per work from five sources, normalised author and date | 695,021 rows, 533,328 with text | `data/catalog/catalog.parquet` |
| Comparison corpus | English print 1780-1830: Harvard Institutional Books 1.0, HathiTrust (non-Google), Internet Archive, Chronicling America | **[pending]** volumes after OCR exclusion | text local; manifests public |
| Early modern reference | EEBO-TCP, Evans-TCP, ECCO-TCP, hand-keyed | 61,310 texts | text local (CC0, republishable) |
| Book of Mormon | 1830 first edition (Jenson reproduction), with the surviving original manuscript and the printer's manuscript for alignment | 268,811 words | `data/bom/` (manuscript transcripts private) |
| Candidates | eight authors of section 3, by provenance tier | 621,005 words across 63 units | `data/candidates/` (Joseph Smith Papers texts private) |
| Controls | pseudo-biblical (two lists), 1820s sermons, history with a Native American origins subset, general prose | **[pending]** | `data/controls/` |

Labels and derived tables: genre (two passes plus a 5,000-record reliability sample),
near-duplicate groups (nothing deleted), per-author word counts, per-volume OCR quality and
estimated CER, KJV masks, Book of Mormon segments and the discovery/confirmation split.

## Collection

Each source's acquisition is in `data/catalog/SOURCES.md` with dates, terms and rebuild steps;
restricted sources have numbered steps to obtain them in `docs/replication.md`. HathiTrust's
75,984 Google-digitized volumes in range were not obtainable under the researcher agreement and
are absent.

## Preprocessing

1. **OCR cleaning** (`ocr_fix.clean`): long s read as f, hyphens rejoined, running headers
   and page numbers removed. Measured against hand-keyed TCP twins of 1,885 volumes: median
   character error rate 0.099 raw, 0.083 cleaned (letters only 0.078, 0.064).
2. **Quality**: every volume gets an estimated CER from proxy metrics, calibrated on those
   twins (cross-validated Spearman 0.78; 18.5% of volumes on the wrong side of the registered
   0.10 cutoff). Volumes over the cutoff are flagged `ocr_excluded`, never deleted; those within
   one cross-validated error of it are flagged `near_cutoff`.
3. **Spelling** (`ocr_fix.normalize`): MorphAdorner's Early Modern English table before 1700;
   long s and ligatures only from 1700 on, with no lexical modernisation.
4. **Deduplication**: MinHash, 5-gram shingles, threshold 0.8, keep the earliest; re-run on
   cleaned, normalised text **[pending]**.
5. **KJV masking**: passim with Amendment 2's settings; 6.82% of the Book of Mormon's words
   masked; validated on 200 alignments by a simulated hand check (95.5% KJV-derived).

## Known gaps and limits

- **OCR quality is uneven and often poor.** 38% of the ground-truth volumes exceed 10% CER
  even after cleaning. The keyed twins are 1780-1800 books; estimates for 1800-1830 print
  extrapolate in date, and for newspapers in genre as well.
- **Cross-source duplicates are under-detected on raw OCR** (`data/catalog/DEDUP.md`):
  independent OCR of the same book rarely reaches 0.8 similarity.
- **Interleaved newspaper columns are not repaired** (Wayne Sentinel, Lake Light): reading
  order needs page layout (BOM-50).
- **Genre labels are model-made.** Pass 1 used pseudo-biblical freely as a second label, so
  the either-label pseudo-biblical pool is mostly ordinary religious prose; a primary-label
  list is published beside it. The hand validation of labels is deferred (BOM-53).
- **Masked spans run short at the edges**: in the validation, 38 of 100 verbatim spans were
  judged too short, so some quoted words stay in the "original" text.
- **Book of Mormon copies are in the corpus** (six with text, one misdated to 1800). They are
  listed in `data/catalog/sealed.json` and kept out of every pool by title and by 4.2's
  contamination check.
- **Scribe evidence covers 24% of the text**: the rest of the original manuscript is lost.

## Uses

Intended for the registered analyses. Not suitable as a general-purpose clean corpus of
1780-1830 English without the OCR flags applied.

## Distribution

Manifests, catalogs, labels, masks, segments and control lists are public in the repository and
will be archived on Zenodo with a DOI; corpus text is not redistributed where terms forbid it
(Harvard Institutional Books, HathiTrust, Joseph Smith Papers). **[pending: DOI]**

## Maintenance

Corrections are made by commit, with the change and its reason in the commit message and the
affected manifest rebuilt. A later corpus version gets its own datasheet and DOI.
