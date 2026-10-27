# Drafting rules for the 300-record genre validation (AI draft, human adjudication)

Judge the work, not the OCR: title, author, year and excerpt together. Where the excerpt is
Google/JSTOR boilerplate or OCR noise, judge from title and author if the title is unambiguous,
otherwise mark uncertain. A secondary label only when the second category applies to the work
as a whole, not to a part. Order inside a label pair does not matter to the scorer (sets).

1. Serials (newspapers, magazines, reviews, journals, Transactions/Proceedings carrying papers)
   -> newspaper_periodical primary; subject secondary when the whole run is in one subject
   (scientific_medical for science journals, sermon_devotional for religious magazines).
   Single newspaper pages (Chronicling America, IA sim_/per_ items) -> newspaper_periodical alone.
   A single offprinted article (JSTOR Early Journal Content) -> subject primary,
   newspaper_periodical secondary.
   Administrative reports of a society (annual report, council report) -> other.
2. Novels, tales, romances, drama, poems, broadside ballads, chapbook verse, satire
   -> fiction_narrative. Political satire or advocacy in verse -> fiction_narrative, legal_political.
3. Sermons, hymns, psalms, prayers, catechisms, tracts, theology, religious controversy,
   religious biography written for edification, prophecies in ordinary prose -> sermon_devotional.
   Religious reference (concordance, liturgical calendar/directory) -> other, sermon_devotional.
4. pseudo_biblical only for works written in imitated scriptural style (chapter-and-verse
   "Book of ..." / "Chronicles of ...", KJV diction throughout). A prophecy or religious work in
   the author's own prose is sermon_devotional, not pseudo_biblical.
5. History, biography, memoirs, lives, travels, voyages, antiquities, relations of events
   (including "strange news" pamphlets), editions of historical records -> history_chronicle.
6. Statutes, proclamations, petitions, parliamentary lists, trials, political letters and
   pamphlets, political economy, government reports, law lectures -> legal_political.
7. Natural philosophy, chemistry, mathematics, medicine, natural history, astronomy, agriculture
   as science, academic dissertations in those fields, lecture notes -> scientific_medical.
   Philosophy of every kind (mind, logic, metaphysics, aesthetics, morals) -> scientific_medical,
   other.
8. Grammars, dictionaries, catalogues, directories, indexes, almanacs, conduct and household
   books, cookery, trade and military manuals, school textbooks outside science -> other.
   Almanacs -> other, scientific_medical.
9. uncertain when title and excerpt together do not say what the work is.
