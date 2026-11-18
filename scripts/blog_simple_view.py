"""Add the simple view (?eli5) to the blog page: a plain-words box per section, the full text opening under it.

Usage: python scripts/blog_simple_view.py <page.html>   (paper/blog-phase1.html, and the copy on the site)
"""
# ruff: noqa: E501  (the page text below is kept one sentence or row per line)

import html
import re
import sys

Q, DID, FOUND, MEANS, CANT = (
    "The question",
    "What I did",
    "What I found",
    "What it means",
    "What it can't tell us",
)

BOXES = {
    "top": [
        (Q, "Who wrote the Book of Mormon, and did it borrow from other books?"),
        (
            DID,
            "I built a library of nearly 700,000 books, pamphlets and newspaper pages printed between 1780 and 1830. I trained language models only on that text, so they had never seen the Book of Mormon or anything written about it since. I checked the book against more than 220,000 earlier books for copied wording, shared ideas and shared storylines. I compared its style with the eight people most often proposed as its author, and with 23,872 writers of that era. Every method was first checked on books whose authors are known.",
        ),
        (
            FOUND,
            [
                "<b>Borrowing:</b> apart from the King James Bible, the book copies almost nothing. Only 0.16% of its text matches earlier books. The books most often named as sources, like <i>The Late War</i> and <i>View of the Hebrews</i>, don't stand out from other books of their kind. It doesn't follow any earlier book's outline either: the test that catches Josephus retelling Genesis in his own words finds no book whose story it follows.",
                "<b>Authorship:</b> the closest writing is Joseph Smith's revelations, the short texts he dictated in God's voice, among the eight candidates and across the whole library. His ordinary writing, his letters and journals, doesn't stand out the same way. And writers who died long before 1829 also rank near the top, so the tools are matching a style of religious writing, not just a person.",
            ],
        ),
        (
            CANT,
            "The tools are good at picking the closest match from a list, and bad at telling whether the real author is on the list at all, so nobody is ruled in or out. They also can't tell a person from the style they are writing in, which is why a believer and a skeptic can both read the result as fitting their view.",
        ),
    ],
    "library": [
        (
            Q,
            "How do you test the Book of Mormon without an AI that has already read it, and everything written about it since?",
        ),
        (
            DID,
            'I catalogued 695,021 books, pamphlets and newspaper pages printed between 1780 and 1830, and trained three language models from scratch on that text alone. I set aside 168 passages of the Book of Mormon that no model saw until the final test. I also masked King James Bible wording first, so the tests weren\'t just measuring the Bible. The phrase "it came to pass that" alone appears 1,290 times.',
        ),
        (
            FOUND,
            "As far as I can find, nothing on this question has come close to this size. Earlier studies compared the book with a few dozen to a couple of hundred writing samples.",
        ),
        (
            MEANS,
            "The results aren't shaped by two centuries of commentary, and they aren't dominated by Bible phrasing.",
        ),
        (
            CANT,
            "The library is what I could gather, not everything ever written. And most candidates left writing only from after the book was printed.",
        ),
    ],
    "borrowing": [
        (Q, "Did the Book of Mormon copy wording, ideas or storylines from earlier books?"),
        (
            DID,
            "I ran four tests against about 221,000 earlier books: copied wording, rare four-word phrases, passages with the same ideas (163 million passages compared), and the same events told in the same order. Each test was first run on books known to borrow. It caught <i>The Late War</i> copying War of 1812 documents, and Josephus retelling Genesis.",
        ),
        (
            FOUND,
            [
                "<b>Wording:</b> only 0.16% of the text matches earlier books.",
                "<b>Rare phrases:</b> <i>The Late War</i> and <i>The First Book of Napoleon</i> share enough to count. So do other books written in Bible style, and 2,044 books in the library meet the same criteria.",
                "<b><i>View of the Hebrews</i>:</b> not a hit on wording, ideas or storyline. 77 of 500 religious books are closer in ideas.",
                "<b>Storyline:</b> no book tells the same story.",
            ],
        ),
        (
            MEANS,
            "The book copies almost nothing. The books usually named as sources look like neighbours in the same genre, and this test can't tell a source from a neighbour.",
        ),
        (
            CANT,
            "Where a single, widely shared idea came from. The ideas it shares with <i>View of the Hebrews</i> are in hundreds of religious books of the time, so they point to no one source.",
        ),
    ],
    "earlier": [
        (Q, "Do the earlier computer studies, from 1980 to 2013, hold up?"),
        (
            DID,
            "I rebuilt five of them, each with its own method, and one on the data its authors published.",
        ),
        (
            FOUND,
            [
                "The 2008 study put Sidney Rigdon first or second for 169 chapters. With other genuine Rigdon writing it's 92, and Parley Pratt goes from 42 to 137.",
                'The 2011 study\'s "none of these" was wrong 80% of the time with 1,000-word samples and 0% with 10,000-word samples.',
                "The narrators can be told apart 74% of the time, against 28% by chance. Real authors are told apart 96% of the time.",
            ],
        ),
        (
            MEANS,
            "Two earlier headline results depend on which samples were used. The narrators sound different, but not as different as separate people.",
        ),
        (
            CANT,
            "Whether the narrators differ because of who is speaking or because of when each part was dictated. Sorting by early or late dictation works about as well.",
        ),
    ],
    "tools": [
        (Q, "How far can these tools be trusted?"),
        (
            DID,
            "I gave every method, mine and the older ones, the same exam on books whose authors are known. Two jobs: pick the closest author from a list, and say whether the real author is on the list at all.",
        ),
        (
            FOUND,
            [
                "<b>Picking from a list:</b> my models get 91&ndash;94% right on authors nobody had looked at. The older methods get 76&ndash;78%.",
                '<b>Saying "none of these":</b> every method fails. Set to confirm 95% of true authors, the best still lets in one stranger in three. The bar was one in twenty.',
            ],
        ),
        (
            MEANS,
            "These tools can tell you who on a list is closest. Every result after this section is that kind of answer.",
        ),
        (
            CANT,
            "Whether the real author is on the list at all. A test that must name someone will always name someone.",
        ),
    ],
    "joseph": [
        (
            Q,
            "Of the eight candidates, whose writing is closest to the Book of Mormon, and does it matter which of Joseph Smith's writing you use?",
        ),
        (
            DID,
            "I kept his revelations, short texts dictated in God's voice, apart from his letters and journals. Seven revelations survive from the same months as the book. I scored all 168 sealed passages against every candidate with eight methods, then made four attempts to knock the result down.",
        ),
        (
            FOUND,
            [
                "Six of eight methods rank his 1828&ndash;29 revelations first, including all three of my models.",
                "His letters and journals don't stand out the same way.",
                "At the largest model size, writers who were dead before 1827 do as well.",
                "Misheard-word slips are about nine times as common in the original manuscript as in the printer's copy. The book was dictated aloud.",
            ],
        ),
        (MEANS, "Among the candidates, his revelation voice is the nearest match."),
        (
            CANT,
            "Whether that's the same man or the same kind of text. The revelation sample is also small, a couple of pages.",
        ),
    ],
    "others": [
        (Q, "If the other candidates rank lower, are they ruled out?"),
        (
            DID,
            "I checked whether each candidate's model could recognise that same person in a different work of their own.",
        ),
        (
            FOUND,
            "Only Ethan Smith's model passed. Rigdon's and Phelps's models didn't recognise a single passage of their own author's other writing. Spalding and Hunt left one work each, so they can't be checked this way.",
        ),
        (
            MEANS,
            'Ethan Smith\'s low rank is real evidence that the book doesn\'t read like him. For Cowdery, Rigdon, Phelps and Pratt the right word is "not shown", not "ruled out".',
        ),
        (CANT, "Anything about Spalding or Hunt, or about the four whose models failed."),
    ],
    "next": [
        (
            Q,
            "Does anyone from that era write more like the Book of Mormon than the eight usual candidates?",
        ),
        (
            DID,
            "I compared the book with all 23,872 authors in the library who left at least 10,000 words. Writers already dead when the book was written stayed in the ranking as a check: if they rank near the top, the search is matching a style, not a person.",
        ),
        (
            FOUND,
            "Joseph Smith's revelations come out first in two of the three versions, and second in the third, behind John Wroe, an English prophet. After them come visionaries and Quaker ministers. In one version 9 of the top 20 were already dead, where chance says 5.",
        ),
        (
            MEANS,
            "The closest writing is a voice of revelation, not one person. A believer would say the book and the revelations came from the same source. A skeptic would say Joseph Smith wrote both. Both predict this result.",
        ),
        (
            CANT,
            "Whether the match comes from the man or the style. For a book unlike its author's other writing, this search puts the true author in the top 10 only about four times in ten.",
        ),
    ],
    "check": [
        (Q, "Can someone else check this work?"),
        (
            DID,
            "I made everything public: the code, the result tables, the plan and every change to it, and the models on Hugging Face.",
        ),
        (
            FOUND,
            "With the candidate models anyone can rerun the Book of Mormon result without training anything. Rebuilding every other model costs about $50 to $100 of rented computing.",
        ),
        (MEANS, "You don't have to trust me. Every number can be checked."),
        (
            CANT,
            "Four sources I'm not allowed to republish, though the repository gives the steps to get the same access. I did this as one person working with AI, and the reviews in the repository are simulated by an AI model and labelled that way.",
        ),
    ],
}

