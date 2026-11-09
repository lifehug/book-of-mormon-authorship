# Amendment 41: V1 and V2 learning rates chosen per size on held-out training text (BOM-28)

*Filed 2026-11-09. Post hoc. Evidence: `data/benchmark/alm_mid_v1.json`, `alm_mid_v2.json`,
`logs/alm_pod_mid/pod_evidence/` (per-author scores), `alm/lr_select.py`.*

---

**Amendment 41, filed 2026-11-09, post hoc: decided after the 590M's V1 and V2 benchmark results,
before any rerun.** Amendment 23's secondary variants used learning rates fixed for the 297M: V1
fine-tunes at 1e-4 (ten times Amendment 22's 1e-5), V2 trains its classifier head and model at
1e-5. At 590M (Amendment 39) V1's closed-set accuracy fell from 0.936 (297M) to 0.627 and V2's
from 0.909 to 0.764; V1's fine-tuned models raised the loss on new text above the base model's by
0.81 nats on average (0.56 at 297M), i.e. the rate damaged the larger model. The registered runs
stand and are reported as measured. Beside them, for every size (125M, 297M, 590M), each
variant's rate is chosen from {1e-6, 3e-6, 1e-5, 3e-5, 1e-4} (`alm.lr_select_grid`) by the lowest
loss on the last 10% (`alm.lr_select_val_share`) of each benchmark author's training tokens (V1:
mean token log-loss) or windows (V2: class-weighted cross-entropy), the model fine-tuned on the
first 90%. The 110 benchmark tests are never read in the choice. V1 and V2 are then rerun at the
chosen rates on the full training text and judged by Amendment 22's rule, as
`alm_<size>_v1_lrsel` and `alm_<size>_v2_lrsel`, beside the registered variants, never in place
of them. No hypothesis, decision rule or threshold changes. Every fine-tuned model is kept and
published (owner, 2026-11-09).
