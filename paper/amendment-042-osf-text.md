# Amendment 42: V2's run-to-run spread (BOM-28)

*Filed 2026-11-09. Post hoc. Evidence: `data/benchmark/alm_pilot_v2.json`, `alm_pilot_v2_lrsel.json`.*

---

**Amendment 42, filed 2026-11-09, post hoc: after V2 reran at its own registered settings and
moved.** At 125M, Amendment 41's selection chose V2's registered rate (1e-5), so its rerun repeated
the registered procedure and seed on different hardware (an H100 rather than the Mac); closed-set
accuracy moved from 0.900 to 0.764 and the open-set false-match rate from 0.282 to 0.591. V2's
single registered result per size therefore cannot be read alone. V2 is rerun at its registered
settings with `alm.v2_seed_runs` (5) further seeds per size (125M, 297M, 590M), on an H100, and
reported as the registered run beside the range and mean of the reruns. No hypothesis, decision
rule or threshold changes; every fine-tuned model is kept and published.
