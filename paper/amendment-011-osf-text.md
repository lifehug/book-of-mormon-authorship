# Amendment 11: the King James italics test

*Filed 2026-10-31. Evidence: `docs/italics-plan.md`.*

---

**Amendment 11, filed 2026-10-31, before any italic word has been counted in any text.** It adds
a test; no hypothesis, decision rule or threshold of section 6 changes.

**The test.** The King James translators printed in italics the English words they supplied,
which have no counterpart in the Hebrew or Greek. Within every King James span found by the
registered masking (4.4; at least 8 tokens at identity 0.60 or more), each King James word is
classed as kept, changed or dropped by the text, by word-level alignment to the 1769 Oxford text
with its italics marked (eBible.org). Rates: R_i, the share of italic words kept; R_r, the share
of roman words kept; D = R_r - R_i. 95% intervals by bootstrap over spans (10,000 resamples, seed
"bom62-boot"). Before measuring, 100 italic words drawn with seed "bom62-italics" from the
chapters the Book of Mormon parallels are checked against page images of the 1828 Phinney
edition (a model-assisted, simulated check) and the agreement is reported.

**Its known-answer check.** Amendment 9's set rarely runs parallel to the King James text, so
this test has its own reference groups: (a) independent period translations from the Hebrew or
Greek, measured on their translation text only (notes and dissertations, which quote the King
James text, are cut out at ranges recorded before counting): Lowth's Isaiah (1795), A New
Translation of Isaiah by a layman (1790), A New Translation of the Book of Psalms (1807) and
Wakefield's Matthew (1782); (b) the King James spans of the registered 1820s sermons control. The
test is shown to work if (a)'s pooled R_i interval lies below (b)'s and their D intervals do not
overlap; otherwise the Book of Mormon's rates are reported without interpretation. Amendment 9's
texts are scored where a text has at least 50 italic words in its spans; if fewer than two
presented-as-ancient texts qualify, Amendment 9's separation is reported as not computable for
this test.

**Reading the result, fixed now.** (1) If the Book of Mormon's R_i interval lies above (a)'s, it
reproduces the King James translators' supplied words more often than an independent translation
does: dependence on the King James English, including its additions. (2) Under (1), D within (b)'s
interval reads as keeping the supplied words like a quotation; D above (b)'s interval reads as
selective revision at the italics; both are dependence on the King James English. (3) If its
R_i interval overlaps (a)'s, the test does not show dependence on the added words. The project
draws no conclusion about inspiration. Published scholarship on the question, critical and
apologetic, is gathered after this filing and cited beside the result.
