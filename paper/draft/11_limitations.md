## 11. Limitations

**No method passes the benchmark.** Every method ranks well (up to 0.991) but none keeps false
matches at or below the registered 5% (best stable result 0.218, the candidate models at 590M).
Under the registered thresholds General Imposters and the style encoders cannot return "match" at
all, so section 6.2's two-family rule could not have supported any candidate, and the registered
synthesis cannot recognise an author's own text (section 7.3). "No match" therefore cannot be read
as "not this person".

**Methods differ in stability.** The primary language-model method reproduces exactly across
machines and improves with size; V1's registered learning rate broke at 590M; V2 swings from 9% to
98% false matches across seeds and carries no weight; the model-based methods are weaker than the
classical ones on deliberate imitation.

**Closest is confounded with register.** Joseph Smith's revelations are the only candidate sample
in the text's own scriptural register; his ordinary prose is not close, and at 590M another
writer's chronicle scripture competes. The methods cannot separate shared register from shared
authorship, nor the person who dictated a text from the person who composed it.

**Medium and channel.** The Book of Mormon is a dictated text taken down by scribes and set in
type from a manuscript; nearly every comparison text is edited print. Differences of medium
(dictation, scribal spelling, the absence of an editor) can move both attribution and dating.
King James masking removes aligned spans only; formulae such as "it came to pass" and "behold"
remain in the "original" text, and how much the features rest on them has not been measured.

**The local print environment.** How much of what was printed and sold in western New York before
1830 survives in the corpus is not measured: the national newspaper set holds almost nothing from
the region, and the access scores centre on Joseph Smith's documented reach.

**Small and uneven samples.** Joseph Smith's pre-1830 writing is 2,720 words and Cowdery's 1,310
(844 tokens without quotations); both are under the 10,000-word floor. Rigdon, Pratt and Phelps are
represented only by writing after 1830, by which time they had read the book. Samples mix
provenance (dictated, edited, posthumous); each tier is recorded.

**The borrowing and dating tests cannot speak to translation.** None separates genuine translations
of ancient texts from compositions presented as ancient (Amendment 9). The dating models learned
1780-1830 English from edited print; unedited vernacular may read to them as archaic.

**One person, simulated review and simulated blinding.** The study is designed and run by one person
with AI assistance. Every review step (adversarial, draft, peer) and the second triage pass are
simulated by AI models; the blind run's "fresh session" is a new AI session without the key, not
an independent analyst. None of this is independent scrutiny.

**The corpus.** OCR quality is uneven, and the wording searches miss an unmeasured but probably
large share of real shared phrasing in poor scans (a 4-gram survives about 41% of the time at 80%
word accuracy); a negative from poor OCR is not evidence of absence, as the 26 June 1829 *Wayne
Sentinel* title-page notice shows (present on the page image, 0 of 10 search terms found in its
OCR). Training volumes holding 1 to 19 of the text's 12-token strings (below the removal threshold
of 20) were kept and not reported; some catalog dates are wrong (corrected where the text names
later years); author names conflate namesakes and split variants; 72% of the original manuscript
is lost. Writers whose work did not survive in print, or is outside the 23,872 swept authors, are
not covered. The sweep failed its own usability test and is descriptive only.

**The models.** The time-locked models were trained on the period corpus, which includes held-out
authors' volumes used later for calibration (language modelling, not authorship supervision). The
fine-tuning settings were fixed for all sizes in advance and may not suit the largest. GPT-2 is
used on the benchmark only, since it read modern text possibly including the Book of Mormon.

**Post hoc decisions.** Every decision made after results existed is listed with its effect in
section 7.4 and labelled in the pre-registration.

**Access is not use.** The access table records documented availability, not reading.

**Planned and not run.** The hand validation of the genre labels and the 100-run perturbation that
would show whether label errors matter (BOM-53); thematic dating, whether the text's themes track
the 1820s (BOM-63); the register placebo (BOM-76); and Joseph Smith's prose over time (BOM-73,
in progress). Genre labels agree moderately between two model passes (84.9% on either label, 50.8%
exactly) and worst on early modern text.
