This is an AI-simulated fact-check (written by an AI model, not a human reviewer), dated 2026-11-14.

# Fact-check of `paper/paper.md` sections 1-13 (outline version 3)

Scope: sections 1 to 13 of `paper/paper.md` (same text as `paper/draft/v3/sec01.md` to `sec13.md`),
checked against the results files they cite. The abstract and section 14 were read only for
contradictions. Nothing was rerun; every value below was read from the file named. No file other
than this one was changed.

About 860 numeric claims were opened against a file. Sections 3, 5, 6 and 7 were checked
exhaustively (every table cell and every number in the prose); sections 2, 4, 8-13 by spot check
(section 2: 30+, section 9: 40+, the others 6 to 28 each).

Severity: **H** changes what a reader would conclude; **M** a wrong or unsupported statement that
does not change a conclusion; **L** rounding, labelling or wording.

Counts: wrong number 6, overclaim 12, framing 0 (2 notes), contradiction 6.

## What checked out

So that the tables below are read in proportion: every cell of the following matched its file.

- 3.2 rare-phrase table and 3.3 paraphrase table (`rare.json`, `named.json`, `named_null.json`),
  the triage counts (`triage.json`), the story-order figures for the named sources and the top 20
  (`skeleton/bom.json`, `top.json`), 3.6 (three `known_answer` files).
- 5.1 accuracy table (28 cells), both by-author tables (all counts, Holm p, gaps and ranges), the
  32-author figures, the passage counts, the Part 1 disagreement counts, the variants table, 5.3
  imitation table, 5.4 curve and normalisation tables, 5.5 list-size table (`clustered.json`,
  `prior_work.json`, `open_set.json`, `alm_*_p2/p3.json`, `imitation.json`, `list_size.json`).
- 6.1 both tables, 6.2, 6.3 both tables, 6.4 both tables, 6.4a, 6.5, 6.6 (`a44/people.json`,
  `a45/report.json`, `decoys_report.json`, `a54/report.json`, `a55_by_length.json`,
  `seeds_report.json`, `js_time/results.json`).
- 7 the 11-row by 8-method table (ranks and first-place counts), cross-work recognition, 7.8
  (`a43/per_candidate.json`, `decoys_report.json`, `sweep/calibration.json`).
- 4 (Jockers swap table, ENSC 225, fidelity 80%/0%), 8.1, 8.2, manuscripts, 9.2 table, 9.3, 10
  verdict table and totals.

## Section 1 and abstract

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| Abstract, "The whole library" | "no author rates closer than Joseph Smith's revelations" | Contradiction with section 14.4's own table and with the file. At the 11-episode profile one library author is closer than the 1830-34 revelations, and at the full profile twelve are closer than the 1828-29 revelations. | `data/sweep/bom_ranking.json` `rankings.large`: `wroe, john` score 0.6297 against `cand__joseph-smith__revelations__post1830` 0.6148, `rank_among_all` 2. `rankings.full`: `cand__joseph-smith__dictated__pre1830` `rank_among_all` 13. Section 14.4 table: "1830-34 revelations ... 2" at 11 episodes, "1828-29 ... 13" at full profile. | State it per profile size: first at 2 episodes and at full profile (1830-34 sample); second to John Wroe at 11 episodes; the 1828-29 sample 13th at full profile. Same fix in 14.4 ("No author in the library scores closer ... at any size they can enter") and 14.6. | H |
| Abstract, "The whole library" | "Searching all 23,872 authors with a style encoder that places the true author ... in its top ten 66% of the time" | The 66% is not measured over 23,872 authors. | Section 14.1: the second encoder's rows "are over the 18,288 authors not known to have been dead or under age"; the row over all 23,872 is the first encoder, 58.0%. | Say the 66% is over 18,288 authors, or give the figure for the full 23,872. | M |
| Abstract, "Borrowing" | "The books most often named as sources do not stand out from other books of their kind" | Overclaim by omission. Two of the three pass the registered rare-phrase rule; "of their kind" rests on a comparison Amendment 13 labels post hoc. | `data/reuse/bom/rare.json` `named`: Late War p 0.00065 rank 131, Napoleon p 0.00031 rank 63. `imitation_scripture.ranking`: Napoleon 4th and Late War 5th of 17; ranks 2 and 3 rest on one shared phrase each. `paper/preregistration.md` Amendment 13: "post hoc ... ranked within the curated pseudo-biblical list". | Add that two pass the registered rule and that the within-genre comparison is post hoc. | M |
| Abstract | "under six of eight methods" | Section 6.1 says "Six of the eight rankings": the eight count three model sizes and two encoder sizes separately. | `data/blind/a44/people.json` has 8 keys: 3 `alm_*`, 2 `style_*`, 3 classical. | "six of eight rankings (five method families at their several sizes)". | L |

