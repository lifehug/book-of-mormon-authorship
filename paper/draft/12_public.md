## 12. Everything is public

The study is meant to be checked and redone. Mistakes are possible; what makes up for them is that
every step can be found and rerun.

- **Pre-registration and amendments:** https://osf.io/6ugxc/ (frozen 2026-10-15; 45 dated
  amendments, each post hoc one labelled), mirrored in `paper/preregistration.md`.
- **Code and configuration:** https://github.com/lifehug/book-of-mormon-authorship. Every analytic
  value comes from `config/preregistered.yaml`, and every output records that file's SHA-256 and
  the git commit. Every command, what it needs and writes, and how long it takes, is in
  `eval/README.md`.
- **Models:** every trained model is on Hugging Face: the time-locked base models
  (`etherfuse/timelocked-1830-125m`, `-297m`, `-590m`) and every fine-tuned candidate, benchmark,
  style-encoder and dating model (`etherfuse/bom-authorship-*`), with checksums in
  `data/manifests/`.
- **Data:** the catalog, genre labels, derived tables and every result file (numbers and names,
  never licensed text) are in `data/`.
- **Simulated reviews:** three simulated peer reviews and the responses (`paper/review/`).
- **What is held back, and how to get it:** Harvard Institutional Books (noncommercial terms, no
  redistribution), the HathiTrust researcher dataset, the Joseph Smith Papers transcripts
  (copyrighted) and one purchased book. For each, `docs/replication.md` gives numbered steps to get
  the same access we had.
