# Known-author benchmark data (Phase 3)

| File | Built by | What it is |
| --- | --- | --- |
| `federalist/pg1404.txt` | fetched 2026-10-28 from https://www.gutenberg.org/cache/epub/1404/pg1404.txt (public domain) | The Federalist Papers, Project Gutenberg ebook 1404 |
| `federalist/papers.jsonl` | `python -m eval.federalist` | the 70 papers with one undisputed author under the standard attribution (Mosteller and Wallace 1964): Hamilton 51, Madison 14, Jay 5; the 3 joint and 12 disputed papers left out. Headings, author lines and PUBLIUS removed, since the author's own name would give the answer away |
| `pseudo_biblical_known.json` | by hand, 2026-10-28 | known-author pseudo-biblical works, one copy per text (Hunt, Snowden 2 volumes, Linning, Hughes), with why each was chosen and what was left out; text is the normalised, KJV-masked control text |
| `power.json` | `python -m eval.power` (seconds) | BOM-43's sample-size curves per method, both corpora, and the floors |
| `power_candidates.csv` | the same | each candidate's masked word count per sample type and the pre-1830 total, against the reference floors: testable / unreliable / untestable |

## Power analysis (BOM-43)

Section 7: a method's minimum sample is the smallest size at which closed-set accuracy stays at
or above 80%. Measured on known authors only (no Book of Mormon text). Text in 1,000-word blocks;
each curve uses one author set, those able to supply every size; 20 seeded trials per author per
size. Methods: Burrows and Cosine Delta (300 most frequent words), General Imposters, ENSC
(shrinkage 0 until BOM-21, so its floor is provisional).

**Test size** (how long the questioned text must be; references are the rest of each author's
text). Federalist (hamilton, madison, chance 50%): 1,000: burrows 98%, cosine 92%, general 90%, ensc 88% | 2,000: burrows 90%, cosine 92%, general 95%, ensc 85% | 5,000: burrows 100%, cosine 92%, general 100%, ensc 100% | 10,000: burrows 92%, cosine 95%, general 92%, ensc 92% | 20,000: burrows 60%, cosine 100%, general 98%, ensc 50%.
Pseudo-biblical (hunt, snowden): 1,000: burrows 100%, cosine 100%, general 98%, ensc 100% | 2,000: burrows 100%, cosine 100%, general 98%, ensc 100% | 5,000: burrows 100%, cosine 100%, general 100%, ensc 100% | 10,000: burrows 100%, cosine 100%, general 100%, ensc 100% | 20,000: burrows 100%, cosine 100%, general 100%, ensc 100%.

**Reference size** (how much known text an author needs; 5,000-word test). Federalist:
1,000: burrows 55%, cosine 55%, general 65% | 2,000: burrows 45%, cosine 52%, general 62%, ensc 65% | 5,000: burrows 68%, cosine 62%, general 72%, ensc 72% | 10,000: burrows 80%, cosine 80%, general 85%, ensc 80% | 20,000: burrows 90%, cosine 90%, general 90%, ensc 90%. Pseudo-biblical: 1,000: burrows 85%, cosine 75%, general 70% | 2,000: burrows 92%, cosine 90%, general 88%, ensc 90% | 5,000: burrows 95%, cosine 95%, general 92%, ensc 98% | 10,000: burrows 95%, cosine 92%, general 90%, ensc 98% | 20,000: burrows 95%, cosine 100%, general 100%, ensc 100%.

**Floors.** Reference: Federalist 10,000 words for every method; pseudo-biblical 1,000-2,000.
The pseudo-biblical set is easier than it looks: test and reference come from the same book (bar
Snowden's two volumes), so subject words help. The Federalist papers share one subject and are
the stricter test, so the candidate table uses its floor. Test size: 2,000- and 5,000-word tests
reach 85-100% in both sets, so the Book of Mormon's chunks (4.5) are usable for these methods. At
20,000-word tests Burrows' Delta and ENSC fall to 60% and 50% on the Federalist, because Madison's
reference is then nearly exhausted; that is a limit of the set, not of the chunk length.

**Candidates** (pre-1830 masked words, the confirmatory sample of section 3): Ethan Smith
277,352, Hunt 56,956 and Spalding 41,833 are testable by every classical method; Joseph Smith
3,082 and Oliver Cowdery 2,691 are below the strict floor ("unreliable": above the easy set's,
below the Federalist's); Rigdon, Pratt and Phelps have no pre-1830 text. Section 6.2 needs two
method families to agree before a candidate is supported; only the classical family exists so
far, and the curve is re-run as the language-model (BOM-28) and embedding (BOM-30) families land.
