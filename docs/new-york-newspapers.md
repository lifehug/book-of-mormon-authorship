# The New York newspapers Chronicling America does not have (BOM-41)

Chronicling America holds **47 New York pages** for the whole of 1800-1830. The papers that
matter most to this project are not among them: not the Palmyra paper that printed the Book of
Mormon's title page, and not the two papers a candidate author edited. They are digitized, just
somewhere else.

This closes two gaps at once — the access evidence for BOM-33, and the missing pre-1830 writing
sample for W. W. Phelps in BOM-13.

## The three titles

| Title | LCCN | Place, years | Why it matters | Digitized? |
| --- | --- | --- | --- | --- |
| **Wayne Sentinel** | `sn84024337` | Palmyra, 1823-1859 | The Smiths' local paper. Reported the "Golden Bible" rumour and printed the Book of Mormon title page on 26 June 1829, nine months before publication; carried the 26 March 1830 sale advertisement | **Confirmed** on NYS Historic Newspapers, about 1,400 issues |
| **Ontario Phoenix** | `sn84031006` | Canandaigua, 1828-1832 | Anti-Masonic weekly. Publisher line: **W. W. Phelps & R. M. Bloomer (1828-1829), W. W. Phelps (1829-1830)** — a candidate author's own prose, written eleven miles from the Smiths, in the years the Book of Mormon was being dictated | Catalogued by the Library of Congress with no pages in Chronicling America. Status on NYSHN **unverified** |
| **Lake Light** | `sn84031024` | Trumansburg, 1827-1829 | Phelps's earlier paper, publishers Phelps & Bloomer 1827-1828 | Listed in the Ulysses Philomathic Library's Community History Archives. Status **unverified** |

## Why this is the biggest single gap in the candidate corpus

`docs/candidates.md` records that four of eight candidates have no pre-1830 writing sample at
all, and names the *Ontario Phoenix* as the most valuable missing item. Phelps is the one
candidate whose pre-1830 prose plausibly survives in quantity: a weekly paper he edited for
roughly two years is on the order of tens of thousands of words, written in the right place at
the right time.

Without it his pre-1830 result carries the pre-registration's "unreliable sample" flag and the
only usable comparison is post-1830 text, by which point he had read the Book of Mormon — the
exposure problem the inventory already flags. With it, he becomes one of the better-evidenced
candidates rather than one of the worst.

The same is true in a smaller way for the access evidence. "What could Joseph Smith have read
near Palmyra before 1829" is partly answered by what the *Wayne Sentinel* printed and
advertised, and that paper is currently absent from our corpus entirely.

## Getting them

NYS Historic Newspapers runs the same Open ONI software as Chronicling America, so the URL
shape is familiar and a fetcher would be a small variation on `ingest.chronicling_america`:

```
https://nyshistoricnewspapers.org/lccn/sn84024337/1829-05-15/ed-1/seq-2/
```

**But scripted access is blocked.** `nyshistoricnewspapers.org` sits behind Cloudflare and
answers automated requests with a challenge page (403 to curl, 403 to WebFetch). This is the
same situation as the Library of Congress bulk batches in BOM-10: a browser passes, a script
does not. The volumes here are small — hundreds of issues, not 76 GB — so hand-downloading is
less painful than it was for the batches, and `docs/chronam-bulk-download.md` is the pattern to
follow.

Before any of that, two things need checking in a browser, and neither takes long:

1. Does NYSHN actually hold the **Ontario Phoenix** for 1828-1830? The title is catalogued by
   the Library of Congress but has no pages in Chronicling America, and no search result
   confirmed NYSHN coverage either. If it is not there, the next stop is the New York State
   Library's microfilm holdings, which are listed but not digitized, and that collides with the
   digitized-sources-only decision in `docs/budget.md`.
2. Does the Ulysses Philomathic Library's archive hold the **Lake Light** for 1827-1828, and is
   its text downloadable?

The Wayne Sentinel needs no such check — it is confirmed, and its 1823-1830 issues can be
pulled whenever the route is built.

## Links to check

Browser only — both sites answer scripted requests with a Cloudflare challenge.

**Ontario Phoenix** (`sn84031006`), the one that matters most:
- https://nyshistoricnewspapers.org/lccn/sn84031006/
- https://nyshistoricnewspapers.org/newspapers/ (title search, if the LCCN 404s)
- https://chroniclingamerica.loc.gov/lccn/sn84031006/ (LoC record, confirms Phelps as publisher)

Looking for: issues listed for 1828, 1829, 1830.

**Lake Light** (`sn84031024`):
- https://www.loc.gov/item/sn84031024/
- https://nyshistoricnewspapers.org/lccn/sn84031024/
- https://communityhistoryarchives.com/places/ulysses-philomathic-library-2/

Looking for: coverage of 1827-1828, and whether text is downloadable or image-only.

**Wayne Sentinel** (`sn84024337`), confirmed, no check needed:
- https://nyshistoricnewspapers.org/lccn/sn84024337/
- https://nyshistoricnewspapers.org/lccn/sn84024337/1829-06-26/ed-1/seq-1/ — the issue carrying the Book of Mormon title page

## What it does not fix

Even complete, this is availability evidence, not readership evidence. That a paper printed
something near Palmyra does not establish that anyone in the Smith household read it. The
ceiling stays where `docs/backlog.md` puts it for BOM-33: *demonstrably available in the area*,
never *he read it*.

For Phelps the claim is stronger, because the prose would be his own rather than something he
might have seen. The caveat there is different: a newspaper editor writes to a house style and
much of a weekly is reprinted matter, so attributing specific columns to Phelps rather than to
his partner Bloomer or to a wire source will need care. Unsigned editorial matter from a paper
with two named publishers is not automatically one man's writing.
