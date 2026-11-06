# Amendment 24: the style embeddings (BOM-30)

*Filed 2026-11-05. Evidence: `docs/style-embed-plan.md`, `style_embed/`.*

---

**Amendment 24, filed 2026-11-05, before any style-embedding model is trained or scored.** It fixes
section 5.4's authorship-embedding model (LUAR-style), its validation on the benchmark (6.1, 7), and
what it provides to the author sweep (5.6, 6.6).

**Training authors.** The volumes of the time-locked model's training set (BOM-27: 1780-1830, the
Book of Mormon, the benchmark authors, the named candidates and the known-answer texts already
removed), grouped by catalog `author_norm`. Left out: volumes with no author, and corporate or
collective authors (an `author_norm` containing anonymous, anon, unknown, united states, great
britain, congress, parliament, society, church, committee, convention, assembly, association,
company, college, university, board of, council, legislature or court). A work is a group of an
author's volumes sharing the first six title words. An author qualifies with at least 2 works.
10% of qualifying authors, by a seeded hash (`bom30-heldout`), are held out of training entirely;
they monitor training and are the calibration pool for the sweep (6.6).

**Text.** The benchmark's word form, so that the embeddings can be used in the benchmark's own
trials and beside the classical method in the sweep: normalised text, lowercased word tokens
(`classic.features.tokenize`) joined by spaces, encoded with the time-locked tokenizer. Passages
are 128 tokens. Per author at most 16 works (seeded); per work 32 passages, each from a random
volume of the work at a random position (seed `bom30-passages`).

**Model.** The 297M time-locked base model (BOM-27) as encoder: a passage's vector is the mean of
its final hidden states; an episode (8 passages of one work) is the mean of its passages' vectors,
mapped by a linear layer to 512 dimensions and normalised to unit length. A longer text (a
benchmark sample, an author profile, a Book of Mormon segment) is one episode made of all its
passages.

**Training.** Each step draws 64 training authors; each gives two episodes from two different works
(so that topic and book cannot be what is learned). Loss: symmetric InfoNCE over the 128 episodes,
each episode's positive being its author's other episode, temperature 0.05. AdamW, learning rate
2e-5 for the encoder and 1e-3 for the linear layer, weight decay 0.01, 500 warmup steps, cosine
decay to 10%, 20,000 steps, bf16, seed `bom30-train`. One rented H100 (Secure Cloud; the owner set
a working cap of about $50); the text is deleted from the machine after the run and the deletion
checked. The final step's model is used; held-out retrieval accuracy is logged every 1,000 steps
and does not select the model.

**Benchmark (6.1, 7).** The benchmark's own trials (BOM-21: tasks, tests, references with each
test's span left out, imposter pools): a sample's vector as above; closed set by cosine distance
to each author's profile (all its reference blocks as one episode); verification by General
Imposters on the vectors with the registered settings; threshold and false-positive rate as for
General Imposters; passes at closed-set accuracy at least 0.90 and open-set false-positive rate at
most 0.05.

**For the sweep.** The trained model is the sweep's embedding signal (5.6). The held-out authors
above supply 6.6's 200 calibration books; the sweep's own rules are BOM-39's and BOM-47's and are
not set here.