## Section 2

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 2.1 | "Harvard's and HathiTrust's texts are licensed and the Joseph Smith Papers transcripts are copyrighted ... Everything else is public" | Contradiction with section 13, which lists four held-back sources. | Section 13: "Four sources cannot be redistributed ... and one purchased book, Rick Grunder's *Mormon Parallels*". | Add Grunder to 2.1. | L |
| 2.8 | "failed: training became unstable ... (Amendment 38)" | Amendment 38 is post hoc in the pre-registration and is not labelled here (it is listed in 9.1). | `paper/preregistration.md`: "Amendment 38, 2026-11-07, post hoc". | Add "post hoc". | L |
| 2.4, 2.5, 2.7 | "a single blind run", "The blind run scored" | Note, not a breach: blinding is labelled simulated in the title note, 2.0 and 12, but not at these uses. | - | Optional: "the (simulated) blind run" at first use in 2.4. | L |

Spot-checked and correct: 695,021 and the five source counts (`data/catalog/catalog.parquet`);
366,580 / 23,859 / 19,463; 11,494 / 1,502; 19,920 / 4,697; 1,883 / 0.083 / 38%; 2.5 / 11.9 / 24.9%;
84.9 / 50.8 / 15.1%; 18,336 of 268,811 (6.8%); 32.7% / 15.0%; 3.7% / 1.8%; 756 chunks; 121 + 47;
the eleven sample word counts; 30 authors, 37-60% against 80%; 202,816 volumes; losses 2.515 /
2.325 / 2.192; step 15,800.

## Section 3

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 3.4 "Checked first on a known retelling" (and section 11 item 1, "was shown to work first") | "It can find a retold story when there is one." | Overclaim by omission. The registered positive control had three texts; one was not found and is not mentioned. | Amendment 15: "positive control on Josephus, the Twelve Patriarchs and Jasher". `data/semantic/skeleton/controls.json` `controls.jasher`: `matched` 4, `order_p` 0.753, `passes` null; `twelve_patriarchs`: 8 events, p 0.003; `josephus`: 108, p 0.001. | Report all three: found for Josephus and the Twelve Patriarchs, not for Ilive's *Jasher* (4 events, p 0.75). | H |
| 3.5 intro (and section 10, first sentence) | "Each claim was registered with its decision rule before any result"; "before any result existed" | False for c13 to c17, which include two of the four books in 3.5 (Spalding c13, Napoleon c14). They were added after the borrowing results existed. | `git log -- data/claims/register.yaml`: c13-c17 added 2026-11-06 15:36 (the earlier version has 12 claims). `data/reuse/bom/rare.json` committed 2026-11-01; `named.json` 11-01; `named_null.json` 11-05; `triage.json` 11-06 09:57. The register's own comment says "written before any blind result exists". `frozen: false` is still set. | "c01-c12 were registered on 2026-10-18 before any result; c13-c17 on 2026-11-06, before the blind run and after the borrowing results." | H |
| 3.3 "Proposed parallels" | "only Josephus stands out" | Contradicted by the file: a second firmly matched entry stands out. | `data/semantic/grunder_ranks.json` `entries`: entry 203 (Josephus) and entry 298 (Owen, *Debate on the Evidences of Christianity*, basis `author+title`) both have `best.stands_out` true; `paraphrase_firm_vs_unproposed.stand_out.proposed` = 4 of 99 volumes (3 history, 1 legal). | "two entries stand out: Josephus and the Owen-Campbell debate (4 of 99 volumes)". | M |
| 3.2 table, row 3 | "*View of the Hebrews* (1825) ... 2 ... 0.37 ... 9,496" | Edition label. The scored volume is the 1823 edition. | `rare.json` `named.view_of_the_hebrews`: `catalog_year` 1823, `work_id` `institutional_books:AH3M5I`, title "...exhibiting the destruction of Jerusalem..." (the first-edition title; `data/access/access_table.csv` row `es-1823`). | Label the row 1823 (or say rarity is counted by text across 4 copies). | M |
| 3.2 Preparation | "rarity is counted by distinct text, not by volume ... (Amendment 8)" | Post hoc step not labelled. | Amendment 8: "post hoc, the 6.5 borrowing analysis counts document frequency by text". | Add "post hoc". | L |
| 3.2 table, column "p (95% interval)" | "0.0003 (0.0002-0.0031)" etc. | The intervals are a post hoc addition, not labelled. | Amendment 13: "post hoc ...: genre percentiles, 1,000-word block-bootstrap intervals". | Footnote the intervals as post hoc. | L |
| 3.1 Result | "Seventeen of those volumes are later texts ... all of it is short, loose religious stock phrasing" | The sorting of the 47 volumes into kinds is post hoc and not labelled. (The 0.16% itself follows from the registered date audit and seal: 16 volumes by date, 1 by seal.) | `docs/reuse-plan.md`: "that rule and the kinds below were written after seeing the table and are **post hoc**"; `data/reuse/exact/redated.json` `bom.covered_share_redated` 0.0026, `volumes_out` 16. | Label the classification post hoc. | L |
| 3.4, Philip's War | "one p-value that small arises by chance about 4 times in 10" | Arithmetic. | 1 - (1 - 0.008)^49 = 0.33 (file `order_p` 0.00799). 0.39 only if the threshold 0.01 is used. | "about 1 time in 3". | L |
| 3.4 Result | "the longest shared run is 9 ... (an edition of Josephus, p 0.24)" | Only the longest run's p is given. Three of the 20 leading sources have smaller uncorrected p-values, none at the registered level. | `data/semantic/skeleton/top.json` `sources`: `order_p` 0.019 (rank 6), 0.026 (rank 16), 0.028 (rank 3); all `order_significant` false. | Add "smallest p among the 20 is 0.019, above the registered level". | L |

