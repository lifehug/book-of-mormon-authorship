# SIMULATED review: historian

> **SIMULATED.** Written by an AI model (claude-opus-5-5) acting as a historian referee, 2026-11-10. No human reviewed this work. Shown: the draft and the pre-registration, SHA-256 `753deba893c96bfb08e7ddfaa15be64c81a3f89f7a138c86fe1d3eb4b8309368`.

## Summary
The paper reports an open-set, pre-registered computational study of the 1830 Book of Mormon text and asks three questions: whose writing it resembles (Q1), what it borrowed (Q2), and when its English dates from (Q3). It builds a large 1780–1830 print corpus and trains period-only language models. It masks text aligned to the King James Bible (KJV) and validates methods on known-answer tasks before a simulated-blind run. It concludes that no named candidate is matched and that a Bayesian synthesis favours "none of these" (0.744). It also finds no proposed source sharing specific wording beyond its genre, dates the grammar mostly before 1700, and finds that the methods rank Joseph Smith's 1828–29 revelations closest, which it attributes to shared register. The study is unusually transparent about its own post hoc steps, failures and leakage. Several historical framings, however, are stated more strongly than the evidence allows, and they mostly lean in one direction on candidates and sources. The candidate, source and access lists also leave out the parts of the historical record that matter most to the competing theories.

## Major points
1. **The headline posterior does not cover the candidates the debate is about.** The posterior includes only candidates with reliable pre-1830 confirmatory samples, which leaves Hunt, Spalding and Ethan Smith. Joseph Smith (2,720 words) and Cowdery (1,310 words) fall below the floor and are excluded. Rigdon, Pratt and Phelps have only post-1830 samples and are secondary. Yet the Abstract and Discussion place "none of these candidates 0.744" right after a list naming Joseph Smith, Cowdery and Rigdon. A reader will take it as evidence against the authorship theories that matter most, when it is not.
   - The posterior also rests on General Imposters alone, which cannot return *match* at its registered threshold.
   - Hunt and Ethan Smith are, historically, proposed *sources*, not proposed *authors*. A posterior over them is close to uninformative on the live questions.
   - **Fix:** state in the Abstract which candidates the posterior covers. Say plainly that Joseph Smith and Cowdery are untested as authors rather than disfavoured, and describe what the posterior can and cannot discriminate.

