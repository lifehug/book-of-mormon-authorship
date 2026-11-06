# Limitations (draft, BOM-36)

**No method passes the benchmark.** Every attribution method ranks candidates well (closed-set
accuracy up to 0.991 at 297M) but none keeps false matches at or below the registered 5%
(best: 0.136, V2 at 297M; `data/benchmark/open_set.json`). Under the registered thresholds General
Imposters and the style embeddings cannot return *match* at all (their calibrated match threshold
is 1.0, the largest possible score), so section 6.2's two-family rule cannot support any candidate
unless a larger model changes this; the owner's decision on how to report that is recorded with
Amendment 33. Results are therefore graded evidence, not attributions.

**The borrowing and dating tests cannot speak to translation.** None separates genuine
translations of ancient texts from compositions presented as ancient (Amendment 9; section 1.5 of
`results_so_far.md`). They describe resemblance and period, not process.

**One person, simulated review and simulated blinding.** The study is designed and run by one
person with AI assistance. Every review step (adversarial, draft, peer) and the second triage pass
are simulated by AI models and labelled as such; the blind run's "fresh session" is a new AI
session without the key, not an independent analyst. None of this is independent scrutiny.

**Small and uneven candidate samples.** Joseph Smith's undisputed pre-1830 writing is 2,720
dictated words; Oliver Cowdery's pre-1830 handwritten sample is 1,310. Both are below the
10,000-word floor and are reported as unreliable samples, not as non-matches. Candidate corpora
mix provenance (dictated, edited, posthumously published); each sample's tier is recorded.

**Dictation and scribes.** Several hands stand between any author and the page. The manuscript
evidence shows dictation-type errors but cannot say what was dictated from; the scribe/narrator
comparison (6.3) runs only after unblinding.

**The corpus.** OCR quality is uneven (measured, BOM-14/BOM-50); catalog dates are wrong for some
volumes (corrected where the text names later years, BOM-64); author names conflate namesakes and
split variants. 72% of the original manuscript is lost.

**Post hoc decisions.** Several choices were made after some results were seen and are labelled:
Amendments 8, 13 (partly), 19, 20, 21, 25, 26, 37, the disclosed slip in 31, and Amendment 33's
option (b) if used. Each is listed with its reason in section 11 of the pre-registration.

**Models.** The time-locked models were trained on the period corpus, which includes held-out
authors' volumes used later for calibration (language modelling, not authorship supervision);
the dating cross-check reports volumes the model trained on separately for this reason
(Amendment 29). The fine-tuning settings were fixed for all sizes in advance and may not suit the
largest. The GPT-2 ablation is benchmark-only, since GPT-2 read modern text possibly including the
Book of Mormon.

**Replication.** Licensed texts cannot be redistributed (Harvard Institutional Books, HathiTrust,
Joseph Smith Papers transcripts). Derived tables, checksums and the steps to obtain every source
are published (`docs/replication.md`), and every result is rerunnable from the repository with
those sources.

**Access is not use.** The access table records documented availability; it does not show that
anyone read a given book.

**A sweep with no leads says nothing beyond the corpus.** [RESULT: sweep usability and leads.]