## Section 4

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 4 table, Johnson row, and "The 2013 study" | "top 0.05% (p 0.0004) ... 30 books ... are denser"; "returns and is examined in section 3.2" | The same test appears in 3.2 with different values (rank 131 of 204,520 = top 0.064%, p 0.0006). They are two runs (the BOM-22 replication on 221,344 volumes and the BOM-24 search) and the text does not say so. | `data/benchmark/replication_johnson.json` `volumes` 221344; `paper/replication-report.md` line 20; `data/reuse/bom/rare.json` `named.the_late_war` rank 131, p 0.00065. | One sentence saying which run each figure comes from. | L |

## Section 5

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 5.4 first table, column "BOM-75, 430 tests" | "General Imposters ... 79%"; "ENSC ... 76%"; 640-test cells blank | The values are from a 500-test draw, not the 430 shared tests the column names (the note under the table says so, the header does not). On the shared tests the files give other values, and the blank 640 cells have values. | `data/benchmark/part2/open_set.json` `general_imposters`: `tests` 500, `open_set_fpr` 0.794; `ensc` 0.76. `data/benchmark/prior_work.json` `tails_p2_general_imposters.open_set_fpr` 1.0, `tails_p2_ensc` 0.833. `prior_work_classic_tails_p3.json` `summary`: General Imposters 1.0, ENSC 0.827. | Give the shared-test values (100% and 83% on 430; 100% and 83% on 640) or relabel the column. | M |
| 5.2 table and text; 5.5 summary; section 11 item 4 | "GPT-2, 355M ... 86%"; "86-92%" | Rounding. | `data/benchmark/alm_gpt2_medium.json` `verdict.open_set_fpr` 0.8545 (94 of 110). | "85%"; "85-92%". | L |
| 5.5 "None of these" | "nearly all of that gain is in the first step" | Overclaim: 8 of the 12 points. | `part2/open_set.json`: 0.751, 0.674, 0.635. | "two thirds of that gain". | L |

## Section 6

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 6, "Three kinds of Joseph Smith text" | "about 11,300 words pooled ... (5,039 words) ... (6,363 words)" | The two parts sum to 11,402. | `data/benchmark/alm_candidates_plan.json` words 5039 and 6363; `docs/results-inventory.md` line 65: "11,400 words". | "about 11,400". | L |
| 6.4 (and section 11 item 5, "land directly behind them") | "At the two smaller sizes every slice ... lands directly behind the 1828-29 pages" | Slightly more than the file shows. | `data/blind/a54/report.json` `slices.base.per_slice`: median rank 3 for six of twelve slices (2 for the other six). `slices.pilot`: one slice (grid10) has median rank 1 with the 1828-29 model at 2, as the table itself says. | "second or third at 297M; second at 125M except one slice that is first". | L |
| 6.7 | "whoever, or whatever, their source" | Note, not a breach: the sentence takes no position, but "whatever" is the one place in sections 1-13 that gestures at a non-human source. | - | Owner's call; "whatever their source" is enough. | L |

## Section 7

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 7 intro | "No sample other than Joseph Smith's 1828-29 revelations is called a match by any method at any size." | True only of the Amendment 43 rerun. The section promises the registered run "where it differs", and it differs here; the registered calls to other samples are stated nowhere in sections 6-9. | `data/blind/per_candidate.json` `alm_125m`: Pratt `match` 4, Cowdery 1829 `match` 4, revelations 2; `alm_297m`: Cowdery 3, revelations 2; `alm_590m`: Cowdery 3. | Add: "in the registered run the candidate models also called 4 chunks for Pratt (125M) and 4, 3 and 3 for Cowdery's 1829 sample; all were quotation." | M |
| 7 table, 7.1, 7.6, 7.7 | "Oliver Cowdery, printed after 1830 (44,338)"; "Parley P. Pratt (91,478)"; "W. W. Phelps (28,479)" | The table's ranks are from the Amendment 43 run, but these word counts are the registered samples before quotations were removed. | `data/benchmark/a43/alm_candidates_plan.json`: 44,330; 89,822; 28,450. Registered plan: 44,338; 91,478; 28,479. | Give both, or say the counts are before the quotation rule. | L |

