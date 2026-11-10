# Inventory of measured and tested results (as of 2026-11-10)

Swept: all GitHub issues BOM-01 to BOM-86 with comments (#11-#97), docs/*.md, paper/blog.md (body and Log), paper/replication-report.md, paper/preregistration.md section 11, paper/deviations.md, paper/review/*, data/**/SOURCES.md and reports, and the result JSONs where a number was needed (data/blind, data/synthesis, data/dating, data/benchmark). Not compared against the paper drafts.

Format: **name** | what was tested | key number(s) | source | why it might matter to a reader.
"Simulated" = an AI model stood in for a human reviewer or reader.

## 1. Corpus and data quality

- **Harvard Institutional Books slice** | English volumes 1780-1830 from the 983,004-volume dataset | 31,958 volumes, 10.47B tokens, 73 GiB (two OCR versions), median OCR score 99 | BOM-07 | sets the scale of the core library; the dataset ships two OCR versions per volume, so storage doubled.
- **Harvard date-filter correction** | first filter used the earlier of two MARC dates | 32,132 -> 31,958; 174 reprints (e.g. Faraday 1859 via an 1821 date) dropped | BOM-07, blog | an early example of catalog dates letting later books into the window.
- **HathiTrust overlap and pull** | period public-domain volumes not in Harvard | 135,035 in window; 107,178 not in Harvard; 31,194 received (19 GiB, 24 min); 75,984 Google-digitized not obtainable; 9,384 genuinely new; 21,810 duplicate Internet Archive scans | BOM-08 | most of HathiTrust's extra volumes were unobtainable; about 104k Google volumes are still outside the library (BOM-71).
- **HathiTrust overlap bug** | first overlap check | returned 0 because of a field-name bug (`ia_id` vs `ia_identifier`) | BOM-08 | a plausible-looking wrong answer would have passed unnoticed.
- **Internet Archive pull** | English texts 1780-1830 | 307,567 catalogued; 249,906/251,204 pulled (99.48%), 99 GiB, 0 HTTP 429s; 4,822 not obtained (coded) | BOM-09 | the largest source; 11,896 items carried a placeholder date of 1800.
- **IA filename assumption** | 404s assumed to mean no OCR | 28 of 30 sampled 404s had OCR under another filename; ~8,500 books (3.4%) recovered | BOM-09 | a silent-loss bug found by checking a side question.
- **Chronicling America** | newspapers 1800-1830 | 158,960/159,146 pages (99.88%); 258 failures; New York only 47 pages; per-page API would have taken ~219 days; bulk text identical word-for-word on 2,490 overlap pages | BOM-10 | the national newspaper set has almost nothing from the Palmyra region.
- **TCP (EEBO/Evans/ECCO)** | hand-keyed early modern texts | 61,310/61,315 texts, 22 GiB | BOM-11 | the pre-1700 comparison set for dating; also the hand-keyed ground truth for OCR error.
- **Phinney 1828 Bible check** | does the Smiths' 1828 Cooperstown Bible carry the 1769 KJV text | 66.9% of verses, 64.5% of words found verbatim in noisy OCR, even across OT/Apocrypha/NT | BOM-06 | supports using the 1769 KJV for masking.
- **New York newspapers** | Wayne Sentinel, Lake Light, Ontario Phoenix | Sentinel 376 issues, 1,429 pages, 1823-1830; Lake Light 42 issues, 168 pages, 565,630 words; Ontario Phoenix not digitized anywhere (~20 scattered pre-1830 paper issues survive; film starts 7 Jul 1830) | BOM-41 | the "New York gap" was Chronicling America's, not digitization's; Phelps's pre-1830 paper is unrecoverable.
- **Lake Light attribution** | Phelps's tenure in the masthead | Phelps & Bloomer only to 1828-02-18; only 15 of 42 issues (196,448 OCR words) eligible; expected yield near zero; the signed-item extraction was never applied | BOM-41, BOM-13 | corrected an overstated Phelps tenure; Phelps still has no pre-1830 sample.
- **Catalog merge** | combined catalog | 695,021 rows, 533,328 with text (first close missed HathiTrust entirely; reopened) | BOM-12 | a close that was wrong and was reopened.
- **OCR error measured on keyed twins** | CER on 1,883 TCP hand-keyed twins | median 0.099 raw, 0.083 cleaned (letters 0.078/0.064); 38% still over 0.10 after cleaning | BOM-14 | OCR error is high and the registered 10% CER cutoff excludes a large share.
- **Per-volume CER model and exclusions** | proxy model for every volume | MAE 0.041, Spearman 0.78, 18.5% on wrong side of cutoff; over 0.10: Harvard 2.5%, HathiTrust 11.9%, IA 24.9%, Chronicling America 27.8%; vs Harvard's own score Spearman -0.58 | BOM-14 | OCR quality differs by source, which can bias borrowing nulls.
- **Cleaning volumes** | header, hyphen and long-s repair over 472,018 volumes | 100.6M header lines, 252.9M hyphen joins, 348.9M long-s fixes | BOM-14 | scale of preprocessing.
- **LLM OCR correction (rejected)** | Sonnet correction on 100 windows | median CER 0.094 -> 0.061 but some replies invented text; mean got worse; not applied | BOM-14 | a tempting method that fails on faithfulness.
- **Wayne Sentinel OCR fragmentation** | single-letter tokens vs real garbling | Sentinel vowelless-token rate 0.009 vs Chronicling America 0.008; 30% lone letters from the viewer; re-segmentation recovered words 62% -> 93% | BOM-14, BOM-41 | a quality metric nearly down-weighted the most important local paper.
- **Dead letter-digit garbage check** | OCR scoring code | branch scored 0.000 everywhere because tokenizer split digits out; read as a result before being found | BOM-14 | a zero read as a finding was a bug.
- **ALTO confidence (deleted, then misread)** | per-word confidence from the one surviving batch | mean WC 0.493, 53.2% of words below 0.5; the extractor had deleted ALTO for all 158,960 pages | BOM-50 | a data-loss incident; the confidence figure was later shown to be misleading.
- **OCR verified on page images** | phrases picked from images, searched in OCR | Chronicling America typical page 8/10 exact (10/10 present), worst of 5,000 15/16; Wayne Sentinel 26 Jun 1829 p3 0/10 | docs/ocr-verification.md | CA OCR is good enough; NYSHN OCR destroys words, so no negative may be read from it.
- **4-gram survival under OCR** | arithmetic at ~80% token accuracy | 4-gram survives ~41%, 5-gram two passes ~33% | DEDUP.md | borrowing search loses over half of real matches (false negatives, unmeasured margin).
- **Dedup, same-source** | MinHash 5-gram at 0.8 | raw 19,697 groups / 20,869 non-keepers; normalized 19,920 / 21,218 | BOM-12, BOM-15 | duplicates flagged, never deleted.
- **Dedup cannot see cross-source copies** | 300 same-title/author cross-source pairs | median similarity 0.164 (first sample), 0.117 raw -> 0.180 normalized; 0% reach 0.8 | DEDUP.md | the registered dedup method misses the same book OCR'd twice.
- **Metadata dedup pass** | title+author+year across sources (Amendment 6) | 4,697 groups, 8,269 non-keepers; combined 19,692 groups, 24,779 non-keepers; text check: 341/352 pairs within 1.5x length, vocab overlap 0.95 | BOM-55 | fixes most cross-source double counting; copies within one source still escape.
- **Spelling normalization** | MorphAdorner pre-1700 | 442,381 mappings over 128.8M tokens; table-only first pass wrongly made part -> partly ~1M times, ye -> you on determiners; MorphAdorner itself maps an -> and 3.28M times | BOM-15 | a tool used wrongly at first; its quirks needed amendment.
- **Normalization rewrites grammar** | MorphAdorner substitutions | doth -> does 1,270,334; ye -> you 882,357; saith -> says 592,880 | BOM-29, dating-plan | would have made early modern text look modern; dating model reads printed text instead.
- **Genre labelling pass 1** | rules plus llama3.1:8b | 389,532 by rule, 305,489 by model; 290 PARSE_FAIL | BOM-12 | genre is used only to build pools and nulls.
- **Genre model choice** | 60 then 300 records | Haiku 65% -> 72% with definitions; Sonnet 87% (60); on 300: Sonnet 98%, Llama 97% on rule-decided rows; models agree only 72% on hard rows (a third are taxonomy holes) | blog | small-sample choices were within noise; taxonomy, not models, caused disagreement.
- **Genre pass 2 agreement** | Sonnet on 5,000 stratified sample | 84.9% either-label, 50.8% exact, 15.1% contradiction; HathiTrust 83.9%; "other" 37.4% contradiction; 1640s text 22-25% vs 1820s 7%; Opus adjudicated 757 (Sonnet 553, Llama 62, both 87, neither 55) | BOM-12 | label reliability is moderate and worst for early modern text.
- **Genre pass-2 outage error** | usage-limit failures | 3,027 outage failures written as PARSE_FAIL; first agreement figure 7.4% (wrong) | blog Log 10-24 | led to the "transient failure is not an answer" rule.
- **Same-model self-agreement** | Llama at temperature 0 | 19/20 identical | Amendment 4 | second pass must be a different model family.
- **Genre hand validation and perturbation** | 300-record validation; 100-run label perturbation (Amendment 4) | AI draft agrees with pass 1 on 151, pass 2 on 87, neither 62; the perturbation and hand validation have NOT been run | BOM-53 open | the only accuracy measure of genre labels does not yet exist.
- **Placeholder 1800 dates** | title pages of 11,494 volumes dated 1800 | 2,431 confirmed; 1,281 other 1780-1830 year; 1,502 post-1830; 6,280 no year | BOM-56 | post-1830 books (e.g. 1840s Cooper) sat in the window in v1.0.
- **Catalog date audit** | volumes whose own text names later years | 366,580 scanned; 23,859 flagged; 19,463 moved past 1830; Harvard 38.9% flagged; serials 19.4% | BOM-64 | catalog dates are unreliable, mainly for serials and Harvard.
- **Date-audit precision** | model-read sample (simulated) | 81/100 flagged truly later; 5/97 unflagged missed; ~1 in 5 moved volumes may truly be pre-1830 (e.g. library stamp "1923") | BOM-64 | the correction errs toward exclusion; moved volumes kept in a separate column.
- **Misdated later quotations** | Book of Mormon text in "pre-1830" volumes | 17 volumes (Congressional serial set "1817" quoting Jacob 2, Monthly Review "1826", etc.); dates move 16, the seal catches the 17th; seal alone catches 9 | BOM-23, BOM-64 | without the audit, later texts quoting the book would look like sources.
- **Book of Mormon copies in corpus** | sealed copies | 13 titled works sealed; a modern "Book of Morman" and Oahspe (1882, catalogued 1800) found | BOM-54 | seal title rule widened to "morm[ao]n".
- **KJV masking** | passim alignment of KJV spans | BoM 18,336/268,811 words (6.82%; 2 Nephi 32.7%, 3 Nephi 15.0%); candidates 3.71%; controls 1.78% (sermons 2.46%, pseudo-biblical 3.40%); known-answer texts 0.30% (Jasher 3.5%) | BOM-16 | quantifies how much of the book is KJV text.
- **KJV mask validation** | simulated check of 200 spans; planted quotations | 191/200 KJV-derived (95.5%); edges too short in 38/100; planted P 0.947, R 0.781, F1 0.856 | BOM-16 | some KJV words remain in "original" text.
- **Segmentation** | narrator, dictation-order, scribe schemes | 756 chunks, 250,486 words after masking; seeded discovery/confirmation split | BOM-17 | defines the sealed units.
- **Controls** | four control groups | pseudo-biblical 3,672 (either label) / 29 (primary); sermons 6,143; history 2,986 (47 on Native American origins); general prose 4,998; 0 fail contamination | BOM-18 | either-label pseudo-biblical pool is mostly ordinary religious prose.
- **Curated pseudo-biblical control** | marker rule + two-model judging | 1,349 candidates; Sonnet/Opus agreement 97.7%; gate 15/15 named editions admitted, 25/25 rejection set refused; 49 yes -> 18 works | BOM-54 | a checkable, reproducible definition of "imitation scripture".
- **Corpus freezes** | v1.0 and v1.1 | v1.0 70 files (DOI 10.5281/zenodo.23740903); v1.1 83 files (DOI 10.5281/zenodo.23819273) | BOM-19, BOM-56 | the corpus state behind every result is pinned.
- **Derived data and hash reconstruction** | non-reconstructability of published tables | a complete 4-gram hash list can be unrolled into text; Enoch and Josephus hashes withheld; all 180 benchmark tests reproducible from published counts | BOM-44 | an outsider can rerun the classical benchmark without the licensed corpus.
- **Index build integrity** | passage index | 163,121,310 passages, 280 shards, 120 GB; GPU vs Mac vectors cosine min 0.9999983; 3 volumes in two shards; 61 volumes too short | BOM-25 | the search index was checked across machines.
- **Backup check** | 914 GB to B2 | 2,358,446 files match; 6 differences explained and fixed; restore SHA matches | BOM-65 | everything is recoverable.

## 2. Candidate samples and power

- **Candidate word counts (measured)** | pre/post-1830 samples by provenance | JS handwritten 0 pre / 6,158 post; JS dictated 2,844 pre / 5,402 post; Cowdery handwritten 1,443 pre; Spalding 44,279; Ethan Smith 299,398; Hunt 59,611; Rigdon 23,478, Pratt 101,748, Phelps 31,538, Cowdery printed 48,002 (all post-1830) | BOM-13 | only the three non-Mormon candidates clear the 10,000-word floor before 1830.
- **JS pre-1830 sample far smaller than estimated** | Revelation Book 1 under a written rule | 2,844 words vs the 11,500 estimate | BOM-13 | the central candidate is barely testable.
- **Signed periodical items** | signature lines in Messenger and Advocate and Star | 77 lines, 43 admitted | BOM-13 | Cowdery's letters were declared written with Joseph Smith's help.
- **JSP transcript reader bug** | glossed words and editorial notes | BoM manuscript rebuild changed 1 of 1,182 paragraph mappings; printer's similarity max +0.014; earlier "2,188 splits" claim was wrong (8) | BOM-52 | a reader bug with tiny effect, and a corrected overstatement.
- **Power analysis** | minimum sample on Federalist and pseudo-biblical authors | ~10,000 masked words of reference needed; 2k/5k test chunks fine; masked pre-1830: Ethan Smith 277,352, Hunt 56,956, Spalding 41,833; JS 3,082, Cowdery 2,691 below floor | BOM-43 | stated before testing that JS and Cowdery cannot be tested reliably.
- **Time-split validation** | can later writing stand in for earlier (30 authors, 7+ year gap) | 37-60% by method (chance 3%) vs 80% gate; JS correct by all 4 methods on one sub-floor test, Cowdery by none | BOM-48 | no expanded post-1830 corpus is admitted for any candidate.
- **Expanded corpora refused** | Amendment 5 gate | no candidate granted an expanded corpus; strict tier admits only JS's 11,400 words | BOM-49 | the post-1830 route to testing JS is closed.
- **Dual-register authors** | authors with both imitation scripture and 10k+ ordinary prose | 3 (Snowden, Dodsley, Kenrick); first count said 5 (copies of own works) | BOM-46 | imitation weights rest on three authors.
- **BoM quotation in candidate samples (first find)** | 12-token check on replication samples | 5/35 Pratt and 1/25 Cowdery samples quote the BoM; excluded | BOM-22 | circular matching caught early for the replications.
- **BoM overlap analysis** | runs of 8+ words shared with the narrative, classed by date | Cowdery's 1829 Articles 40.4% shared (295 quotation words); Pratt Voice of Warning 4.8% (997); JS revelations 69 words (2.5%): 0 quotation, 9 predate the passage, 51 same weeks, 9 stock | docs/bom-overlap-analysis.md | the registered seal was not applied to candidate samples; Cowdery's ranking was leakage.
- **After Amendment 43 masking** | quotation removal | Cowdery Articles -494 words (36.5%) leaving ~798 words (844 tokens, unscorable by candidate models); Pratt -1,321 and -375; one JS 1833 letter passage (24 words); JS revelations unchanged | Amendment 43, commit edf5977 | Cowdery's pre-1830 sample effectively vanishes.

## 3. Benchmark and classical methods

- **Classical library on synthetic authors** | unit tests | Delta 20/20; GI true >= 0.9, other <= 0.1 | BOM-20 | basic correctness.
- **Classical methods on corpus authors** | 30 known authors, held-out books, chance 3% | Delta 60-73%; char n-gram 63-67%; GI true 0.52 vs wrong 0.04, AUC 0.91; ENSC 43% falling to 7%, its "none" too eager (11/30) | BOM-20 | real-corpus accuracy is far below benchmark accuracy.
- **Benchmark run 1 defects** | GI pool 10 instead of 200; a Late War copy among Hunt's imposters | kept as evidence | BOM-21 | an error caught and published.
- **Benchmark verdicts (run 2)** | 180 tests: Federalist, imitation scripture, Scott dictated | Burrows 100%, Cosine 97.2% (no open-set score); GI 83.3%, threshold saturated -> fails; ENSC (BOM-20 version) 100% closed, 66.1% open-set FP -> fails | BOM-21 | no classical method passes both halves of the registered bar.
- **GI confusions** | where GI fails | Hunt -> Snowden 13/20; Scott -> Galt 11/60 | BOM-21 | authors writing in the same imitation register are confused.
- **Multiverse (54 configurations)** | benchmark under alternative settings | Deltas 54/54 closed set; ENSC 0/54 both halves; GI 8/54, all at feature fraction 0.3; corpus demo median agreement 100%, lowest 50% (GI) | BOM-21, BOM-40 | verdicts are robust except GI's.
- **Open-set check flaw** | false-match check as built | ~5% by construction for continuous scores; corrected (Amendment 25): GI 0.0 -> 0.617, ALM 125M 0.055 -> 0.473 | BOM-69 | the original yardstick was invalid and flattered methods.
- **Fidelity: GI** | our GI on PAN 2014 vs Kestemont et al. Table 1 | 11/12 rows within 4 points, median gap 1.3 | BOM-57 | GI's failure is the published method's, not a bug.
- **Fidelity: ENSC** | our BOM-20 ENSC vs Funai 2010 / Schaalje 2011 | ours not faithful (alpha cutoff vs latent author); published method 29.2% wrong (Funai 16%) vs ours 63.3%; "none" error falls 80% -> 0% from 1k to 10k-word samples; eq. 12 narrows swing 80 -> 25 points | BOM-57 | ENSC's "none of these" depends on candidate sample length and kind.
- **Repair test on 30 fresh authors** | GI at 0.3 features; published ENSC | GI 93.9% / 3.3% on benchmark but 51.3% fresh; ENSC 44.4% / 88.3% false "not none"; Deltas 63.0% / 61.8% fresh | BOM-58 | GI and ENSC retired; Delta accuracy collapses with 30 candidates.
- **Improvement attempts** | Delta verification score; ENSC size refit; GI 1,000 rounds | Delta threshold FP 24-29% (benchmark), 68-97% (fresh); ENSC refit shows published model understates variance ~4x (favours "none"); final eval on 30 new authors: GI 56.5%/56.7%, Burrows 57.0%/73.2% FP, Cosine 60.3%/98.8%, ENSC 53.8%/90.2% and 54.8%/92.5% | BOM-60 | no improvement works; classical ceiling ~55-60% among 30 period authors.
- **Rarity by text** | counting document frequency by text not volume | 221,344 volumes -> 217,386 texts; Hunt 9 printings -> 4 groups; Late War 1 -> 15 rare shared (p 0.05 -> 0.0008); title keys failed twice (Serial Set, Gibbon) | BOM-60, Amendment 8 | the registered rarity rule could not see a reprinted source.
- **Prior-work table on equal terms** | McNemar on the 110 held-out tests | Burrows 0.955, Cosine 0.818, GI 0.745 (FP 0.827), ENSC 0.964 (FP 0.782); 297M primary beats GI 27-0 and Cosine 19-0, not Burrows (4-0, p 0.13) or ENSC | BOM-68 | the language model's gain is mostly in false matches, not ranking.
- **Word counts vs model features** | Burrows vs V3 hidden states (180 trials) | Burrows beats V3 28-0 (p < 1e-8) | BOM-68 | raw model hidden states are worse than word counts for attribution.

## 4. Language models, training and the ALM benchmark

- **Training set and contamination** | 1780-1830 by corrected year | 202,816 volumes, ~25-25.7B tokens; max 12 shared 12-token strings among kept (threshold 20); 1,489 benchmark, 19 candidate and 225 known-answer author volumes removed | BOM-27 | the models never read the Book of Mormon or the test authors.
- **Model losses** | validation loss by size | 125M 2.515; 297M 2.325; 590M ~2.19 | BOM-27 | bigger models fit period English better.
- **1B attempt** | 1.036B training | first launch died (bf16 off under torchrun, fp32 OOM, 10x slow; ~$33); later unrecoverable loss spike at step ~15,800 (loss 2.33 -> 3.46, grad norm to 150-770); halved and quartered rates failed; abandoned (~$230); checkpoints deleted without asking | BOM-27, Amendments 38-39 | a failed scale-up, partly unrecoverable for diagnosis.
- **QK-norm test** | 125M at 10x and 30x LR | 30x plain val 5.83, grad norm to 3,051; 30x QK-norm val 3.62, grad norm <= 0.2 | data/stability | justifies the 590M design change.
- **ALM benchmark, primary** | 110 held-out tests | right author 0.936 / 0.991 / 0.982 (125M/297M/590M); false matches 0.473 / 0.382 / 0.218; Madison 0/6 at 125M, 6/6 at 297M; Scott dictated 60/60 | BOM-28 | best stable false-match rate is 22%; still far from the 5% bar.
- **ALM variants** | V1 (10x LR), V2 (classifier head), V3 (hidden states) | V1 0.936/0.455, 0.936/0.473, 0.627/0.818; V2 0.900/0.282, 0.909/0.136, 0.764/0.391; V3 ~0.84 / ~0.69-0.72 | BOM-28 | no variant passes; size does not help V3.
- **V1 failure explained** | LR chosen on held-out training text (Amendment 41) | 590M V1 raised loss on new text +0.81 nats; selection picks 1e-5 = primary, reproduces primary to the decimal | Amendment 41 | a bad setting, not a bad method; cross-machine reproducibility of the primary.
- **V2 instability** | five extra seeds per size (Amendment 42) | false matches 9-93% (125M), 53-98% (297M), 32-93% (590M); 297M's 0.136 was an outlier; same seed on Mac vs H100 0.900/0.282 vs 0.764/0.591 | Amendment 42 | the apparent best method was luck; hardware nondeterminism.
- **GPT-2 ablation** | same fine-tuning on modern base models | GPT-2 124M 0.900 / 0.918 FP; 355M 0.945 / 0.855; ours 0.936/0.473 and 0.991/0.382 | BOM-68 | period-only training halves false matches.
- **Candidate model validation** | held-out windows among candidates (297M) | Ethan Smith 20/20, Hunt 8/10, Spalding 7/7, Cowdery printed 7/7, Phelps 3/3, Pratt 19/19, Rigdon 1/2; JS and Cowdery pre-1830 untested (too short) | BOM-28 | candidate models recognise candidates where text exists.
- **Imitation robustness (forward)** | method trained on ordinary prose names author of imitation scripture | Burrows/Cosine 13/18 (weight 0.5); GI 11/18 (0.5); ENSC 7/18; ALM primary 5/7/6 of 17; V1 0-2/17; V3 4-5/17; style 297M 7/18, 590M 10/18 (all weight 0) | BOM-31 | model-based methods are fooled by scriptural imitation; this zeroes them in the synthesis.
- **Imitation reverse direction** | reverse test | Burrows 0.38, Cosine 0.29, GI 0.12, ALM 297M 0.17, 590M 0.04, style 0.54/0.42 | BOM-31 | weak in both directions.
- **Imitation disclosure** | smoke test before registration | one Cosine Delta number (0.72/0.29) seen before Amendment 31 | Amendment 31 | a disclosed pre-registration leak.

## 5. Style encoders and the author sweep

- **Style encoder training** | contrastive encoder on 8,527 authors | held-out top-1 0.42 (297M), 0.418 (590M); 1,100,930 passages | BOM-30 | moderate author recognition on unseen authors.
- **Style encoder benchmark** | 180 trials | 297M 0.839 closed, 0.500 FP; 590M 0.839, 0.628; match threshold 1.0 (cannot say "match" under registered rule) | BOM-30 | style encoder cannot return a registered match.
- **Sweep calibration** | 200 held-out books among 23,872 authors | true author first: MFW 27%, style 30%, either 34.5%; top-5 46%/52%; median rank 11.5/4; not usable by 70% rule | BOM-39 | the whole-library sweep failed its own usability test.
- **Expected false leads** | leave-one-out over 200 books | 0.035 per query (7/200); thresholds MFW 0.211, style 0.092; signal correlation 0.29 / 0.55 | BOM-47 | any lead would have been surprising.
- **Plausibility gate** | blind on 100 random swept authors | 10% pass (5.5-17.4%), all on access, none on place; literal reading 94%, lenient 35% | BOM-47, Amendment 40 | the literal gate filters nothing; conjunctive reading chosen before leads.

## 6. Borrowing and wording (exact, rare phrase, paraphrase)

- **Known-answer set** | 9 genuine translations vs 3 presented as ancient | rule: Mann-Whitney p <= 0.01 | BOM-61 | every borrowing test must first show it can separate these.
- **Exact reuse known answer** | passim vs earlier books | U 4/27, p 0.964: fails; forgeries share less verbatim text than genuine translations (Ossian 0, Rowley 0, Jasher 0.28%) | BOM-23 | exact reuse cannot speak to the translation question.
- **Exact reuse table** | KJV-masked text vs earlier volumes | Late War 8.92% (mostly War of 1812 documents); Newton sermons 2.47%; BoM 0.52% -> 0.26% after date audit -> 0.16% with seal; 30 pre-1830 stock phrases (9-46 tokens, identity 0.27-0.67); 0 missed Bible text | BOM-23, BOM-64 | the BoM copies almost nothing verbatim from earlier books.
- **Exact reuse bug** | stock-phrase filter | let through "with propriety be said to have been"; fixed | blog 10-31 | matching code error caught.
- **Null sizing** | 99th percentile stability vs sample size | +-119% at n=500, +-52% 2k, +-31% 5k, +-16% 20k; 7 missed Late War copies collapsed null to 0; ~96% of volumes score 0 | BOM-45 | the registered 500-volume null was far too noisy; whole corpus used instead.
- **Johnson 2013 replication** | <1/1000 rarity rule | Late War rank 97/221,344, 174 shared, p 0.0004; Napoleon 44th; among 10k+ word books Late War 31st, Napoleon 8th, behind other imitation scripture | BOM-22 | the Late War signal is real but not unique.
- **Late War shared phrases** | 183 Johnson-rare phrases | 6 in no other book, 17 in 1-4, 25 in 5-19, 135 in 20+; 36 also in imitation scripture (Snowden 18) | blog, BOM-24 | most shared phrases are stock biblical-register language.
- **Wrong-book correction** | "Late War shares 1 rare phrase" | first figure came from Brockway's 1784 sermon; Hunt's also 1 | BOM-24 | a published number was corrected.
- **Rare-phrase known answer** | strongest-source density | U 6/27, p 0.927 (0.814 without missed own copy): fails; 29/51 draw winners under 1,000 words | BOM-24 | uninformative on translation; score dominated by short pieces.
- **Rare-phrase source list** | registered rule, by text | 2,044 volumes significant (53 of top 100 on one phrase); Napoleon 12 shared, p 0.0003; Late War 22, p 0.0006 (0 by volume count); View of the Hebrews 2, p 0.046; Spalding 1, p 0.068 | BOM-24 | Late War and Napoleon are registered significant results.
- **Imitation-scripture comparison** | within curated pseudo-biblical list (post hoc) | Jasher 1829 first (7.99, 31 shared); Napoleon 4th; Late War 5th (3.86); top sharers Wroe 1829 (62), Jasher printings, Oriental Translation Fund 1829 | BOM-24 | Late War shares at a rate typical of its genre.
- **Seal missed then applied** | rare-phrase run | 11 later quoting volumes held out after first run | BOM-24 | a process slip caught before write-up.
- **Embedding model choice** | 1807 Psalms vs KJV with 1M distractors | bge-small R@1 0.594, R@10 0.777; e5 re-scoring made it worse (0.508 at depth 1,000); MiniLM 0.447; right psalm found in ~3 of 5 queries | BOM-25 | the paraphrase search finds close paraphrase, not every retelling.
- **Semantic positive controls** | Josephus and Twelve Patriarchs | Josephus passes (KJV strongest 3/3); Patriarchs fails in one draw due to 1576 own copy, passes without it (Amendment 20, post hoc) | BOM-25 | the search is shown to find paraphrase, with a post hoc decision.
- **Semantic known answer** | separation | U 14/27, p 0.50: fails | BOM-25 | paraphrase table is descriptive only.
- **Whole-corpus paraphrase table** | BoM vs 221,373 window volumes | 214,549 parallels, 30,994 sources; 622 "stand out" (rule does not control for register); Josephus editions 14 of top 20 (first miscounted as 11); View of the Hebrews 700th | BOM-25 | top sources are biblical retellings.
- **Named sources, direct test and null** | each source vs its group and 500 matched volumes | VoH 1825 1st of 49 (29.6, null p99 45.0, 84.6th pct); VoH 1823 2nd (94.0th); Napoleon 3rd of 18 (98.4th, interval touches 8.8); Late War 6th of 18 (79.8th); Spalding 12th of 49; none stands out | BOM-25, Amendment 21 | View of the Hebrews wins its group by being its most biblical member.
- **False write-up corrected** | "no named source ranked first" | wrong; VoH ranked first; issue reopened | BOM-25 | an error in a closed result.
- **Story skeleton extractor check** | 20 KJV chapters read twice | median agreement 0.92, 233/238 events supported, match threshold 0.700 | BOM-25 | event extraction is reliable on biblical narrative (not checked on period prose).
- **Story skeleton controls** | retellings vs sources | Josephus-Genesis 25.5, 108 events, p 0.001 (best unrelated 4.5); Patriarchs 5.5, p 0.003; Jasher 4.0, p 0.75 | BOM-25 | the test detects real retellings.
- **Story skeleton, named sources** | BoM 1,421 events | VoH 1823 17/49 (p 0.97), 1825 43/49 (p 1.0); Manuscript Story 18/49 (p 0.67); Late War 12/18; Napoleon 3/18 (p 1.0) | BOM-25 | no named source shares the book's story order.
- **Philip's War skeleton hit** | registered mark met | Church's History of Philip's War 1st of 49, p 0.008 (six letter-and-rebellion events, Alma 60-61); chance of one such p among 49 ~0.39 | BOM-25 | a registered hit best read as chance.
- **Skeleton, top 20 sources** | event order | none at p <= 0.01; longest run 9 of 1,421 (Josephus, p 0.24) vs 108 for control | BOM-25 | no large-scale story borrowing from the leading sources.
- **Triage of parallels** | 1,069 pairs, simulated second review | 382 biblical, 685 common, 2 specific first pass; 0 specific under both; agreement 0.740, kappa 0.505 | BOM-26 | every surfaced similarity is KJV or period stock language.
- **Grunder's proposed sources (exploratory)** | 139 of 500 proposed parallels in catalog | median percentile 91.0 vs 87.4 (p 0.087); histories 92.9 vs 82.6 (p 7e-5); only Josephus stands out | docs/semantic-plan.md | proposed sources look slightly closer, as expected from how they were chosen.

## 7. Italics, dating and story-independent text tests

- **Italics check of Phinney 1828** | are seeded KJV italic words italic in the 1828 edition (simulated) | 88/100 | BOM-62 | the family Bible carried the italics.
- **Italics test** | share of KJV italic vs roman words kept in parallel spans | translations R_i 0.903, sermons 0.904; BoM 0.645 (0.576-0.716) vs roman 0.946; D 0.301 vs 0.02-0.03; test's own check fails, so no interpretation | BOM-62 | the BoM drops italic words far more than other KJV users; registered test cannot say why.
- **Isaiah italics** | italic words not kept in Isaiah | 37.3%, matching Spencer 2020 (37%) and Wright 1998 (~40%) | BOM-62 | independent reproduction of a known finding.
- **Dating validation** | held-out authors | grammar mean error 23.4 y, 90% coverage 0.91, interval ~85 y; lexical 13.2 y, coverage 0.76; transformer 10.1 y, 0.94 | BOM-29 | grammar model is honest but coarse.
- **Interval rule unworkable** | registered 6.4 rule | only 14% of genuine 1780-1830 segments pass (median rule 85%); replaced by median rule (Amendment 19, post hoc) | BOM-29 | the registered dating rule could not date anything to the window.
- **KJV imitation shift** | pseudo-biblical controls vs ordinary 1780-1830 | grammar -53.4 y (p 0.0001); lexical -5.5 y; transformer +0.8 y | BOM-29 | biblical imitation fools the grammar model, not the transformer.
- **Dating known answer** | separation | p 0.57 / 0.81 / 0.95: none separates | BOM-29 | dating cannot tell translations from forgeries.
- **Keyed vs OCR text** | 1780-1809 segments reaching window | keyed 55% vs OCR 83% (71 keyed segments) | BOM-29 | a keyed text like the BoM may be dated early for that reason alone.
- **Median-rule validation** | held-out volumes | 1780-1830: 1,464/1,875 H3a; pre-1700: 3,729/4,144 H3b; KJV H3b; pseudo-biblical 10/7/8 | Amendment 19 | 7 of 25 period imitations are themselves called early modern.
- **Leakage check** | transformer error on volumes the LM trained on vs not | 11.1 y vs 8.4 y | BOM-29 | no sign that having read a volume helps.
- **KJV dated** | KJV text itself | grammar 1631, lexical 1710, transformer 1752 | BOM-29 | calibration point.
- **BoM dating (blind)** | 168 chunks | grammar median 1661 (IQR 1600-1696); lexical 1736; transformer 1755; H3b by grammar (78% of 215 segments before 1700, 7% in window); lexical and transformer: neither | BOM-32 | the text's language dates early by every model.
- **H3c** | BoM vs pseudo-biblical controls | grammar 1661 vs 1734, lexical 1738 vs 1794, p 0.0001; by book p 0.0025 / 0.0001; rejected | data/dating/h3c.json, BOM-38 | the text is more archaic than period imitations; vernacular control unavailable.
- **Thematic dating** | BOM-63 | not run | BOM-63 open | the planned theme-based dating has no result.

## 8. Manuscripts, dictation and scribes

- **Manuscript alignment** | anchors between manuscripts and 1830 | printer's 463/468 pages, 99.7% of paragraphs; original 207/231 pages, 27.6% (Skousen ~28%); 186,331 anchors, all but 66 in order | BOM-05 | alignment independently reproduces the known 28% survival.
- **Text changes** | words changed vs 1830 | printer's MS 3.46%; original MS 18.6% (spelling, damage) | BOM-05 | scale of variation between witnesses.
- **Scribe map** | page hands | printer's: Cowdery 388, Scribe 2 80, Hyrum 7; original: Cowdery 209, John Whitmer 13, Scribe 3 13, JS 1 (28 words); 870/1,197 paragraphs lack original | BOM-05, BOM-34 | scribe evidence covers ~24% of the text.
- **Dictation signature** | homophone corrections, original vs printer's | 36 vs 8; 6.3x share (p 1e-7); same passages OR 12.5 (p 2e-6); Cowdery only OR 9.0 (p 2e-9); 0.43 vs 0.03 per 1,000 words | BOM-34 | the original was written by ear, the printer's copied by eye; agrees with Skousen.
- **Hand check of photographs (simulated)** | 60 events | 21 clear, 12 partly, 27 unclear, 0 contradictions; type right 44/60; homophones 30/36; sound-alike 0/6 and spelling 0/4 are not ear errors; ratio holds (OR 8.9, p 6e-8); there/their 23 of 30 | BOM-34 | the result survives correction of mislabelled pairs; broader measures are not ear evidence.
- **Page-dependence not modelled** | Fisher tests treat corrections as independent | flagged by simulated statistician; not addressed | review response | p-values overstate certainty.
- **Narrator / dictation-order / scribe test (6.3)** | Cosine Delta leave-one-out | narrator 0.744 (chance 0.277, p 0.001); dictation order 0.758 (chance 0.502, p 0.001); chance-corrected narrator 0.645 vs order 0.514; scribe untestable (only Cowdery fills 3+ chunks: 11); benchmark 0.9625 -> not separable | BOM-34 | narrator differences are above chance but below real-author level and confounded with dictation order.
- **Larsen 1980 replication** | speakers by model labelling (simulated) | 16/24 speaker counts within 10%; 17 speakers differ, Wilks 0.079, p 8e-38; 4/215 blocks to a candidate; narrator level p 1e-14, 11/246 | BOM-22 | the 1980 findings reproduce, with the non-independence caveat.
- **Holmes 1992 replication** | five vocabulary-richness variables | JS writing 3/3 alone; prophets mixed; D&C 3/3 with prophets; Isaiah 2/3 apart; his 10,000-equivalent conversion does not reproduce from his formulas | BOM-22 | reproduces, with a reporting gap in the original.
- **Jockers 2008 replication** | NSC on their deposited data and ours | their data: same 110 words, CV error 8.76% (8.8%), Rigdon 169 (197); printed table not reproducible in pamr; our texts: Pratt 193, Rigdon 29; swaps: Rigdon 169 -> 92, Pratt 42 -> 137, Cowdery 36 -> 81 | BOM-22 | the Rigdon result follows sample choice (their Rigdon is mostly 1864).
- **Schaalje 2011 ENSC replication** | published method, our texts | 225/239 chapters to unobserved author (theirs 175); our old ENSC 235 | BOM-22 | the "none of these" conclusion reproduces but depends on sample choices.

## 9. Access evidence

- **Wayne Sentinel BoM items** | OCR index | 6 items on 4 dates in 1830; byline ad 5 weeks; 19 Mar 1830 "will be ready for sale" notice (later found already documented by BYU) | BOM-33, BOM-61 | an apparent new find was already known.
- **26 June 1829 title page** | OCR vs page scan | scan confirms the full title page and "Golden Bible"; OCR returns 0 of 10 terms ("gattlmbible"); earlier negative withdrawn | BOM-33 | OCR absence is not evidence of absence.
- **Bookselling language** | Sentinel pages | 826 of 1,429 (58%) | BOM-33 | books were continuously advertised in Palmyra.
- **Josephus availability** | ads read on page images | Rochester bookseller in Palmyra Herald Jul 1822 (earliest); Wayne County Bookstore 1824; Palmyra Book Store 1826; Grandin's own stock 27 Nov 1828-spring 1829; Canandaigua 1824-25; Manchester library acc. 181-186 (~1827-1830, date vs mid-1829 unknown) | BOM-33 | the top paraphrase source was demonstrably on local sale during dictation.
- **Strong's 1818/1819 Palmyra lists** | read in full | none of the 33 candidate texts | BOM-33 | a genuine negative (read by eye).
- **Access table** | 33 texts scored 0-3 | 3: 15 (14 Josephus + Ontario Phoenix); 2: 3 (VoH 1823 and 1825, Lake Light); 1: 9 (Late War, Blake, Fox, Ethan Smith works); 0: 6 (Napoleon, Spalding, Simpson, Bayly, Nayler) | BOM-33 | no named proposed source reaches 3.
- **View of the Hebrews rescored via Grunder** | Utica Christian Repository review May 1825 | 1 -> 2 | BOM-33 | the one regional fact Grunder added.
- **"Historical Reader" ambiguity** | Palmyra ads 1827-1830 | unassignable (Hunt vs Blake); the one named-author Canandaigua ad (1825) is Blake's | BOM-33 | Late War access stays unproven.
- **Grunder catalog matching** | 500 entries | 139 in catalog (105 same year); 8 in access table | BOM-33 | proposed parallels mostly outside or after the corpus window.

## 10. Blind run and synthesis

- **Seal** | sealed set | 211 ids: 168 BoM chunks (121 x 2,000 + 47 x 5,000) + 43 decoys (22 candidate, 21 control) | BOM-32 | blinding was simulated (fresh AI session without key).
- **Decoy check** | right candidate first / control called match / candidate called match | Burrows 20/22; Cosine 15/22; GI 19/22, 0/21, 0/22; style 16/22 and 18/22, 0/21, 0 (10/22 achievable); candidate models 20/21/19 of 22, 0/21 at every size, 20/14/11 of 22 | results-first-read | 0 control false matches, but Cosine and 297M style fell below benchmark accuracy (calibration shift).
- **Who ranks closest (registered)** | 168 chunks | Cosine JS 131; Burrows JS 77, Hunt 47, Pratt 37; GI Pratt 74, JS 48; style 297M JS 150, 590M Cowdery 102; candidate models 125M pseudo-biblical controls 126, 297M JS 106, 590M Cowdery 109 | BOM-32 | the answer moves with model size.
- **Match calls (registered)** | chunks with any match | GI 0; style 0 (achievable rule at 50% FP: many); candidate models 10 / 5 / 3 | BOM-32 | essentially no matches.
- **Synthesis posterior** | registered Bayesian synthesis | "not in set" 0.744 (prior 0.5); Hunt 0.089, Spalding 0.085, Ethan Smith 0.082; identical at all sizes because only GI (weight 0.833 x 0.5) enters | BOM-35 | rests on one classical family; covers only three candidates.
- **Synthesis sensitivity** | prior grid, equal weights, independence, drop-one | prior 0.2-0.8 -> 0.42-0.92; equal weights ~0.99; independent chunks ~0.99999; dropping GI returns the prior | BOM-35 | the number is driven by modelling choices.
- **Synthesis placebo** | registered synthesis on decoys grouped by true author | Ethan Smith decoys "not in set" 0.588 (ES 0.191); Hunt 0.561; Spalding 0.511; controls 0.630 | BOM-38, data/synthesis/placebo | the synthesis leans "none" even on true authors' own text, so 0.744 carries little information.
- **Secondary synthesis** | post-1830 candidates added | "not in set" ~0.62; Pratt highest (~0.10) | BOM-35 | exposed candidates are not favoured.
- **Sweep result** | 23,872 authors, 22 discovery chunks | 0 leads (expected 0.035); nearest Wroe, Huntington, George Fox, Field, Sewel (MFW 0.58-0.76, style 0.31-0.50 vs thresholds 0.211 / 0.092) | BOM-32, BOM-39 | no unproposed author is close; sweep failed usability, so descriptive only.
- **Amendment 43 rerun** | quotations removed from candidate samples | Cosine JS 148; Burrows JS 91; GI JS 66 = Pratt 66; style 590M JS 99; candidate models JS 159 / 168 / 131; matches 2 / 2 / 0; synthesis unchanged 0.744 | data/blind/a43 | Cowdery's prominence was leakage; JS ranks closest consistently.
- **Amendment 44 register check** | JS revelations 1828-29 vs his 1831-33 ordinary prose (~11,600 tokens) | mean rank revelations 1.0-1.3 (models), 1.1-1.5 (style), Cosine 1.2, GI 3.6, Burrows 7.7; prose 5.4-6.3, 4.7-5.7, 3.3, 6.1, 2.7 | data/blind/a44 | closeness to JS runs through the revelatory register; Burrows reverses.
- **Amendment 45 dose check** | all units fine-tuned at the revelation sample's 3,039 tokens | revelation model first in 168/168 chunks at 125M and 297M (20 equal-dose rivals); 590M mean rank 1.63, first in 62 (Hunt slice beats it in 63% of chunks) | data/blind/a45 | the JS ranking is not a sample-size artifact at the two smaller sizes.
- **Unblinding failure** | first unblind attempt | stopped on a data-shape bug before revealing anything | BOM-32 | blinding integrity held.

## 11. Claims register

- **Claim verdicts** | 17 claims, rules written before results | supported 2 (c09 by rule, c17), contradicted 6 (c02, c07, c08, c13, c15, c16), mixed 4 (c01, c05, c10, c14), not addressed 1 (c04), untestable 4 | docs/claims-verdicts.md | every side's claims answered by pre-written rules.
- **CES Letter book list** | which sources the Letter names | View of the Hebrews, The Late War, The First Book of Napoleon; not Spalding | docs/ces-letter-books.md | Spalding is tested from other critics.

## 12. Simulated reviews (BOM-38) and protocol review

- **Protocol review (simulated)** | adversarial review of the pre-registration | 14 objections, 11 changes | BOM-03 | e.g. a JS null reported as "untestable", not "not a match".
- **Draft reviews (simulated)** | statistician, historian, stylometrist | 31 major points, all "major revision"; key: synthesis contradicts exclusion rule; posterior excludes the candidate ranked first; decoy calibration shift; Late War/Napoleon demoted post hoc; vernacular control missing; dose confound; H1c verdict too strong | paper/review/response_plan.md | several headline readings were narrowed; many minor items pending.
- **Post hoc decisions** | count of labelled post hoc amendments | 8, 13 (partly), 19, 20, 21, 25, 38, 41-45 plus D1, D2 | preregistration section 11 | the garden of forking paths is large and documented.

## 13. Incidents and process failures found and fixed

- **ALTO deletion** | extractor deleted 76 tarballs | per-word confidence for 158,960 pages lost; guard test added | BOM-50 | data-loss incident.
- **Results file with corpus text** | repair.json held 117 MB of fresh-author text | caught by push size limit; guard test added | BOM-58 | near-publication of licensed text.
- **Harvard text and personal data committed** | validation excerpts; IP address and email | excerpts replaced by an index; history rewritten | blog Log | privacy and licence slips.
- **JSP throttling** | automated fetch | blocked after ~165 requests; transcript service later failed for everyone | BOM-13 | access fragility of the key private source.
- **Benchmark fine-tunes discarded** | per-author fine-tuned models | scored then deleted; rebuild pending | BOM-72 | contrary to the publish-everything rule.

## 14. Not run or not resolved (for completeness)

- Genre hand validation and the 100-run perturbation (BOM-53, Amendment 4) | not run.
- Thematic dating (BOM-63) | not run.
- ALTO recovery and recalibration (BOM-50) | open.
- Register placebo (BOM-76) and JS prose over time (BOM-73) | planned, not run.
- Rebuilt benchmark fine-tunes (BOM-72); Part 2 (BOM-74 to BOM-86) | not started.
- Google-digitized HathiTrust volumes (~104k) not in the library (BOM-71).
- Manchester Josephus accession date; which "Historical Reader" was sold; Ontario Repository 1827-28 | unresolved.
- Recall loss of 4-gram borrowing under OCR | flagged to be measured, never measured.
- Verse/two-column records given empty genre excerpts | flagged, unmeasured.
- Volumes with 1-19 shared BoM strings in base-model training | requested by a simulated reviewer, not reported.
