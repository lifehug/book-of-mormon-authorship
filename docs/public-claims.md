# Public claims and how this study's results apply to them (BOM-42)

Written 2026-11-06, before the blind run (BOM-32) or the synthesis (BOM-35). The register of record
is `data/claims/register.yaml`: every claim, its source, and its decision rule (`supported_if` /
`contradicted_if`) fixed before any verdict. `python -m eval.claims table` fills
`data/claims/claims.json` with the evidence that exists today and marks the rest pending. Verdicts
are set by hand from the written rule after BOM-35, never changed to fit the result.

**The register takes no side.** It holds critical, apologetic and academic claims and applies the
same rules to all. A claim the study cannot test is reported as untestable, with the reason, as a
group, so the table is not read as a scorecard; untestable is not disproved. Nothing here bears on
inspiration or the truth of the book's contents.

## The claims

| Id | Claim (short) | Source (citation) | Our tests | Evidence files | Status today |
| --- | --- | --- | --- | --- | --- |
| c01 | *The Late War* (1816) shares unusually many rare phrases | Runnells, *Letter to a CES Director* (2013), https://cesletter.org; C. and D. Johnson (2013) | BOM-24, 25, 26 | `data/reuse/bom/rare.json`, `data/semantic/named*.json`, `triage.json` | evidence in; verdict after BOM-35 |
| c02 | *View of the Hebrews* shares themes closely enough to suggest dependence | Runnells (2013) | BOM-25, 26 | `named.json`, `named_null.json`, `triage.json` | evidence in |
| c03 | Cowdery's link to Ethan Smith's congregation makes transmission plausible | Runnells (2013) | none | - | untestable (biography, not text) |
| c04 | ~80 early modern English forms obsolete by 1830 | Skousen and Carmack, Critical Text Project vol. 3 (2018-) | BOM-29 | `data/dating/validation.json`, blind dating | pending the blind run |
| c05 | Its syntax is neither KJV nor period pseudo-biblical, so not imitation | Skousen and Carmack | BOM-29, 31 | dating validation, `transformer_validation.json`, `imitation.json` | pending the blind run |
| c06 | Dictation was under "tight control" | Skousen and Carmack; Gospel Topics | none | - | untestable (production mechanism) |
| c07 | Nearest shrunken centroids point to Rigdon and Spalding | Jockers, Witten and Criddle, *LLC* 23(4) (2008), https://doi.org/10.1093/llc/fqn040 | BOM-22, 32 | `replication_jockers_pamr.json`, `replication_ensc.json`, synthesis | pending the blind run |
| c08 | Narrators are distinct from each other and from 19th-century candidates | Larsen, Rencher and Layton, *BYU Studies* 20(3) (1980) | BOM-17, 32, 34 | `replication_holmes.json`, `data/manuscript/summary.json`, `scribes.json` | pending |
| c09 | With "none of the above" allowed, no 19th-century candidate is the author | Schaalje, Fields, Roper and Snow, *LLC* 26(1) (2011), https://doi.org/10.1093/llc/fqq029 | BOM-22, 32 | `open_set.json`, synthesis | pending |
| c10 | The style belongs to an American pseudo-biblical genre | Shalev, *American Zion* (2013) | BOM-18, 31 | `imitation.json`, dating validation | pending |
| c11 | Genetics cannot settle Book of Mormon population questions | Gospel Topics essays (2013-15) | none | - | untestable (genetics) |
| c12 | Dictated to scribes, largely without notes | Gospel Topics essays | none | - | untestable; used as the study's stated limit |
| c13 | Spalding's manuscript supplied the story or text | Howe, *Mormonism Unvailed* (1834); Cowdrey, Davis and Scales (1977) | BOM-24-26, 28, 32 | `rare.json`, `named.json`, `triage.json`, synthesis | evidence partly in |
| c14 | *The First Book of Napoleon* (1809) shares wording | named-source list, pre-registration 6.5 | BOM-24-26 | `rare.json`, `named*.json`, `triage.json` | evidence in |
| c15 | Cowdery or Rigdon wrote or shaped the text | named candidates, `docs/candidates.md` | BOM-28, 32, 35 | synthesis, unblinded | pending |
| c16 | The language reflects its 1820s environment | Brodie, *No Man Knows My History* (1945); Vogel, *Indian Origins* (1986) | BOM-29, 63 | dating validation, blind dating | pending |
| c17 | Narrators are not distinct and sit near Joseph Smith's revelations | Holmes, *JRSS A* 155(1) (1992) | BOM-22, 32, 34 | `replication_holmes.json`, `scribes.json` | pending |

Each row's full rule is in the register. Where the rule depends on the blind run, the reading is
the pre-registered one (6.1-6.3 as amended), at every model size side by side (Amendment 37); a
claim is "supported" only if every size agrees, "mixed" if they disagree.

## Before the blind run

Set `frozen: true` in the register and commit its SHA-256 with the analysis thresholds (BOM-32's
checklist). Claims added after that are dated additions with their own rule written first.
