# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft on outline version 3, 2026-11-14. Dave Taylor, with analysis by an AI model (Claude). Every
review step is simulated by an AI model and labelled so; the blinding was simulated (the scoring
ran without the key; the analyst is an AI model). Sections 1-13 were drafted by an AI model from
the previous draft and the results files, checked against those files by an AI model
(`paper/review/v3-factcheck.md`), and are under the owner's review. Repository: https://github.com/lifehug/book-of-mormon-authorship; pre-registration:
https://osf.io/6ugxc/ (frozen 2026-10-15; amendments 1-46 filed there, 47-58 recorded in the
repository; the post hoc ones labelled). Section 14 is exploratory and says so.*

## Abstract

We ask three questions of the earliest English text of the Book of Mormon (1830): who writes like
it, what it borrows, and when its language belongs. The tools are language models trained only on
text printed before 1830 (25.7 billion tokens; 125M, 297M and 590M parameters), the older
stylometric methods beside them, and a library of 695,021 catalogued items of 1780-1830. Every
method was first measured on texts of known authorship, the plan was registered before the
results, and each later change is dated and labelled.

**Borrowing.** With King James quotation set aside, 0.16% of the book matches earlier print, all
of it stock religious phrasing. Two of the three books most often named as sources pass the registered rare-phrase
rule, but do not stand out from other imitation scripture (a post hoc comparison), and no book
shares its plot. These tests cannot tell a translation from a
period book written to sound ancient, so the finding describes the text and not its origin.

**Authorship among named candidates.** On 55 authors of known work our models pick the right
author more often than every older method at every size. Among eight proposed candidates the
closest writing is Joseph Smith's revelations of 1828-29, in six of eight rankings (five method families at their several sizes); his
ordinary prose does not stand out under the language models. At the largest model size, writers
who could not have written the book score as close, so register explains part of the result. No
method can reliably answer "none of these".

**The whole library (exploratory).** A style encoder that places the true author of a known book
in its top ten 59% of the time among the 18,288 authors not known to have been dead (38% for a
book unlike its author's other writing; 727 known books) was run on all 23,872 authors with the candidates
beside them, at three profile sizes. A sample of Joseph Smith's revelations is first at two
sizes and second at the third, behind one library author, John Wroe, who also published
revelations. The rest of the head of the list is religious testimony, and dead authors are
over-represented in it: it is a kind of writing, not a set of possible authors.

The study does not argue for or against inspiration. Everything is public and rerunnable.

