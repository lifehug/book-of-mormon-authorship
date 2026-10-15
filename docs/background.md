# Background

Research questions, prior work, what is new, and hard limits. Exported from the planning conversation of 2026-10-15; the pre-registration (BOM-02) supersedes this once published.

## The three research questions

- Q1 Attribution (open-set): which candidate authors, if any, does the text resemble? 'None of the above' must always be a possible answer.
- Q2 Borrowing: which earlier texts share wording or ideas with it, and is each overlap more than chance?
- Q3 Dating: when does its grammar and vocabulary come from (early modern English vs. 18th-19th century pseudo-biblical English)?

## Key decisions already made

- Python codebase.
- Pre-register the analysis on OSF before analyzing (#2). Any change after registration needs a dated public amendment.
- Adversarial collaboration: get a believing (e.g. BYU-associated) stylometrist and a critical scholar to approve the protocol before results exist (#3).
- The Book of Mormon text is sealed from all model training and tuning until the blind run in Phase 6 (#32). Exception: #22 replicates published studies with their original methods.
- Strip KJV quotations before attribution analysis (#16), and compare against genre-matched controls, especially other pseudo-biblical texts (#18).
- Stay neutral: the design must be able to return any answer. Report nulls and conflicts.

## What has already been done by others (so we build on it)

- Larsen, Rencher and Layton (1980): function-word wordprints; found internal narrators distinct and unlike 19th-century candidates. Criticized because biblical-register words (unto, behold, yea) dominate; that is genre, not author.
- Holmes (1992): vocabulary richness; https://www.physics.smu.edu/scalise/P3333sp08/ScienceReligion/MormonStylometric.pdf
- Jockers, Witten and Criddle (2008): nearest shrunken centroids pointed to Rigdon and Spalding; criticized as closed-set and for excluding Joseph Smith as a candidate.
- Fields, Schaalje and Roper (2011): extended nearest shrunken centroid (open set); https://scholarsarchive.byu.edu/jbms/vol21/iss1/4
- Overview of stylometry studies (believing side): https://scripturecentral.org/evidence/stylometry-1 and https://scripturecentral.org/archive/periodicals/journal-article/stylometric-analyses-book-mormon-short-history
- Johnson and Johnson (2013), WordTree: rare 4-grams across ~110,000 pre-1830 books pointed to The Late War (Gilbert Hunt, 1816); http://wordtree.org/thelatewar/ . Rebuttal: the same score rates the Gospel of Luke even higher, i.e. no proper null model; https://www.fairlatterdaysaints.org/answers/The_Late_War_theory_of_Book_of_Mormon_authorship
- Skousen and Carmack: argue for many early modern English features that disappeared before 1830. Shalev (American Zion) places the book in an American pseudo-biblical genre. Carmack compared against only four pseudo-biblical texts: https://interpreterfoundation.org/journal/is-the-book-of-mormon-a-pseudo-archaic-text

## What is new and makes this project different

- Corpus scale: Harvard Institutional Books 1.0 (983,004 public-domain volumes with cleaned OCR; https://arxiv.org/abs/2506.08300), plus HathiTrust, Internet Archive, Chronicling America, EEBO-TCP.
- A time-locked language model trained only on 1780-1830 text with the Book of Mormon held out. Commercial LLMs have memorized the Book of Mormon and KJV, which contaminates perplexity-based tests.
- Authorial language models (one fine-tuned model per candidate; attribute by lowest perplexity). Huang, Murakami and Grieve: https://arxiv.org/abs/2401.12005 and https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12225838/ . They also found content words carry more authorship signal than function words.
- Precedent: Dartmouth (Stropkay et al., Oct 2025) trained GPT-2 from scratch per author and confirmed the authorship of the 15th Oz book: https://arxiv.org/abs/2510.21958 . As far as we found, nobody has applied this to the Book of Mormon.
- Semantic text-reuse search (sentence embeddings + FAISS) to catch paraphrase, not just identical n-grams.
- A dating classifier trained on dated corpora, tested against a large pseudo-biblical control set.

## Hard limits (state these honestly in the pre-registration and paper)

- Joseph Smith's pre-1830 writing that is undisputedly his own is very small; attribution gets unreliable below ~5,000-10,000 words.
- Dictation and multiple scribes sit between any author and the page.
- Stylometry measures whoever produced the English text. It cannot decide the theological question of translation either way.
- Any method that cannot pass the validation benchmark (#21) and the imitation test (#31) is down-weighted or dropped.
