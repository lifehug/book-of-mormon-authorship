# Amendment 27: triage of the parallels (BOM-26)

*Filed 2026-11-06. Evidence: `docs/triage-plan.md`, `semantic/triage.py`.*

---

**Amendment 27, filed 2026-11-06, before any parallel is triaged.** It fixes how the borrowing
searches' hits are sorted into biblical, common and specific (BOM-26), which the plan names but does
not specify. The searches' own results and rules are unchanged.

**What is triaged.** A hit is a pair: a Book of Mormon passage and a passage of another text.
(a) The paraphrase search (BOM-25): for each named proposed source (*View of the Hebrews* 1823 and
1825, *The Late War*, *The First Book of Napoleon*, Spalding's *Manuscript Story*), its stored
strongest pairs from the direct test (up to 50 each, `named.json`); for each of the 20 leading
non-Bible sources of the whole-corpus search, its 25 strongest parallels (score minus the query's
bar); and 250 parallels drawn at random (seed `bom26-sample`) from all non-Bible parallels.
(b) The rare-phrase search (BOM-24): every shared rare 4-gram of the named sources, and of each of
the 20 highest-density volumes up to 10 phrases (seeded), each with 40 words of context either side
in both texts. Exact reuse (BOM-23) was sorted by hand when it was reported (later quotations;
shared period phrases) and is not re-triaged.

**First pass.** The hosted model `claude-sonnet-5-5` (as Amendment 15; model-assisted) reads both
passages, the source's title and year, and answers BIBLICAL (both draw on King James wording or a
biblical narrative), COMMON (stock phrasing or ideas common in period writing of that kind) or
SPECIFIC (a particular shared detail, idea or wording that neither the Bible nor common phrasing
explains), with a one-sentence reason. Replies are logged; a transient failure is retried, never
recorded as an answer.

**Second review (simulated).** Section 9's human reviews are simulated by a model and labelled so.
An independent call to a different model, `claude-opus-5-5`, blind to the first label, applies the
same rubric to every first-pass SPECIFIC and to a seeded 10% of the others. Reported: Cohen's kappa
between the passes, the confusion table, and the list of pairs both call SPECIFIC with their
reasons. A pair counts as specific only if both passes say so.

**Pace.** At most 500 model calls an hour, 2 at a time (the owner's usage limit).
