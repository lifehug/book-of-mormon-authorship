# The plausibility gate (BOM-47)

Pre-registration section 3 lets a sweep lead become a confirmatory candidate only if, among other
things, "it has documented historical plausibility (period, place, or access, from the evidence
table in BOM-33)". The gate is judged by a person after the leads are seen, so on its own it has no
prior. This file fixes its criteria in writing and measures how often a **randomly chosen** swept
author passes it. That pass rate, times the sweep's expected false-lead count, is how many leads
would survive the gate by chance (`docs/sweep-plan.md`, "Chance survival of the plausibility gate").

**Blind.** The 100 authors are the `gate_sample` list in `data/sweep/calibration.json` (a seeded
random draw from the 23,872 swept authors, seed `bom47-gate`). They were judged from catalog
metadata and public sources only. No sweep score, distance or rank was opened for anyone:
`data/blind/`, `data/corpus/blind/` and the `records` of `calibration.json` were not read.

**The ceiling** of `docs/access-evidence.md` applies. A pass means a person's writing was
documented as within reach of the region. It never means that Joseph Smith or anyone else read it.

## Criteria (written 2026-11-07, before any author was judged)

The cut-off date throughout is **1 July 1829** ("mid-1829"): the dictation ran roughly April to
June 1829 in Harmony, Pennsylvania, and Fayette, New York.

The **region** is the one the BOM-33 scale already uses for a score of 2: western and central New
York within about 150 miles of Palmyra (for example Canandaigua, Geneva, Rochester, Auburn,
Ithaca, Trumansburg, Utica, Cooperstown, Buffalo), plus northeastern Pennsylvania (Susquehanna and
neighbouring counties, which hold Harmony). Albany, New York City, Philadelphia and Boston are
outside it.

### PERIOD

- **pass**: the author's text existed in an English-language edition dated before 1 July 1829.
  The author need not have been alive: a 1790s London sermon, or a seventeenth-century divine
  reprinted in 1792, could still circulate in the 1820s. A catalog row counts as the evidence when
  its date is credible for the work; the catalog's date is checked against the author's known dates.
- **fail**: every documented edition is after 1 July 1829, or the catalog date is shown to be
  wrong and the author wrote only after 1829 (for example an author born after 1829).
- **undocumented**: no credible date before the cut-off can be established.

### PLACE

- **pass**: documented presence of the author in the region before 1 July 1829 (lived, preached,
  travelled through, published from there), or an edition of the author's work printed or
  published in the region before that date.
- **undocumented**: otherwise. Being American, or printed in New York City, Boston or Philadelphia,
  is not enough on its own (see the lenient reading below).

### ACCESS

- **pass**: documented availability of the author's work in the region before 1 July 1829, to the
  standard of `docs/access-evidence.md` score 2 or 3: held by the Manchester (Farmington) library
  by its 1830 accessions, sold, advertised, reviewed or excerpted in a regional newspaper, or
  listed by a regional bookseller.
- **undocumented**: otherwise.

### The gate

**pass** if PERIOD is pass **and** (PLACE is pass **or** ACCESS is pass). Anything else is a
**fail**. "Documented plausibility" means the evidence was found; an author the search could not
document does not pass, exactly as a sweep lead would not.

The pre-registration's wording, "period, place, or access", can be read as needing only one of the
three. Under that reading PERIOD alone would pass almost every swept author, since the corpus is
1780-1830 by construction; the gate would filter nothing. The conjunctive reading above is the one
that makes the gate a filter, and it is the reading this file applies. Both readings' rates are
reported below so that neither is chosen after the leads are seen. **This interpretation is a
method choice that the pre-registration does not pin; it belongs in `pending_amendment` and should
be filed before the sweep's leads are read.**

### Evidence, and what "undocumented" means

The search for every author is the same, so that "undocumented" means the same thing each time:

1. **Catalog imprints**: every catalog row for the author (`data/catalog/catalog.parquet`, joined
   on `author_norm`), with HathiTrust's `imprint` and MARC `pub_place` where the volume is in
   HathiTrust (`data/catalog/hathitrust.jsonl.gz`).
2. **Manchester library**: the full appendix of Robert Paul (1982), 421 accessions (no. 275 is the
   last before 1830), searched for the surname and title words.
3. **Regional newspapers (this repo's OCR)**: *Wayne Sentinel* (Palmyra, 1823-1830), *Palmyra
   Register* (1817-1821), *Palmyra Herald* (1822-1823), *Ontario Repository* (Canandaigua,
   1824-1826, 1829) and *Lake Light* (Trumansburg, 1827-1828), searched with the access index's
   squeezed matching for the surname next to a title word, or a distinctive title phrase. Only
   pages dated before 1 July 1829. Every hit is read in its snippet before it counts.
4. **Grunder** (`data/access/grunder_sources.csv`) and the BOM-33 access table.
5. **Public reference works**, only for authors whose record leaves a real chance of a pass: an
   American author, an American edition before 1829, or a work of the kind that sold in rural New
   York (devotional, school, popular history). Biographical dictionaries, Wikipedia with its
   sources, archive.org and HathiTrust catalog records, the Library of Congress.

A positive hit counts. A miss does not show absence: the OCR's recall is poor (the 26 June 1829
*Sentinel* page, `docs/access-evidence.md`), Manchester's list is half one-word entries, and the
1827-1828 Canandaigua run is missing. So "undocumented" means **not found by steps 1-5**, never
"shown not to have been there". The chance-survival rate is therefore a rate *under this search
effort*; a lead in the sweep must be judged with the same effort, no more, or the comparison is
unfair. A lead researched harder than these 100 would pass more easily than the baseline assumes.

