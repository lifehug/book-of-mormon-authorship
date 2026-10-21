# Amendment 3: genre tagging as multi-label, with few-shot prompting

*Paste-ready text for https://osf.io/6ugxc/. Reasoning in `paper/amendment-003-draft.md`.*

---

**Amendment 3, [DATE], before the corpus is labelled and before any calibration.**

Amendment 2 registered genre tagging as a fixed eight-label set with exactly one label per work.
Measurement since then shows that single-label assignment is the wrong instrument for this
corpus, and this amendment replaces it. No hypothesis, decision rule or threshold in the
original registration is changed, and the eight categories themselves are unchanged.

**What was measured.** Two language models from different families were run over 300 catalogue
records drawn from both the rule-decided and model-decided halves of the corpus. On the 60
records where the source archive determines the answer, both scored 97-98%. On the 239 records
requiring judgement they agreed only 72%, and inspection showed roughly a third of the
disagreements were not errors by either model: the works genuinely belong to two categories at
once. *Philosophical Transactions of the Royal Society* is a periodical and is scientific.
*Curtis's Botanical Magazine* likewise. The scheme forced an arbitrary choice and recorded the
arbitrary result as though it were a finding.

**Change 1: up to two labels per work, ordered.** A work receives a primary genre and, where a
second category genuinely applies, a secondary genre. Analyses needing a single value use the
primary; genre-matched control sets (BOM-18) match on either. A precedence rule was considered
and rejected: it resolves the ambiguity by discarding half the information, which would remove
every scientific periodical from the scientific control pool.

**Change 2: few-shot prompting.** The classification prompt carries three worked examples, one
of which is deliberately ambiguous and demonstrates the two-label case. The examples are fixed,
published with the code, and drawn from the comparison corpus, never from the Book of Mormon or
from any candidate author's writing.

**Change 3: an explicit uncertainty option.** The model may return `uncertain` rather than
guess. Records so marked are routed to human adjudication and are reported as a count.

**Change 4: two passes and a reliability figure.** Every record is labelled twice. Agreement
between passes is recorded per record and published as an aggregate, and disagreement is one of
the signals routing a record to adjudication.

**Validation, replacing Amendment 2's unqualified sample.** The hand-labelled validation sample
is drawn stratified rather than uniformly: it over-samples the ambiguous categories and the
records where the two passes disagree, and it includes records decided by rule as well as by
model, so the published agreement rate covers the rule path too. The sample size and the
stratification are published with the agreement rate, and the rate is reported separately for
the rule-decided and model-decided halves.
