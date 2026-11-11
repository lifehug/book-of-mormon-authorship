# Part 2: does more data and a larger model change the conclusions? (plan, 2026-11-10)

Part 1 (the current paper) reports what the tests show at 125M-590M on 1780-1830 English. Its
two limits are measurement: no method passes the 5% false-match bar, so "no match" cannot be read
as "not this person"; and the library covers 1780-1830, while a source could be older. Part 2
asks two questions, in stages, each with a gate fixed in advance:

1. **Do the conclusions hold** with a larger model and a larger library?
2. **Can we say confidently "not a match"** for a candidate (false matches at or below 5% on a
   larger benchmark, with enough sensitivity that a "no" means something)?

**Commitment and order (owner, 2026-11-10; changed 2026-11-11).** Only Stage 0 is committed. On
2026-11-11 the owner moved Stage 0 ahead of the paper rewrite (BOM-36), so the paper can report it;
the reasoning for each Stage 0 item is in `paper/blog.md`, "Part 2, Stage 0". Weights from pods
go straight to Hugging Face. Amendments are recorded in the repo, not on OSF. Stage 1
starts only when the paper is fully written and the owner has reviewed Stage 0's results and said
go; every later stage likewise needs the owner's go after its gate. Each stage is a GitHub
milestone ("Part 2 · Stage 0" to "Stage 3") holding its issues.

The study still takes no position on the book's origin: it asks which known texts, of any period
before 1830, the text resembles.

| Stage | Issue | What | Time | Cost |
| --- | --- | --- | --- | --- |
| 0 | BOM-74 | Pre-register Part 2: success criteria, gates, stopping rule (amendment) | 0.5 day | $0 |
| 0 | BOM-75 | Larger benchmark (110 -> ~400 held-out tests), all sizes rescored | 1-2 days | ~$15 |
| 0 | BOM-76 | Cross-work decoys and a register placebo | 1 day | ~$10 |
| 0 | BOM-77 | Methods: several seeds per candidate model; larger candidate samples where they exist | 2-3 days | ~$40 |
| 1 | BOM-78 | 1.3B time-locked model, QK-norm, current data | 3 days | ~$650 |
| 1 | BOM-79 | Every test at 1.3B; gate 1 | 1 day | ~$40 |
| 2 | BOM-71 (open) + BOM-80 | More 1780-1830 text: Google-digitized volumes (owner's files) and the period's newspapers, cleaned and deduplicated | 1-2 weeks after files | $0 |
| 2 | BOM-81 | ~1.7B model on the expanded data; every test; gate 2 | 5-6 days | ~$950 |
| 2 | BOM-82 | Borrowing searches and author sweep over the expanded library | 3-4 days | $0 |
| 3 | BOM-83 | All English before 1830: 1700-1780 (Internet Archive, HathiTrust extension, ECCO-TCP) and 1473-1700 (EEBO-TCP), year-tagged | ~2 weeks | $0 (owner: HathiTrust extension) |
| 3 | BOM-84 | Year-conditioned 2-3B model; every test; gate 3 | 1-1.5 weeks | ~$1,500-2,500 |
| 3 | BOM-85 | Borrowing, story structure and dating against all pre-1830 English | ~1 week | $0 |
| - | BOM-86 | Part 2 write-up: same conclusions or not; which candidates can now be excluded | 3-5 days | $0 |

Totals: Stage 0 about a week, ~$65; Stage 1 about 4 days, ~$700; Stage 2 about 3 weeks after the
Google files, ~$950; Stage 3 about 4-5 weeks, ~$1,500-2,500. All stages: roughly 2-3 months
part-time, ~$3,200-4,200 in GPU. Each gate can stop the sequence: if a stage does not cut false
matches meaningfully, the next model is not trained and the remaining effort goes to data and
methods.
