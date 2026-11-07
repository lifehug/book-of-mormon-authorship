# Amendment 39: a ~590M model with QK-norm in place of the unstable 1B (BOM-27)

*Filed 2026-11-07. Owner's decision. Evidence: Amendment 38, BOM-27 issue, `config/preregistered.yaml`.*

---

**Amendment 39, filed 2026-11-07 (owner's decision, after the 1B's failure; before any larger
model is benchmarked).** The 1B (Amendments 26, 38) became unstable at step ~15,800 and did not
recover at half or a quarter of its learning rate; it was abandoned (its pod and partial
checkpoints deleted; it can be retrained from scratch later with the fix below). In its place a
third size, **mid**: 28 layers, width 1,280, 20 heads, 592,849,664 parameters, with QK-norm (each
head's queries and keys layer-normalised before attention, the standard remedy for the attention-
logit growth behind late loss spikes at this scale) and peak learning rate 2.5e-4 (the registered
3e-4 x 0.8333, typical for this size). Data, tokenizer, schedule shape, batch and steps are as for
the other sizes. Amendment 37 applies with mid in place of the 1B: every model-based test runs at
125M, 297M and mid, side by side. The mid model is not exported to GPT-2 format (QK-norm does not
fit it); its release needs its own export.
