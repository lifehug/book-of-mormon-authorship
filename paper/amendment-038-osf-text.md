# Amendment 38: the 1B model's recovery from a loss spike (BOM-27)

*Filed 2026-11-07. Post hoc. Evidence: `logs/large_pod/`, `timelocked_lm/train.py`, BOM-27 issue.*

---

**Amendment 38, filed 2026-11-07, post hoc (during training, before the 1B model is benchmarked or
used on any text).** The 1B time-locked model (Amendment 26) had a training-loss spike at step
~15,800 (loss 2.33 to 3.46, gradient norm 0.4 to ~150-770) that did not recover over the next ~450
steps and was worsening (loss up to 5.5). The only checkpoint, written at step ~15,909, was taken
after the spike began. Training was resumed from it at step 15,908 with the optimizer's moment
estimates reset and the learning-rate schedule multiplied by 0.5 for the rest of the run; every
other setting is unchanged. Within ~230 steps the loss returned to its pre-spike level (2.34) with
gradient norm 0.3. The registered peak learning rate (Amendment 2) is therefore halved from step
15,908 for the 1B only; the 125M and 297M models are unaffected. From now on the previous checkpoint
is kept beside the latest. The 1B is reported with this history.

**Addendum, 2026-11-07 00:35.** At half the rate the gradient norm rose again from step ~16,250
(median ~800 by step 17,350) while the loss crept up (median 2.35 to 2.44). Training was resumed a
second time from the step-15,909 checkpoint, again with fresh optimizer state, now with the
schedule multiplied by 0.25. The degraded checkpoints (steps 16,403 and 16,942) are kept.