**Lenient reading, reported beside it.** A second column, `us_print`, records whether an American
edition before 1 July 1829 is documented (the BOM-33 score-1 tier: in print in the United States,
no regional evidence). The lenient gate is PERIOD pass and (PLACE or ACCESS or `us_print`).

## Results (2026-11-07)

Per-author table: `data/sweep/gate_sample.csv`, one row per author: `author, period, place,
access, gate, evidence`, plus `us_print`, `lenient_gate` and `borderline`. The evidence column
gives catalog ids (`source:id`, HathiTrust MARC place code in brackets), newspaper dates and
pages, Paul accession numbers and URLs.

| Criterion | pass | fail | undocumented |
| --- | --- | --- | --- |
| PERIOD | 94 | 4 | 2 |
| PLACE | 0 | 0 | 100 |
| ACCESS | 10 | 0 | 90 |
| `us_print` (lenient tier) | 32 yes | 60 no | 8 |

**The gate passes 10 of 100: 10%, 95% interval 5.5% to 17.4%** (Wilson score interval).
That is the chance survival rate. Against the sweep's registered expected false-lead count of
0.035 per query (`data/sweep/calibration.json`), **0.035 x 0.10 = 0.0035 false leads per query
would be expected to survive the gate by chance** (interval 0.0019 to 0.0061).

| Reading | Passes | Rate (95% interval) | x 0.035 |
| --- | --- | --- | --- |
| **Conjunctive (applied)**: PERIOD and (PLACE or ACCESS) | 10 | 10% (5.5-17.4%) | 0.0035 |
| Same, borderline calls excluded | 8 | 8% (4.1-15.0%) | 0.0028 |
| Lenient: PERIOD and (PLACE or ACCESS or US printing before mid-1829) | 35 | 35% (26.4-44.7%) | 0.0123 |
| Literal "any one of period, place, access" | 94 | 94% (87.5-97.2%) | 0.0329 |

The last row shows why the conjunctive reading is the one applied: read literally, the gate
removes only the six authors without a credible pre-1829 date, and passes nearly anything.

**Who passed**, every one on ACCESS, none on PLACE:

| Author | Evidence |
| --- | --- |
| Bunyan | Manchester library no. 49 (*Pilgrim's Progress*, New York 1804); Palmyra bookseller lists 1818 |
| Thomas Cogan | "Cogan on the Passions" in Palmyra bookstore lists, *Wayne Sentinel* May-June 1824 |
| Byron (Lake's edition) | "Don Juan, cantos ... by Lord Byron", Canandaigua ads 1824; "Byron's Childe Harold", Palmyra 1824 |
| Goldsmith (two catalog keys, one OCR-garbled as "gol dsmith, liver") | Manchester nos. 15, 41, 85; "Goldsmith's Essays", Palmyra 1818 |
| James Hervey | "Hervey's Works", Palmyra 1818; "Hervey's Meditations", *Palmyra Herald* 1822 |
| James Kirke Paulding | *Koningsmarke* in Canandaigua and Palmyra lists, 1824 |
| Joseph Sansom | "Sansom's Canada" in a Palmyra bookseller list, May 1818 |
| Kotzebue (borderline) | Palmyra theatre bill, 18 Aug 1826, for a play "from the German of Kotzebue" (*Pizarro*): a performance, not a sale |
| Montolieu / Holcroft (borderline) | *Wayne Sentinel* 8 Sep 1826 excerpts Holcroft's *Travels*; the catalog key conflates author and translator |

**What the pattern says.** The passes are the books that sold everywhere: standard British
devotional and literary authors (Bunyan, Hervey, Goldsmith, Byron) and a few Americans whose new
books reached the 1818-1824 bookseller lists. The local record is a store inventory, so a
famous author passes and an obscure one cannot. Of the 32 authors with an American printing
before mid-1829 (Boston ministers, Philadelphia and New Hampshire imprints), none could be placed
in the region. Nobody passed on PLACE. Four failed PERIOD outright: Conan Doyle (catalog dates of
1798 and 1803 for an author born 1859), Dwyer (printed at Utica, inside the region, but in 1830),
Yates and Yeghishe (1830 only).

**Limits.** "Undocumented" means not found by the search above, not absent. The OCR's recall is
poor, the Canandaigua run lacks 1827-1828, and Manchester's list is half one-word entries ("Durand's
Journal", no. 200, might be J. B. L. Durand's *Voyage to Senegal*, but neither its identity nor its
date before mid-1829 is established, so it was not counted). The rate is therefore tied to this
search effort. A lead must be judged with the same steps 1-5 and no more. In particular, PLACE
was never met by anyone here, so a lead passing on PLACE alone deserves a note on how the
evidence was found. Two calls are marked borderline, and the rate is reported with and without them.

**Next action.** Add the conjunctive reading of the gate and the search protocol (steps 1-5) to
`config/preregistered.yaml` `pending_amendment`, and file the amendment before the sweep's leads
are read. Leads that pass the gate are then reported against 0.0035 per query, not alone.
