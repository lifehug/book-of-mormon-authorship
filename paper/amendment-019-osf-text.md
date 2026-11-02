# Amendment 19: 6.4's dating rule decided on segment medians (post hoc)

*Filed 2026-11-02. Evidence: `data/dating/validation.json`, `docs/dating-plan.md`, `dating/classifier.py`.*

---

**Amendment 19, filed 2026-11-02, after the dating classifier's validation and before any Book of
Mormon text is scored. Post hoc: decided after seeing validation results.** It changes how 6.4
decides H3a and H3b. H3c, the models, features, bins, data and every other rule are unchanged.

**Why.** 6.4 dates a text to a window if at least 80% of its segments' 90% intervals fall inside
it. The grammar model (Amendment 17) is honest about its uncertainty: on held-out authors its
90% intervals contain the true year 91% of the time, but they are about 85 years wide for
1780-1830 text, wider than the 51-year window. So only 14% of genuine 1780-1830 segments meet
the interval condition, and the rule could almost never date any text to H3a's window, whatever
its real date. Kept as written, H3a would be untestable.

**The amended rule.** Each segment's point estimate is the median year of its predicted
distribution. H3a holds if more than half of the segments' median years fall in 1780-1830; H3b
holds if more than half fall in 1473-1700; otherwise neither. This is H3a's and H3b's own wording
in section 2 ("places the majority of segments in the 1780-1830 window"; "places them earlier").
The interval rule is still computed and reported beside the decision, as is the lexical model.
H3c is unchanged: a permutation test of the Book of Mormon's predicted-year distribution against
the pseudo-biblical controls', accepted if p is above 0.05.

**How the amended rule performs on held-out text (grammar model, already computed).** Segments of
1780-1830 volumes: 85% have median years in the window (interval rule 14%). Volumes, each judged
on its own segments: 1780-1830, 1,464 of 1,875 called H3a, 80 H3b; 1473-1699, 3,729 of 4,144
called H3b, 48 H3a; 1700-1779, 217 H3a, 212 H3b, 568 neither. The King James text is called H3b.
The 25 pseudo-biblical controls of 1780-1830 split 10 H3a, 7 H3b, 8 neither: King James imitation
alone moves a genuine late text out of the window often, which is what H3c tests. Keyed (TCP)
1780-1809 segments reach the window less often than OCR segments of the same years (55% against
83%, 71 keyed segments); this is reported as a limitation.

**Config.** `dating.decision: segment_median`, `dating.majority_share: 0.5`,
`dating.early_window: [1473, 1700]`; `window` and `window_share` stay for the reported interval rule.
