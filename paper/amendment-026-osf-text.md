# Amendment 26: a 1B time-locked model (Amendment 2's size decision)

*Filed 2026-11-06. Note after filing: no 8-GPU machine was free, so the run uses 4 H100s; each step's 512 sequences are split four ways instead of eight, which changes nothing else. Evidence: `docs/alm-plan.md` (Results), `docs/timelocked-plan.md`, BOM-27.*

---

**Amendment 26, filed 2026-11-06, after the 125M and 297M models' benchmark results had been read;
the further amendment on size that Amendment 2 provides for.** On the registered decision point,
accuracy on the hard half of the benchmark is still rising steeply with size (false matches under
Amendment 25's check: the primary method 0.473 at 125M, 0.382 at 297M; the classifier-head variant
0.282, 0.136), and validation loss fell from 2.515 to 2.325. The owner decided to train a larger
model. This is outside section 5.2's registered 100-300M range and is reported as such; the 125M and
297M models and all their results stand and are reported beside it.

**The model.** 32 layers, width 1,600, 25 heads: 1,035,878,400 parameters with the 32,000-entry
tied embedding (`timelocked_lm.large_shape`). Everything else exactly as the 297M model, so that the
models differ only in size: the same training set, tokenizer, one pass over the same 25.7B tokens in
the same seeded window order, 524,288 tokens per step, AdamW, peak learning rate 3e-4, 2% warmup,
cosine to 10%, bf16, validation every 1,000 steps. It is trained on 8 H100 GPUs, each step's 512
sequences split evenly across them (a 2-process test reproduced the 1-process training loss and
gradient norm to seven digits).

**Use.** The 1B model is benchmarked exactly as the others (Amendments 22, 23 and 25) and published
as they were. If it does better on the benchmark it becomes the model used for BOM-28's candidate
models and the later scoring; the choice of model for those steps follows the benchmark result,
by Amendment 25's rule, and both are reported.