LEDE = (
    '<p class="eli5lede">I asked a computer two things. Did this book copy from other books? And whose writing '
    "does it sound like? It copied almost nothing. It sounds most like the revelations Joseph Smith dictated in "
    "the same months, and not like his everyday letters and journals. But the computer can't tell whether that's because one man wrote both, or because both are "
    "written in the same kind of religious voice. So this doesn't settle who wrote it, for a believer or for a "
    "skeptic.</p>\n"
)

CSS = """<style>
/* The simple view (?eli5): a short box per section; the full text opens under it. */
.viewsw,.eli5box,.eli5more{display:none}
.full>.src{margin:-8px 0 22px}
.js .viewsw{display:inline-block;float:right;font-family:var(--sans);font-size:.8125rem;line-height:1.3;border:1px solid var(--line);background:var(--surface);color:var(--text-2);padding:4px 12px;border-radius:999px;text-decoration:none;margin-left:12px}
.js .viewsw:hover{background:var(--lime);border-color:var(--lime);color:#000}
.eli5 .eli5box{display:block}
.eli5 .eli5more{display:inline-block}
.eli5 .full,.eli5 .draft{display:none}
.eli5 .full.open{display:block}
.eli5 h2{margin-top:2.75rem}
.eli5box{font-family:var(--sans);background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:.35rem 1.25rem;margin:1.25rem 0 .75rem}
.eli5box dl{margin:0}
.eli5box .r{display:grid;grid-template-columns:8.5rem 1fr;gap:16px;padding:.8rem 0;border-top:1px solid var(--line);line-height:1.5}
.eli5box .r:first-child{border-top:0}
.eli5box dt{font-size:.8125rem;font-weight:700;color:var(--text-3);padding-top:.2rem}
.eli5box dd{margin:0}
.eli5box ul{margin:0;padding-left:1.1rem}
.eli5box li{margin-bottom:.45rem}
.eli5box li:last-child{margin-bottom:0}
.eli5box .r.x{display:none}
.eli5box.open .r.x{display:grid}
.eli5head{padding:.7rem 0;border-bottom:2px solid var(--text);font-weight:800;letter-spacing:-.01em}
.eli5lede{font-size:1.1875rem;line-height:1.5;margin:1rem 0 .4rem;padding-bottom:1rem;border-bottom:1px solid var(--line)}
.eli5more{font-family:var(--sans);font-size:.8125rem;border:1px solid var(--line);background:var(--surface);color:var(--text);padding:6px 11px;border-radius:4px;cursor:pointer}
.eli5more{margin:0 0 .5rem}
.eli5more:hover{background:var(--lime);border-color:var(--lime);color:#000}
.eli5more:focus-visible,.viewsw:focus-visible{outline:2px solid var(--text);outline-offset:2px}
@media (max-width:560px){.eli5box .r{grid-template-columns:1fr;gap:2px}.eli5box{padding:.25rem 1rem}}
</style>
<script>
  document.documentElement.classList.add('js');
  if (/[?&]eli5(=|&|$)/.test(location.search)) document.documentElement.classList.add('eli5');
</script>
"""

