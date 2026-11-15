## 13. Everything is public

The study is meant to be checked and redone. It was designed and run by one person
with AI assistance, and mistakes are possible; section 9 lists the ones found so far.
What stands behind the results is that every step can be found and rerun.

- **The plan and every change to it.** The pre-registration was frozen on OSF on 2026-10-15
  (https://osf.io/6ugxc/) and is mirrored in `paper/preregistration.md`. Its section 11 holds
  every amendment, dated, with post hoc ones labelled. Amendments 1 to 46 were also filed on OSF.
  From Amendment 47 on (2026-11-11) they are recorded in the repository only, committed and
  pushed before the results they govern exist, so that the commit time is the record. Decisions
  made after results were seen are also listed in `paper/deviations.md` and in section 9.1.
- **Code and configuration.** https://github.com/lifehug/book-of-mormon-authorship. Every
  analytic value (threshold, cutoff, chunk size, seed, model choice) comes from
  `config/preregistered.yaml`, and every results file cited in this paper records that file's SHA-256 and the git
  commit that produced it. `eval/README.md` lists every command: what it does, what it needs,
  what it writes, and how long it takes.
- **Results and data tables.** The catalog, genre labels, derived tables and every results file
  are in `data/`, each directory with a `SOURCES.md` saying where its files came from and how to
  rebuild them, and with checksums in `data/manifests/`. Results files hold names and numbers,
  never licensed text. The derived tables that the analyses read (phrase frequencies, feature
  matrices, genre labels, OCR scores) are published so that the statistics can be rerun without
  obtaining any restricted source.
- **Models.** The three period base models and the candidate models are published at these
  Hugging Face addresses:
  `etherfuse/timelocked-1830-125m`, `etherfuse/timelocked-1830-300m` (the 297M),
  `etherfuse/timelocked-1830-590m`, and `etherfuse/bom-authorship-candidate-models`. These two
  sets are enough to replicate. With the base models, every other fine-tune in the paper
  (benchmark, seeds, slices, placebo writers) can be rebuilt from the code, configuration and
  seeds for roughly $50 to $100 of rented GPU. With the candidate models, anyone can check the
  Book of Mormon ranking without any restricted text and without training anything. Other
  fine-tunes publish their scores, not their weights (owner's decision, 2026-11-11). The
  style encoder, the dating models and an earlier set of benchmark fine-tunes are also published,
  at `etherfuse/bom-authorship-style-encoder`, `etherfuse/bom-authorship-dating-models` and
  `etherfuse/bom-authorship-benchmark-finetunes`, and by the owner's decision of 2026-11-14 they
  are left up; `README.md` lists all seven addresses.
- **Simulated reviews.** Three simulated peer reviews (a historian, a statistician, a
  stylometrist), the response plan, the adversarial review and the research review of 2026-11-12
  are in `paper/review/`, `paper/adversarial-review.md` and `docs/research/`. All were written by
  AI models and are labelled as simulated. The study has had no independent human review.
- **The running account.** `paper/blog.md` is a dated, informal log of what was done and why,
  wrong turns included; `docs/method-improvements.md` records each change to the method and
  whether it worked.

**What is held back, and how to get it.** Four sources cannot be redistributed: the HathiTrust
researcher dataset (a signed agreement), Harvard's Institutional Books (accepted terms:
noncommercial, no redistribution), the Joseph Smith Papers transcripts (copyrighted), and one
purchased book, Rick Grunder's *Mormon Parallels*. For each, `docs/replication.md` gives numbered
steps to obtain the same access we had, and the public checksum manifests let a replicator
confirm they hold the same files. The large corpora themselves stay on local disk, covered by
those manifests. Nothing else is withheld. A replicator refused access to one of these sources
cannot check the results that depend on it from the raw text; the published derived tables are
there for that case.