## Section 8

No mismatch found in the numbers checked (215 segments, 78% / 7%, medians 1661 / 1736 / 1755, H3c
means and p-values, by-book p-values, 7 of 25, errors 23 and 10 years, 53-year shift, 8.2 table,
chance-corrected 0.645 / 0.514, homophone ratios 6.3 to 12.5 and p 2e-9). One sentence could not be
verified; see the last section.

## Section 9

No numeric mismatch in the 40+ values checked (9.1 effects, 9.2 table, 9.3 posteriors and placebo).

## Section 10

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 10, first sentence | "Seventeen public claims ... were written into a register ... before any result existed" | As in 3.5: 12 claims on 2026-10-18, 5 more on 2026-11-06 after the borrowing results. | See section 3 row 2. | Same correction. | H |

## Section 11

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 11 item 3 | "Five were reproduced with their own methods and data." | Only one study's data was available. | Section 4: "on the authors' own data where they deposited it"; section 2.0 row "Models and data public": "data deposited" for Jockers et al. only; `data/benchmark/replication_jockers_data.json` is the only rerun on published data. | "with their own methods, and one on its own data". | M |
| 11 item 2, heading | "The named books do not stand out." | Same as the abstract: the body of the item says two pass the registered rule. | See abstract row 3. | "do not stand out within their genre (post hoc comparison)". | L |

## Section 12

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 12, "No method can say 'none of these'" | "At that point the language models call a stranger's text a match 51 to 57% of the time on the 430-test benchmark." | The figure is the post hoc leave-author-out version (Amendment 55), given without that label; the registered split gives 63-75%. | `clustered.json` `verification_curve.*.raw.operating_points.registered_95.false_match`: 0.565, 0.519, 0.514. `part2/open_set.json`: 0.751, 0.674, 0.635. | Give both, labelled. | L |

## Section 13

| Location | Quote | Problem | Evidence | Suggested correction | Sev |
| --- | --- | --- | --- | --- | --- |
| 13, "Code and configuration" | "every results file records that file's SHA-256 and the git commit that produced it" | "Every" is not true of all JSON under `data/`. | No `config_sha256` in, for example, `data/sweep/pool_fusion_pilot.json`, `data/classic/multiverse_benchmark_summary.json`, `data/catalog/dedup_cross_source_check.json`. All results files cited in sections 3-9 do carry it. | "every results file cited in this paper". | L |

## Cross-references

Every section number cited in sections 1-13 exists in this version (2.0-2.8, 3.1-3.6, 5.1-5.5,
6.1-6.7 and 6.4a, 7.1-7.8, 8.1-8.2, 9.1-9.4, 14). No dangling reference found.

## Framing rules

- Divine inspiration: no sentence takes a position (one note under section 6).
- Owner's preference: none implied.
- Reviews: every review, second reading and research check is labelled simulated or as done by an
  AI model where it is mentioned (one note under section 2 on "blind run").
- Licensed text: no quotation from the Joseph Smith Papers transcripts, Harvard, HathiTrust or
  Grunder in sections 1-13. The only quoted strings of 25+ characters are the paper's own phrases
  and one event paraphrase.

## Could not verify

No file found, or the cited file does not hold the value. None of these is reported as wrong.

- 8.1: "the transformer ... still places it before them". `data/dating/h3c.json` holds the
  grammar and lexical comparisons only; no transformer comparison with the 25 control volumes.
- 5.5: "with overlapping ranges" for the 640-test false-match rates. `alm_*_p3.json` hold no interval.
- 2.4: Pratt's books "3.6%" shared. `docs/bom-overlap-analysis.md` gives 4.8% and 3.1% per book.
- 6.4: "80 shorter shared runs" (already marked CHECK). 5.3: "553 authors" and the search outside
  the period (already marked CHECK). 13: the three extra Hugging Face repositories (marked CHECK).
- 2.7: "The screen turned down 17 authors". 2.2: "81" of 100; "41%"; "0.12-0.18 on 300 pairs".
- 7.8: "about one random author in ten" for the gate; the names Wroe, Fox and Sewel.
- 6.3: the placebo writers' death years. 6.6: "(under the 2,000-word floor)" cells.
- 12: the 26 June 1829 *Wayne Sentinel* notice and "none of ten search terms".
- 1: "The largest corpus and candidate set" (a comparison with other studies; no file).
- 13: that the Hugging Face repositories are public (not checkable offline; the names match `README.md`).
