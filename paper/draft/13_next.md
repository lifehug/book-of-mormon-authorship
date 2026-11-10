## 13. What comes next (Part 2)

Three reasons to go further: false matches fell from 47% to 38% to 22% between 125M and 590M, and
the best-fit size for this data is about 1.3B; a source older than 1780 could have been used, and the
library covers 1780-1830; and only a method under 5% false matches lets "no match" mean "not this
person". Part 2 asks two questions: do the conclusions hold with a larger model and library, and
can any candidate be confidently excluded?

| Stage | What | Gate |
| --- | --- | --- |
| 0 | Pre-register success criteria and gates; grow the benchmark from 110 to about 400 tests; cross-work decoys and a register placebo (writers who died before 1827, and writers born after 1830 with no exposure, reported separately); several seeds per candidate model; larger candidate samples where they exist | the owner reviews Stage 0's results before any larger model |
| 1 | A 1.3B time-locked model with QK-norm on the present data; every test rerun | continue only if false matches fall by the pre-registered margin |
| 2 | More 1780-1830 text (Google-digitized volumes, the period's newspapers); a ~1.7B model; borrowing and sweep over the larger library | as above |
| 3 | All English before 1830 (1700-1780 and 1473-1700), year-tagged; a 2-3B model; borrowing, story structure and dating against all of it | as above |

Each gate can stop the sequence; if a stage does not cut false matches meaningfully, the next model
is not trained and the effort goes to data and methods. Only Stage 0 is committed. The plan, costs
and issues are in `docs/part2-plan.md` (BOM-74 to BOM-86).

**What each outcome would change.** If a larger model passes 5% false matches with useful
sensitivity, "no match" becomes "not this person" for the candidates with adequate samples, and
the registered synthesis can be replaced by one that can recognise an author. If the
register placebo ranks a writer who died before 1827 as close as Joseph Smith's revelations, the
ranking in section 10.1 measures register rather than person. If the wider library turns up a
source older than 1780, the borrowing tests will show it.
