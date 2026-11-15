## 1. Introduction

The Book of Mormon was published in 1830. Three questions about its English text have been argued
ever since: **who** produced the wording, **what** in it was borrowed from books already in print,
and **when** its language belongs. This paper puts all three to the earliest text with computational
tools, and reports what those tools can and cannot answer.

Two centuries of argument have not settled the questions, and four decades of computer studies have
reached opposite conclusions. Wordprint studies found the book's narrators distinct from each other
and from nineteenth-century candidates (Larsen, Rencher and Layton 1980). A classification study
pointed to Sidney Rigdon and Solomon Spalding (Jockers, Witten and Criddle 2008). A reanalysis that
allowed the answer "none of these" sent most chapters to an unobserved author (Schaalje, Fields,
Roper and Snow 2011). A rare-phrase study singled out Gilbert Hunt's *The Late War* (Johnson and
Johnson 2013). Each was criticised more for its setup than for its arithmetic: candidate lists that
force a pick; features that measure biblical register (the King James manner of writing) rather
than a person; choices made after seeing the data; and comparison libraries too small to say what
is unusual for the period. Section 4 reruns five of these studies and shows how far each answer
follows such choices.

What is new here:

1. **Models trained only on text printed before 1830.** A modern language model has read the Book
   of Mormon and everything written about it. Ours were trained from nothing on 25.7 billion tokens
   of English printed from 1780 to 1830, with the Book of Mormon and all later text kept out, in
   three sizes (125M, 297M and 590M parameters). To such a model, "ordinary English" means ordinary
   for 1830 (section 2.8).
2. **A larger comparison library and candidate set than the five studies rerun here.** The
   comparison library is the surviving digitized print of 1780-1830, 695,021 catalogued items,
   rather than a hand-picked shelf. Of the five earlier studies rerun in section 4, four compared
   candidates' samples only and the fifth searched about 100,000 books; the models here read
   202,816 period volumes (section 2.0). Eight named candidates are tested, as many as the
   largest of those studies, and afterwards every one of 23,872 authors in the library (sections
   2, 7.8 and 14). The comparison is with those five studies only.
3. **Every method tested on known answers first.** Before a method is read on the Book of Mormon it
   is scored on texts whose authors are known: how often it picks the right author from a list, and
   how often it wrongly says "match" when the true author is not on the list. Our own models and
   the methods of the earlier studies take the same tests and are reported side by side, at every
   model size. The earlier methods are baselines to compare against; they are not votes to be
   averaged with ours (section 5).
4. **A plan written in advance.** Thresholds, features, random seeds and model choices were fixed
   publicly before scoring (`paper/preregistration.md`). Every later change is a dated amendment,
   and each one made after results were seen is labelled post hoc wherever it is used (section 9).
   Every span of the text that follows the King James Bible, 6.8% of it, is set aside before
   authorship and dating are measured.
5. **Everything public and rerunnable.** The code, the result tables, the base models and the
   candidate models are public. The licensed source texts are not ours to give, so the steps to
   obtain each are published instead (section 13). One person ran this study with AI models; every
   review step in it (blinding, second readings, the reviews of the plan and the draft) was
   performed by an AI model and is labelled *simulated* where it appears.

What methods of this kind can see is the English on the page. They cannot see how that English came
to be, and in particular cannot separate a writer who composed a text from one who dictated or
translated it. The study therefore takes no position on the book's origin, on translation or on
inspiration.

**The result, stated once.** If the author is among the candidates, the closest writing is Joseph
Smith's revelations. Whether the author is among them, these tools cannot settle. Section 5.4 shows
why the second sentence is needed: no method tested here, ours included, can reliably answer "none
of these".

**How the paper is ordered.** Section 2 describes the scale of the test and how the library and the
text were prepared. Section 3 leads the results with borrowing, including the three books named in
the *CES Letter*. Section 4 reruns the earlier authorship studies. Section 5 scores every method on
known answers. Section 6 examines Joseph Smith's writing in depth, and section 7 takes the other
candidates one by one, then everyone else in the library. Section 8 covers dating and the book's
internal voices. Section 9 lists every correction and every post hoc step. Section 10 judges
seventeen public claims by rules written beforehand. Sections 11 to 13 give what held, the
limitations, and what is public. Section 14 puts the same question to the whole library.