JS = """<script>
/* The simple view: the switch beside the byline, the per-section openers. The address gains ?eli5 so the view can be shared. */
(function(){
  var root=document.documentElement, sw=document.getElementById('viewsw');
  if(!sw) return;
  function on(){return root.classList.contains('eli5')}
  function paint(){
    sw.textContent=on()?'Full article':'Simple version';
    sw.setAttribute('href',(on()?location.pathname:'?eli5')+location.hash);
  }
  function openSec(full,v){
    var btn=full.previousElementSibling, box=btn&&btn.previousElementSibling;
    full.classList.toggle('open',v);
    if(box&&box.classList.contains('eli5box')) box.classList.toggle('open',v);
    if(btn&&btn.classList.contains('eli5more')){btn.setAttribute('aria-expanded',v?'true':'false');btn.textContent=v?'Hide the full section':'Read the full section';}
  }
  function reveal(){
    if(!on()||location.hash.length<2) return;
    var t=document.getElementById(decodeURIComponent(location.hash.slice(1))), f=t&&t.closest('.full');
    if(f&&!f.classList.contains('open')){ if(f.previousElementSibling&&f.previousElementSibling.classList.contains('eli5more')) openSec(f,true); else f.classList.add('open'); t.scrollIntoView(); }
  }
  sw.addEventListener('click',function(e){
    if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey) return;
    e.preventDefault();
    var v=!on();
    root.classList.toggle('eli5',v);
    history.replaceState(null,'',location.pathname+(v?'?eli5':'')+location.hash);
    paint();
    if(window.gtag) gtag('event','simple_view',{state:v?'on':'off'});
  });
  document.querySelectorAll('.eli5more').forEach(function(b){
    b.addEventListener('click',function(){ openSec(b.nextElementSibling,b.getAttribute('aria-expanded')!=='true'); });
  });
  window.addEventListener('hashchange',reveal);
  paint(); reveal();
})();
</script>
"""