2. **The registered borrowing result for *The Late War* and *Napoleon* is demoted by post hoc reasoning.** Under H2's registered rule, *The Late War* (p 0.0006) and *The First Book of Napoleon* (p 0.0003) are significant parallels on rare phrases. They are then set aside on three grounds:
   - a post hoc within-genre comparison (Ilive's *Jasher*);
   - the observation that 2,044 volumes pass the rule;
   - an LLM triage with modest agreement (kappa 0.505).

   The Abstract and Discussion then say no source shares specific wording "beyond what its genre shares." This is not fair to the claim's proponents. "Late War dependence" is a live claim in the current literature.
   - **Fix:** report H2 as *supported* for these two sources under the registered rule, with the genre and triage readings as labelled secondary interpretations.
   - Print the 22 and 12 shared rare 4-grams with their contexts. The 1830 edition and both sources are public domain, so readers can judge for themselves.
   - Have the triage checked by a human reader with a stated protocol. Until then, "explained by King James wording or stock phrasing" should be called a model judgment.

3. **Several claim verdicts go further than the tests can.**
   - ***View of the Hebrews* "contradicted."** B. H. Roberts' parallels, and those of later critics, are conceptual: Israelite origins of the Indians, a buried record, Isaiah, the destruction of Jerusalem, prophetic calls to the gentile nation. They are not shared wording or event order. The passage-embedding, 4-gram and skeleton tests probe textual dependence. A null of 500 "sermon_devotional" volumes also absorbs much of the very register and themes at issue, and that genre label was chosen after the named sources' ranks were seen (Amendment 21).
   - **Brodie "contradicted (language only)."** Brodie's environmental argument concerned ideas: anti-Masonry, revivalism, debates over Indian origins and anti-Catholicism. A grammar-dating test cannot address it, so the verdict should be "not addressed" for the ideas.
   - **Spalding "as source" contradicted.** Spalding-Rigdon proponents (e.g. Cowdrey, Davis and Scales; Criddle) argue that the Oberlin *Manuscript Story* is *not* the source text and posit a lost "Manuscript Found." Testing the Oberlin manuscript leaves their claim as stated untestable. The verdict should say "Oberlin manuscript: no dependence; lost-manuscript claim: untestable."
   - **Cowdery and Rigdon "as author" contradicted.** Cowdery's pre-1830 sample is below the floor, and its main text was 40% quotation. Rigdon's post-1830 sample has two benchmark tests. Both should be "untestable" or "not supported," not "contradicted."
   - **Holmes 1992 "supported."** The paper itself says closeness to the revelations is confounded with register, so this belongs under "mixed."
   - **Larsen 1980 "contradicted."** Narrators separate well above chance (0.744 vs 0.277, p 0.001). The separation falls short of the distinct-author level, but narrator is confounded with dictation order: under Mosiah priority, the small plates (Nephi, Jacob) were dictated last. Narrator is also confounded with genre (sermon vs war chronicle). The fair verdict is "mixed / not separable by this design."
   - **Fix:** re-grade each verdict against what the test can actually observe, and add an explicit "untestable by these methods" note for each claim's non-textual component.

4. **The Joseph Smith comparison is confounded with the production channel, not only register, and its sample has uneven provenance.**
   - The 1828–29 revelations were dictated by the same person, mostly to the same scribe (Cowdery), in the same months, by the same reported process. Believing and naturalistic accounts both predict their closeness to the text, so the result discriminates nothing. The paper should say so for both sides.
   - Several revelations are dated only approximately in the Joseph Smith Papers. D&C 10 is dated variously to summer 1828 or spring 1829. D&C 18 (June 1829) shares phrasing with 3 Nephi and Moroni. The Amendment 43 rule keeping "same weeks" overlaps therefore depends on contested dates and on the dictation chronology.
   - The revelations survive mostly through later copies (Revelation Book 1, from 1831, and the edited 1833 Book of Commandments). They are not 1829 holographs.
   - The "ordinary prose" pool mixes the partly holograph 1832 history with scribe-written letters.
   - **Fix:**
     - Tabulate each sample text's witness, scribe, date range and shared runs.
     - Run a sensitivity check that drops D&C 10 and D&C 18 and every same-weeks overlap.
     - State the dictation chronology used (Welch's Mosiah priority, and the April–June 1829 timeline) and its uncertainty.
     - Note that no Joseph Smith decoy was sealed, so the "Joseph Smith closest" pattern has no blind check.

5. **The scribe claim is historically wrong as stated.** "Every scribed chunk is Oliver Cowdery's" does not match Skousen's identification of hands:
   - The surviving original manuscript includes passages by at least two other scribes, one probably John Whitmer.
   - The printer's manuscript was copied partly by an unidentified scribe 2 (roughly Helaman 13 through Mormon) and by Hyrum Smith.

   H1c's scribe arm is therefore possible on the printer's-manuscript hands, and the manuscript section could test whether copying errors track the hand.
   - **Fix:** state which witness the chunks come from (original manuscript, printer's manuscript, or the 1830 edition with John H. Gilbert's punctuation and compositor changes). Rebuild the scribe segmentation from the identified hands, and rerun H1c.

6. **The dating result needs an unedited-vernacular control before "early modern" is read from it.** The grammar model learns 1780–1830 English from *printed, edited* text. Nonstandard upstate New York and New England vernacular appears in the 1830 text and was largely removed in 1837 ("they was," "was" with plural subjects, "-eth" in odd places, "had ought"). Such vernacular is nearly absent from that training print and may share features with pre-1700 English.
   - This is the core of the dispute between the Skousen/Carmack reading and its critics. H3c controls only for KJV imitation, and the pseudo-biblical controls are mostly British printed authors (Snowden, Dodsley, Linning) plus Hunt.
   - **Fix:** add a control of unedited, period, regional manuscript or semi-literate prose. Candidates include Lucy Mack Smith's draft history, family letters, diaries and court records, and Joseph Smith's 1832 holograph. Report where it falls.
   - Report the result for the 1830 text and for the surviving original manuscript separately.
   - Until both are done, describe H3b as "dates early relative to period print," not as evidence for early modern origin or against 1820s composition.

7. **Corpus coverage of the local print environment is unmeasured, and access scoring centres on Joseph Smith.**
   - The corpus is strong on national book holdings but probably weak on the print most likely to be at hand in Palmyra and Manchester:
     - the *Wayne Sentinel* and *Palmyra Reflector*;
     - anti-Masonic pamphlets and newspapers of 1827–29, such as Morgan's *Illustrations*;
     - local sermons and camp-meeting literature;
     - school readers (the "Historical Reader" question bears directly on *The Late War*);
     - almanacs, chapbooks and Grandin's imprints.

     Chronicling America's coverage of 1820s western New York is thin.
   - The access table covers 33 texts and scores reach for Joseph Smith only. Score 3 counts the Manchester library's accessions as "documented reach," but no Smith membership or borrowing is documented there.
   - The key access routes in the competing theories are not scored:
     - Cowdery's family in Poultney, Vermont, where Ethan Smith was pastor;
     - Rigdon in Pittsburgh with the Patterson shop, for Spalding;
     - Cowdery as a schoolteacher, for school readers.
   - **Fix:**
     - Compile titles from Palmyra and Manchester advertisements and local imprint lists for 1820–29, and report the share present in the corpus.
     - Resolve bibliographically whether the advertised "Historical Reader" is Hunt's text.
     - Score access per candidate and per route, with "proximity" and "documented use" as separate levels.

8. **The production evidence confirms what all sides already accept and omits the tests that could discriminate.** Aural errors in the original manuscript against visual errors in the printer's manuscript are predicted by every account of dictation, believing or naturalistic.
   - The more debated questions are whether the original manuscript shows *visual* error types (eye-skip, dittography, line-length omissions) consistent with a dictator reading from a written page, and whether names were spelled out. Skousen's evidence (e.g. "Coriantumr") bears on the second.
   - The typed corrections should also separate in-line, immediate corrections from later ones, since some original-manuscript corrections were made during the copying of the printer's manuscript.
   - **Fix:** type visual-error categories in the original manuscript as well as the printer's, separate correction timing, and state which hypotheses each pattern does and does not distinguish.

9. **The "Every check on known text passed" sentence (Discussion) is misleading.** No method passes the registered benchmark. "None called a stranger's text a match" is trivially true for General Imposters and the style encoders, which cannot call a match at all.
   - **Fix:** restate this as "decoys were ranked at about benchmark accuracy; match calls are uninformative for two families."

## Minor points
1. The word counts are inconsistent:
   - Joseph Smith's pre-1830 sample is given as 2,720 words and as 2,702 words.
   - His ordinary prose is "about 11,600 tokens" in the paper but "about 11,300 words" in Amendment 44.
   - *The Late War* is said to have 9 printings, but Amendment 21 says "4 of 6."
2. The section numbering restarts in Part I and collides with the Introduction's "1." The imitation table in Part II section 4 is split by a blank line. The 590M row sits below the abandoned 1B row.
3. There is no reference list. Holmes 1992, Shalev, Skousen/Carmack, Brodie and Roberts are cited only by name. The paper should also cite the Joseph Smith Papers volumes and Skousen's *Critical Text* for the manuscript and scribe identifications.
4. Name the KJV edition used for masking. The Book of Mormon's Isaiah variants and the italics test depend on which edition is used.
5. Masking aligned spans only (6.8%) leaves pervasive KJV phraseology ("it came to pass," "behold") in the "original" spans. Report the attribution features' loading on such formulae.
6. Pratt and Phelps had no documented contact with Joseph Smith before he finished the text (Pratt from September 1830), and Hunt is a proposed source rather than a proposed author. Say briefly why each is a candidate, since they mainly serve as exposure controls.
7. Composite or collaborative authorship (Joseph Smith with Cowdery, or Spalding through Rigdon) is a common historical hypothesis. The single-author framework cannot test it, and the Limitations section should say so.
8. Ilive's *Jasher* (1829) was a Bristol reprint. State its American availability before using it to define "the genre."
9. Amendment 21 chose the null's genre label after the named sources' ranks were seen. The paper should flag this where the paraphrase table is reported, not only in the amendment list.
10. The phrase "simulated second review" of triage should be followed in the text by the kappa and an explicit statement that no human read the pairs.

## Recommendation
Major revision. The computational design is careful and admirably transparent, but several headline historical statements outrun what the tests can observe, mostly in favour of "no source, no candidate":
- the posterior's coverage;
- the demotion of the registered *Late War*/*Napoleon* result;
- the verdicts on *View of the Hebrews*, Brodie, Spalding and Cowdery;
- the scribe claim;
- the dating inference without a vernacular control.

These need correcting before the claims are fairly stated for every side.
