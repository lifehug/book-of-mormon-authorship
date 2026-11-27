# "Parents" in Hebrew, and what translators from Hebrew wrote (BOM-132 follow-up), 2026-11-27

A reader said that "parents" could not stand in Nephi's Hebrew of about 600 BCE, because that
Hebrew says "father and mother". In BOM-132 design 3 the Book of Mormon's pre-Christian part
leans the other way from the translations: it has "father and mother" 2 times and "parents" 20
times. The King James Old Testament has 20 and 0, Young's Old Testament 29 and 2, and Jasher (1840)
16 and 2 (`data/lab/translation/hebrew_vocabulary/result3.json`, keys `pairings` and `controls`).
This note collects what the sources say about the Hebrew and about translators. It changes no
result and no config.

The sources were gathered by web search and by small read-only scripts over files we hold. Every
claim carries a URL, a file path or a verse. Points we could not confirm on a page are marked
**unverified**. The project takes no position on how the Book of Mormon text came to be. This note
only describes language and translation.

## Summary

- **Biblical Hebrew has no ordinary noun for "parents".** It names both parents ("his father and
  his mother"), or it uses a participle of *yalad*, "bear, beget": *yoledav*, "those who bore
  him" (Zech 13:3). The only possible noun is *horay* in Gen 49:26 (KJV "my progenitors"), and its
  reading is disputed. BDB reads it as "mountains"; Klein and the medieval commentators read it
  as "my parents".
- **Rabbinic Hebrew does have *horim*, "parents".** The earliest secure case we found is in the
  Tosefta (Tannaitic, roughly 3rd century CE): "הוריו", "his parents", at Tosefta Kiddushin 5:14.
  The Mishnah has none.
- **The Septuagint uses γονεῖς, "parents", only twice in books translated from Hebrew that
  survives.** At Esth 2:7 it stands for Hebrew "her father and her mother"; at Prov 29:15 it
  stands for "his mother".
- **Egyptian likewise seems to have no single word for "parents"** (**unverified**: the
  Thesaurus Linguae Aegyptiae was not searchable). Coptic uses the plural of "father", ⲉⲓⲟⲧⲉ,
  for both "parents" and "fathers".
- **English translators working from Hebrew before 1830 almost never put "parents" in the
  biblical text.** In the files we hold, Geddes 1792/1797, Newcome 1785, Blayney 1797 and the King
  James all write "father and mother" and "who begat him". Young (1862) is the one exception:
  "his father and his mother, his parents" at Zech 13:3.
- **Nobody seems to have published this argument about the Book of Mormon**, on either side.
  The apologetic literature discusses the word "goodly" in 1 Ne 1:1, not "parents". "First
  parents" is a stock English Protestant phrase: Milton, and the Westminster Shorter Catechism.

## 1. How Hebrew says "parents", period by period

### Biblical Hebrew: counts from the Hebrew Bible we hold

Source: Westminster Leningrad Codex with Strong's lemmas,
`data/corpus/lab/sources/translation/morphhb/wlc/*.xml` (OSHB; 23,213 verses). The script is in
the session scratchpad and is not part of the repo. It finds every verse where lemma 1 *'av*
("father") and lemma 517 *'em* ("mother"), both Hebrew rather than Aramaic, fall within 8 words
of each other. That gives 73 verses, which were then sorted by hand. Widening the window to the
whole verse adds only Gen 37:10 ("I and thy mother", not a paired phrase) and Deut 13:7.

| Construction | Verses | Examples |
| --- | --- | --- |
| Father and mother named together as one person's two parents | **48 verses, 50 occurrences** (Esth 2:7 and Zech 13:3 have two each) | Gen 2:24; 28:7; Exod 20:12; 21:15, 17; Lev 18:7; 19:3 (mother first); 20:9; 21:2 (mother first), 11; Num 6:7; Deut 5:16; 21:13, 18, 19; 22:15; 27:16; 33:9; Josh 2:13, 18; 6:23; Judg 14:2-6, 9, 16; Ruth 2:11; 1 Sam 22:3; 2 Sam 19:38 (Eng 19:37); 1 Kgs 19:20; 22:53 (Eng 22:52); 2 Kgs 3:2, 13; Esth 2:7; Ps 27:10; Prov 19:26; 20:20; 23:25; 28:24; Isa 8:4; Jer 16:3, 7; Ezek 16:3, 45 (mother first); 22:7; 44:25; Zech 13:3 |
| Father and mother in poetic parallel lines | 9 | Prov 1:8; 4:3; 6:20; 10:1; 15:20; 23:22; 30:11, 17; Mic 7:6 |
| Bare *'av va-'em* with no possessive, "father and mother" in general | inside the 48 | Esth 2:7 (אָב וָאֵם); Ezek 22:7; 44:25; Prov 19:26 |
| Qal active participle of *yalad* (H3205) used of a parent | 12 forms in 9 verses | Zech 13:3 ×2 (*yoledav*, masc. pl., "those who bore him", said of father and mother together); Jer 16:3 (*ha-yoledot*, "the women bearing them"); Prov 17:21 and 23:24 ×2 (*yoled*, "he who begets"); Prov 17:25; 23:25; Song 6:9; Jer 15:9; Jer 50:12 (*yoledet*, "she who bore") |
| Hiphil participle *molid*, "the one begetting" | 1 | Jer 16:3 (*ha-molidim*, "the men begetting them") |
| Relative clause with the perfect | 1 | Prov 23:22 *zeh yeladekha*, "who begat thee" |
| Participle of *harah* (H2029), "the woman who conceived" | 2 | Hos 2:7 (Eng 2:5) *horatam*; Song 3:4 *horati* |
| *horay* (H2029 form), a possible "my parents" | 1 | Gen 49:26, KJV "my progenitors" |

The *yalad* list in the table keeps only parent uses. The rest of the 42 participle forms the
script found are not parents: the midwives of Exod 1 and Gen 35, 38, and the simile "as a woman
in labour" (Isa 13:8; Jer 6:24; and others). Dan 11:6 *ha-yoldah* is disputed: KJV has "he that
begat her", Young "her child".

The only masculine plural participle used of both parents together is Zech 13:3, *yoledav*. That
is the closest Biblical Hebrew comes to a single word for "parents". BDB lists it under *yalad*,
Qal sense 3: "Zc 13:3 (×2), of both parents"
(https://www.sefaria.org/api/words/ילד, BDB Dictionary entry).

### Gen 49:26 *horay*

- BDB, under הָרָה: "On הוֹרַי Gn 49:26 v. הוֹר and הַר 1 c". Under הַר it says "prob. Gn 49:26 for
  MT הוֹרַי עַד (‖ גִּבְעֹת עוֹלָם)". BDB therefore reads "everlasting mountains", not "my parents"
  (https://www.sefaria.org/api/words/הרה). The Strong's page shows the same cross-reference
  (https://biblehub.com/hebrew/2029.htm).
- Klein, entry הוֹרִים: "parents (a hapax legomenon in the Bible, occurring Gen. 49:26 in the form
  הוֹרַי, 'my parents')" (https://www.sefaria.org/api/words/הורים).
- Medieval commentators read it as "parents". Ibn Ezra: "והורי כמו יולדי", "*horay* is like *yolday*,
  those who bore me". Radak: "the father is called *horeh* and the mother *horah*, because both share
  in the conception" (https://www.sefaria.org/Radak_on_Genesis.49.26; Ibn Ezra and Rashi are on
  the same verse at https://www.sefaria.org/Ibn_Ezra_on_Genesis.49.26).
- Onkelos renders it אֲבָהָתַי, "my fathers" (https://www.sefaria.org/Onkelos_Genesis.49.26).
- Sarna (JPS Genesis) says the "parents" rendering is "based on postbiblical usage". We saw this
  only as a quotation on the Balashon blog,
  https://www.balashon.com/2008/07/hora-and-horim.html; Sarna's own page is **unverified**.
- In the King James, H2029 is rendered "conceived" 32 times and "progenitors" once (Gen 49:26).
  This is our count from the Strong's-tagged KJV (`result3.json`, `hebrew.genesis_49_26`).

### Biblical Aramaic

There is no word for "parents" and no word for "mother". The Aramaic chapters of Daniel and Ezra
have only forms of *'av*, "father/fathers": Dan 2:23; 5:2, 11, 13, 18; Ezra 4:15; 5:12. This is
our own scan of the WLC Aramaic lemmas, and it agrees with a scan of Sefaria's text.

### Qumran

4QInstruction (4Q416 2 iii 15-19) says, in English, "Honor your father in your poverty and your
mother in your steps … because they are the furnace that formed you"
(https://intertextual.bible/book/4q416). The Hebrew is **unverified**: we recall "כור הוריכה", in
which *horekha* would mean "your conception", not "your parents". Checking it needs DJD 34
(Strugnell and Harrington 1999) or Goff 2013. We found no Qumran case of *horim* meaning
"parents".

### Mishnaic and Rabbinic Hebrew

We searched Sefaria's full-text index (https://www.sefaria.org/api/search-wrapper).

- **Mishnah:** no hits for הוריו, הורים, הוריהם or הוריך. The Mishnah says אביו ואמו, "his father
  and his mother".
- **Tosefta Kiddushin 5:14 (Lieberman):** R. Meir, "אוי לו לאדם שרואה את הוריו באומנות פגומה",
  "woe to the man who sees his parents in a lowly trade"
  (https://www.sefaria.org/Tosefta_Kiddushin_(Lieberman).5.14). This is the earliest secure case
  we found.
- The same saying appears in the Bavli at Kiddushin 82b (https://www.sefaria.org/Kiddushin.82b.2)
  and in the Yerushalmi at Kiddushin 4:11
  (https://www.sefaria.org/Jerusalem_Talmud_Kiddushin.4.11.8).
- **Midrash:**
  - Bereshit Rabbah 68:2 puns *heharim* ("the mountains") as *hahorim* ("the parents").
  - Bereshit Rabbah 76:2 has "מכבד את הוריו", "honours his parents".
  - Pesikta Rabbati 23:1.
  - Pirkei de-Rabbi Eliezer 32 and 35.
- **Jastrow**, הוֹר/הוֹרֶה: "teacher, father", plural הוֹרִים, "parents", citing Gen. R. 68, Pesik. R.
  23-24 and PdRE 32 (https://www.sefaria.org/api/words/הורים).
- **Ben Yehuda**, הוֹרָה I (https://www.sefaria.org/api/words/הורה), says the plural means father
  and mother together. On Gen 49:26 he notes that this is how "the ancients" read it, while "the
  moderns" emend the word to הררי עד, "mountains".

So *horim* is rabbinic, not medieval. It is rare in Tannaitic texts and more common in later
midrash.

### Medieval and modern

The classical name of the commandment stays כיבוד אב ואם, "honouring father and mother".
In Sefaria's corpus, the phrase כיבוד הורים, "honouring parents", is mostly modern (Peninei Halakhah,
Hirsch), and Maimonides' Mishneh Torah has no הוריו. This is only an indication, because the corpus
is uneven. *Horim* is the ordinary word in Modern Hebrew. We found no lexicon that dates when it
became the everyday word (**unverified**).

## 2. The Septuagint: γονεῖς, "parents"

The source is Rahlfs 1935, https://github.com/eliranwong/LXX-Rahlfs-1935, searched by lemma and
by surface form. Brenton's 1844 English is from https://ebible.org/Scriptures/eng-Brenton_readaloud.zip.
The Hebrew interlinears are at https://biblehub.com/interlinear/. In all, γονεύς/γονεῖς occurs **17
times**.

| Where | Greek | Hebrew under it | Brenton |
| --- | --- | --- | --- |
| Esth 2:7 | ἐν δὲ τῷ μεταλλάξαι αὐτῆς τοὺς **γονεῖς** | וּבְמוֹת אָבִיהָ וְאִמָּהּ, "at the death of her father and her mother" | "when her parents were dead" |
| Prov 29:15 | αἰσχύνει **γονεῖς** αὐτοῦ | מֵבִישׁ אִמּוֹ, "shames his mother" | "disgraces his parents" |

- **Books with a lost or partial Semitic original (6 hits):**
  - Tobit 10:12, in both the BA and S recensions.
  - Judith 5:8, which Brenton renders "ancestors".
  - 1 Macc 10:9.
  - Susanna (Theodotion) 3 and 30. At verse 30 the Old Greek has "father … and mother" instead.
- **Books composed in Greek (9 hits):** 2 Macc 12:24; 3 Macc 5:31, 5:49, 6:14; 4 Macc 2:10,
  15:4, 15:13; Wisdom 4:6, 12:6.
- **Sirach: none.** At Sir 3:7 the Greek is τοῖς γεννήσασιν αὐτόν, "those who begot him".
- **Zech 13:3:** *yoledav* is rendered with a participle, ὁ πατὴρ αὐτοῦ καὶ ἡ μήτηρ αὐτοῦ οἱ
  γεννήσαντες αὐτόν. Brenton: "his father and his mother which gave birth to him".
- **Gen 49:26:** εὐλογίας πατρός σου καὶ μητρός σου … ὀρέων μονίμων. Brenton: "the blessings of thy
  father and thy mother … above the blessing of the lasting mountains". The translators gave
  "and of thy mother" where the Hebrew has *horay*, and they also have "mountains". That reading
  of what they did is ours, not taken from a commentary.

The English Septuagint of Charles Thomson (1808), which we hold
(`data/corpus/lab/sources/translation/holybiblecontain0[1-4]thom/text.txt`), follows the Greek.
It has "On the decease of her parents" at Esth 2:7 and "shameth his parents" at Prov 29:15. Those
are the two "parents" in its Old Testament (`result3.json` counts 21 "father and mother" and 2
"parents" for `thomson_1808_ot`).

## 3. Egyptian

The Book of Mormon describes its own record as "in the language of the Egyptians" (1 Ne 1:2) and
written in "reformed Egyptian" (Morm 9:32).

- **Middle Egyptian:**
  - *it* means "father"; the plural *itw* means "forefathers".
  - *imy-ḥꜣt* means "ancestor (usually pl.)".
  - Faulkner's index has no headword for "parents". Source: Faulkner, *Concise Dictionary of
    Middle Egyptian*, OCR text at https://archive.org/download/pj1425.f3/PJ1425.F3_djvu.txt.
  - TLA lemmas for *jt* "father": https://thesaurus-linguae-aegyptiae.de/lemma/32820, and for
    Demotic https://thesaurus-linguae-aegyptiae.de/lemma/d727.
- **Coptic:**
  - ⲉⲓⲱⲧ means "father"; the plural ⲉⲓⲟⲧⲉ serves for both "parents" and "fathers".
  - Crum 86b glosses it "father (πατηρ, γονευς)". The data is at
    https://github.com/KELLIA/dictionary, file `data/supplemental_entries.tab`, entry C992.
  - The Sahidic NT has ⲚⲈϤⲒⲞⲦⲈ, "his parents", at Luke 2:41, and the same word for γονεῖς at
    Matt 10:21, Eph 6:1 and 2 Tim 3:2. It also uses ⲚⲈⲒⲞⲦⲈ for πατέρες, "fathers", at Eph 6:4
    (https://ebible.org/Scriptures/copshc_readaloud.zip).
- **Older Egyptian:** a stock tomb formula, "beloved of his father, praised of his mother",
  names the pair. We saw this only in secondary sources
  (https://www.wisdomlib.org/various/book/the-pyramid-texts/d/doc1857855.html). Whether Egyptian
  had a dedicated word for "parents" is **unverified**, because the TLA sits behind a bot check and
  we did not get past it.

## 4. English translations from Hebrew before about 1860

"Catalog" means `data/catalog/catalog.parquet`, which covers 1473-1830. T means `has_text` is
true and the OCR is on the data machine; F means the work is catalogued with no text. URLs are on
archive.org unless another site is named. They were checked against the archive.org metadata
API, except where marked. HathiTrust refused scripted access, so HathiTrust items appear only
through our catalog IDs.

| Work | Translator | Date | From Hebrew? | Free full text | In our catalog |
| --- | --- | --- | --- | --- | --- |
| *The Holy Bible … faithfully translated from corrected texts of the originals*, vol. 1 (Genesis to Joshua) | Alexander Geddes | 1792 | yes (his corrected Hebrew) | https://archive.org/details/bim_eighteenth-century_the-holy-bible-or-the-b_1792_1 | T, same ID |
| Same work, vol. 2 (Judges to Chronicles; the text shows it is the 1797 volume, though catalogued "1792_2") | Geddes | 1797 | yes | https://archive.org/details/bim_eighteenth-century_the-holy-bible-or-the-b_1792_2 | T, same ID; also HathiTrust nyp.33433021030626 (F) |
| *Critical Remarks on the Hebrew Scriptures* | Geddes | 1800 | commentary | https://archive.org/details/bim_eighteenth-century_critical-remarks-on-the-_geddes-alexander_1800 | T |
| *A New Translation of the Book of Psalms* | Geddes (posthumous) | 1807 | yes | Google scan `anewtranslation00geddgoog` | Harvard AH5KIN (T, private) |
| *A New Family Bible and Improved Version* | Benjamin Boothroyd | 1818-24 | yes | https://archive.org/details/ENGNFB_DBS_HS (vol. 1); 1853 one-volume reprint https://archive.org/details/cu31924029268617 | Harvard AH586T, 1824 (T, private); archive.org ENGNFB_DBS_HS (F) |
| *Isaiah: A New Translation* | Robert Lowth | 1778 | yes | https://archive.org/details/bim_eighteenth-century_isaiah-a-new-translatio_1778 | 1795 edition isaiahnewtransla01lowt / 02lowt (T); Harvard 1815 AH6S4S (T) |
| *Jeremiah and Lamentations: A New Translation* | Benjamin Blayney | 1784 | yes | https://archive.org/details/bim_eighteenth-century_jeremiah-and-lamentation_blayney-benjamin_1784 | T; Harvard 1810 AH5JQR (T) |
| *Zechariah: A New Translation* | Blayney | 1797 | yes | https://archive.org/details/zechariahnewtran00blay | T |
| *An Attempt towards an Improved Version … Twelve Minor Prophets* | William Newcome | 1785 | yes | https://archive.org/details/bim_eighteenth-century_an-attempt-towards-an-im_1785 | T; 1809 edition, several copies |
| Same series, *Ezekiel* | Newcome | 1788 | yes | https://archive.org/details/bim_eighteenth-century_an-attempt-towards-an-im_1788 | T |
| Kennicott, *Vetus Testamentum Hebraicum* | n/a | 1776-80 | Hebrew collation, not a translation | not searched | only *A Method of Reading Hebrew*, 1780 (T) |
| *The Holy Bible, Newly Translated from the Original Hebrew* | John Bellamy | 1818 (incomplete) | yes (claimed) | Google Books full view https://books.google.com/books?id=SP1PAAAAYAAJ | HathiTrust chi.58864321, chi.58864441, chi.58864561, nyp.33433017068481 (F) |
| *The Law of God* (Pentateuch) | Isaac Leeser | 1845 | yes | https://archive.org/details/leeser-torat-ha-elohim-philadelphia-1845-images_202402 | not held (after 1830) |
| *The Twenty-Four Books of the Holy Scriptures* | Leeser | 1853 | yes | https://archive.org/details/twentyfourbookso1853lees | not held |
| *The Hebrew Scriptures* (a revision of the KJV) | Samuel Sharpe | 1865 | a revision against the Hebrew | https://archive.org/details/hebrewscriptures00shar | not held |
| *The Holy Bible … with Amendments of the Language* | Noah Webster | 1833 | no, a revision of the KJV's English | https://archive.org/details/TheHolyBible_201607 (a user upload) | not held |
| *The Holy Bible … Translated Literally* | Julia E. Smith | 1876 | yes | https://archive.org/details/holybiblecon00smit | not held (later context only) |
| *The Holy Bible* (Old Testament from the Septuagint) | Charles Thomson | 1808 | no, from the Greek | https://archive.org/details/holybiblecontain01thom (vols 01-04) | catalog F; text in `data/corpus/lab/sources/translation/` |
| Young's Literal Translation | Robert Young | 1862 | yes | text from https://bible4u.net (public domain; our copy `ylt_txt.tar`) | `ylt_txt.tar` in lab sources |
| *Mahzor* (Ashkenazi festival prayers): New Year, Atonement, Tabernacles, Pentecost | David Levi | 1794-96 | yes | https://archive.org/details/bim_eighteenth-century_mahzor-le-rosh-ha-shana_1794; `…mahzor-le-yom-kipur-ke-m_1795`; `…mahzor-le-sukot-ke-minha_1795`; `…mahzor-le-shavuot-ke-mi_1796`; Passover `mazorlepesaformo00jews` | T for the four bim items; F for the `mahzor-l…-david-levi` copies |
| *Order of the Forms of Prayer* (Sephardic) | Levi | 1789-93 | yes | not found free; 1810 Daily Prayers edition https://archive.org/details/seder-hatefilot-david-levi-and-s-m-ximenes-1810 | 1810 edition (F) |
| *Lingua Sacra* (grammar and dictionary) | Levi | 1785-87 | reference work | https://archive.org/details/bim_eighteenth-century_lingua-sacra-in-three-p_levi-david_1785_1 (and _2, _3) | T |
| Prayer book (Ashkenazi) | (Abraham) Alexander Alexander, with B. Meyers | 1770; 2nd ed. 1788 | yes | not found free | not held |
| *Prayers for Shabbath, Rosh-Hashanah, and Kippur* (New York) | Isaac Pinto (attributed) | 1766 | yes | https://archive.org/details/bim_eighteenth-century_prayers-for-shabbath-ro_1766 | not found in catalog |
| *Miscellaneous Discourses … Scribes and Pharisees*, with the Mishnah tracts Shabbath and Eruvin | William Wotton | 1718 | yes | https://archive.org/details/bim_eighteenth-century_miscellaneous-discourses_wotton-william_1718_1 (and _2) | not held |
| *The Reasons of the Laws of Moses* (Maimonides, *Guide*) | James Townley | 1827 | from Latin or Hebrew (**unverified**) | https://archive.org/details/reasonsoflawsof00maim | T (also Harvard 32044048296412) |
| *The Main Principles of the Creed and Ethics of the Jews* (Maimonides, *Yad*) | H. H. Bernard | 1832 | yes | https://archive.org/details/mainprinciplesof00maim | not held (after 1830) |
| *The Book of Jasher* (Sefer ha-Yashar) | Moses Samuel (uncredited); published by Noah and Gould | 1840 | yes | https://archive.org/details/bookofjasherrefe00sefe | not in catalog (after 1830); text in lab sources |
| *Annotations upon the Five Books of Moses, the Psalms and the Song of Songs* | Henry Ainsworth | 1616-27 | yes | 1843 reprint https://archive.org/details/annotationsonpen01ains | TCP A11649, 1627 (T) |
| *The Book of Psalmes: Englished both in prose and metre* | Ainsworth | 1612 | yes | https://archive.org/details/bookofpsalmeseng00ains | TCP A27792, 1644 edition (T) |

Some of the volumes catalogued at 1836 under "Lowth/Newcome" are a different book, *A Literal
Translation of the Prophets*. Do not confuse them with the works above.

## 5. Who has discussed "parents" in the Book of Mormon

These sources came from a web search that was fairly shallow; "nothing found" means only that
the search did not surface it.

- **Apologetic.** The writers discuss the word "goodly" in 1 Ne 1:1, not "parents":
  - Hugh Nibley, *Teachings of the Book of Mormon*, Semester 1, Lecture 2 (FARMS 1993), pp. 15-28,
    https://scripturecentral.org/archive/books/book-chapter/lecture-2-introduction-nephis-heritage.
    He compares the Egyptian autobiography of Kai.
  - Nibley, "Lehi in the Desert, Part II", *Improvement Era*, February 1950. He compares Egyptian
    colophons, which give "the names of his parents and a word in praise of their virtues"
    (https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/nibley/2020-03-16/ie_53.02_hugh_w._nibley_lehi_in_the_desert_february_1950_102-4_155-59.pdf).
  - Matthew L. Bowen, "Nephi's Good Inclusio", *Interpreter* 17 (2016), reads "goodly" as a pun on
    Egyptian *nfr*, "good" (https://scholarsarchive.byu.edu/interpreter/vol17/iss1/14).
  - Book of Mormon Central, KnoWhy #445, "What Is So Good about Nephi's Name?", 2024
    (https://scripturecentral.org/knowhy/what-is-so-good-about-nephis-name).
  - Skousen's *Analysis of Textual Variants*, Part One: no entry on "parents" surfaced. His text
    was not read, so this is **unverified**.
  - Tvedtnes, Parry's *Hebraisms*, Gardner's *Second Witness* and the FAIR wiki: nothing found.
- **Critical.** Nothing found that makes the Hebrew-word argument:
  - MormonThink, the CES Letter, Mormon Stories, Vogel, Palmer, Reddit, Campbell's *Delusions*
    (1831) and Howe's *Mormonism Unvailed* (1834) were checked. The full texts of Campbell and Howe
    were not searched.
  - The one related point we found is about English sources, not Hebrew: bookofmormonfixed.com
    (anonymous) notes that "of goodly parents" occurs in English books before 1830. It was seen in
    a search snippet only, because the site refused the connection: **unverified**.
- **The language point itself, not tied to the Book of Mormon:** the Balashon blog, "hora and
  horim", 18 July 2008 (https://www.balashon.com/2008/07/hora-and-horim.html). It says biblical
  Hebrew had only the word for "mother", and that "in post-biblical Hebrew the generic term horeh
  for 'parent' developed".
- **"First parents" in English before 1830:**
  - Milton, *Paradise Lost* 3.65: "Our two first Parents"
    (https://milton.host.dartmouth.edu/reading_room/pl/book_3/text.shtml).
  - Westminster Shorter Catechism (1647), Q13 and Q15: "our first parents"
    (https://ccel.org/creeds/westminster-shorter-cat.html).

## What a test could measure

The question is what English each translator wrote where the Hebrew has a parent pair. The
fixed list of Hebrew places would be:

- (a) the 48 verses where father and mother are named together;
- (b) the 9 verses where they stand in parallel lines;
- (c) the 12 *yalad* participles, 1 *molid* and 1 relative-clause form used of parents;
- (d) the 2 *harah* participles and Gen 49:26.

Each translator gets a score at those places: "father and mother", "parents", a participle phrase
("that begat him"), or something else. Before 1830 the translator should be working directly from
Hebrew; Thomson, who translated the Greek, serves as the contrast.

What we already see in held text, by grep, before any proper alignment:

| Translator | Zech 13:3 *yoledav* | Gen 49:26 *horay* | "parents" in the biblical text |
| --- | --- | --- | --- |
| King James 1611 | "his father and his mother that begat him" | "my progenitors" | 0 in the OT |
| Newcome 1785 | "his father and his mother … Even those who begat him" | not in this volume | 0 hits in the volume |
| Blayney 1797 | "his father and his mother, who begat him" | not in this volume | 0 hits in the volume |
| Geddes 1792 | not in these volumes | "the blessings of thy father and of thy mother" (like the Septuagint) | 5 hits in vol. 1: 4 in notes and running heads, and the Exod 20:6 rendering "the posterity of those parents, who love God" (OCR, needs a page check) |
| Thomson 1808 (from Greek) | "father and mother" as in the Greek (not aligned) | as in the Greek | 2 (Esth 2:7, Prov 29:15, where the Greek has γονεῖς) |
| Young 1862 | "his father and his mother, his parents" | "my progenitors" | 2 (Zech 13:3; Exod 18:2, where "besides her parents" renders שִׁלּוּחֶיהָ, "her sending away", not a parent word) |
| Jasher 1840 | n/a | n/a | 2 by our count. One located: "return to thy parents and to thy birth place". The Hebrew under it is **unverified** |

Levi's prayer books use "parents" outside scripture: "by vilifying our parents and teachers" in
the Yom Kippur confession of 1795, rendering a liturgical Hebrew phrase that is **unverified**
here. Townley's Maimonides (1827) has 17 hits. Both suggest that translators of post-biblical
Hebrew wrote "parents" freely, while translators of the Bible did not.

The confession phrase, Mahzor 1795 (`bim_eighteenth-century_mahzor-le-yom-kipur-ke-m_1795`), is
the place to start. It is very likely על חטא … בזלזול הורים ומורים, "for the sin of disrespecting
parents and teachers". That would be a rabbinic *horim* rendered "parents" by a translator in the
1790s. Confirming it needs the Hebrew page from the same scan.

The test would put the Book of Mormon's 20 "parents" against that background. Translators of the
Hebrew Bible writing in the 1780s-1860s almost never chose "parents"; translators of rabbinic or
liturgical Hebrew did, because the Hebrew there has *horim*. What the test cannot tell is which
Hebrew or Egyptian, if any, lay behind a given English verse. It measures translators' habits, not
the source of the text.