def box(key):
    rows = []
    for label, body in BOXES[key]:
        if isinstance(body, list):
            body = "<ul>" + "".join(f"<li>{b}</li>" for b in body) + "</ul>"
        cls = "r x" if (label == DID and key != "top") else "r"
        rows.append(
            f'<div class="{cls}"><dt>{html.escape(label, quote=False)}</dt><dd>{body}</dd></div>'
        )
    head = ""
    if key == "top":
        head = '<div class="eli5head">The short version</div>\n' + LEDE
    return f'<div class="eli5box">\n{head}<dl>\n' + "\n".join(rows) + "\n</dl>\n</div>\n"


def main(path):
    s = open(path, encoding="utf-8").read()
    if "eli5box" in s:
        sys.exit("already has the simple view")
    s = s.replace("</head>", CSS + "</head>", 1)
    s, n = re.subn(
        r'(<div class="byline">)',
        r'\1<a class="viewsw" id="viewsw" href="?eli5">Simple version</a>',
        s,
        count=1,
    )
    assert n == 1
    # the introduction: everything between the note under the byline and the contents list
    m = re.search(r'(<div class="draft">.*?</div>\n)', s)
    s = s[: m.end()] + box("top") + '<div class="full">\n' + s[m.end() :]
    assert s.count('<ul class="toc">') == 1
    s = s.replace('<ul class="toc">', '</div>\n\n<ul class="toc">', 1)
    # each section: its heading stays, its body is wrapped
    heads = list(re.finditer(r'<h2 id="([a-z]+)">.*?</h2>\n', s))
    assert [h.group(1) for h in heads] == [k for k in BOXES if k != "top"], [
        h.group(1) for h in heads
    ]
    end = s.index("\n<hr>")
    out, pos = [], 0
    for i, h in enumerate(heads):
        out.append(s[pos : h.start()])
        if i:
            out.append("</div>\n\n")
        out.append(h.group(0))
        out.append(box(h.group(1)))
        out.append(
            '<button type="button" class="eli5more" aria-expanded="false">Read the full section</button>\n<div class="full">\n'
        )
        pos = h.end()
    out.append(s[pos:end] + "\n</div>\n" + s[end:])
    s = "".join(out)
    s = s.replace("</body>", JS + "</body>", 1)
    open(path, "w", encoding="utf-8").write(s)
    print("simple view added:", len(heads), "sections")


main(sys.argv[1])
