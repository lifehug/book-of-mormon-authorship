# What derived data each source's terms allow us to publish (BOM-44)

BOM-44 publishes the derived tables the analyses read (feature counts per document, 4-gram
document frequencies, labels, scores) so the statistical claims can be checked with no access
application at all. Text is never published where terms forbid it. This file records, per
source, what the terms say about derived forms and what we do. Checked 2026-10-28.

| Source | Terms on the text | Terms on derived data | Our reading | What we publish |
| --- | --- | --- | --- | --- |
| Internet Archive (public-domain scans) | none beyond the item's own rights notes | none | free | everything derived |
| Chronicling America | public domain, no account | none | free | everything derived |
| TCP (EEBO, ECCO, Evans) | CC0 | none | free | everything derived |
| KJV, 1830 edition | public domain | none | free | everything, text included |
| Harvard Institutional Books 1.0 | IDI Terms of Use for Early-Access, clause 2: no sharing or redistribution "in whole or in part" | clause 3: derivative works may be shared only if "significantly transformed and cannot substitute for the original -- such as evaluations, summary statistics, or visualizations", with attribution (clause 4) | per-document counts of a fixed vocabulary of common words, n-gram document frequencies and labels are summary statistics that cannot substitute for a book | derived counts, with the clause-4 attribution, **once the owner agrees** |
| HathiTrust (`ht_text_pd_open_access`) | researcher agreement point 4: "may not distribute the dataset to others"; deletion on notice (3, 6) | silent | HathiTrust's own Research Center publishes page-level token counts for these same volumes (the Extracted Features dataset), which is more than we would publish; volumes deleted on notice lose their derived rows too | derived counts, **once the owner agrees** |
| Joseph Smith Papers transcripts | copyright, Intellectual Reserve | none granted | word counts of a text are facts, not its expression, but the owner of these transcripts is protective and the samples are small and below the BOM-43 floor | nothing beyond what is already public (KJV-mask offsets); derived counts stay in the private repo |

## Not reconstructable: the check every exported table must pass

A table is published only if the text cannot be read back out of it. Bag-of-words counts over a
fixed vocabulary carry no word order, and the vocabulary is the most frequent words (mostly
function words), so no passage can be reassembled. N-gram document frequencies are counts across
documents, not within one. `eval/derived.py` checks each table before export: no column holds a
position or an ordering, the vocabulary is capped at the registered maximum (1,000 words;
character n-grams likewise), and per-document vectors are counts only.

## Open question for the owner

Publishing tables derived from Harvard and HathiTrust volumes is publishing data, which waits for
the owner. The reading above says both are allowed; until agreed, those rows are written to the
private repo and the public tables carry the open sources only.
