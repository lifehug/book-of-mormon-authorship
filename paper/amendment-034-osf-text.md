# Amendment 34: the synthesis's likelihoods (BOM-35)

*Filed 2026-11-06. Evidence: `docs/synthesis-plan.md`, `synth/model.py`.*

---

**Amendment 34, filed 2026-11-06, before any Book of Mormon text is scored.** Section 6.7 fixes the
prior, the method weights and the sensitivity analyses of the Bayesian synthesis but not how a
method's result becomes a likelihood. It is fixed as follows; the prior, weights and sensitivity
analyses are unchanged.

**Hypotheses.** Each candidate with a reliable confirmatory (pre-1830) sample, and "not in set";
candidates with only unreliable samples carry no prior mass but their scores are reported. Post-1830
samples (Amendment 5) are a separate, labelled secondary run. The internal narrators (6.3) are
reported beside.

**Likelihood.** Each method family is represented by the method that supplies 6.1's verification
score (classical: General Imposters; embedding: the style embeddings; authorial: the candidate
models). Per chunk, the observation is the candidate the family ranks first and 6.1's band for it.
Under candidate c, the pick has probability a (the family's benchmark closed-set accuracy) if it is
c and (1 - a)/(K - 1) otherwise, and the band has the probability the benchmark's positives (if the
pick is c) or open-set negatives (otherwise) fall in it; under "not in set", the pick is uniform over
the K candidates and the band follows the negatives. Band probabilities are add-0.5 smoothed. A
half's evidence from a family is the mean of its chunks' log likelihoods; the sum (chunks
independent) is reported as an upper bound.

**Combination.** Log posterior = log prior + the sum over families of w times the half's evidence,
with w the family's closed-set accuracy times its section 9 imitation weight; Amendment 7's equal
weights are run beside. Dating, the author sweep, access and manuscript evidence are reported beside
the posterior, not multiplied into it.
