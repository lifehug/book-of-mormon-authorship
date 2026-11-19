"""Fetch the outside sources the lab's new tests need (BOM-99, BOM-102 to BOM-108).

What each source is, where it comes from and its terms are in ``SOURCES`` below and in
``docs/research/2026-11-18-sources-for-new-tests.md``. Open material goes to
``data/corpus/lab/sources/<group>/`` (local disk, backed up, not in git); copyrighted material
(Joseph Smith Papers transcripts, papers, editors' transcriptions) to
``data/private/lab/sources/<group>/`` (the private repository). ``data/lab/sources.json`` records
every source with its address, terms, size, SHA-256 and state: names and numbers, no text.

Every fetch resumes: a file already on disk is skipped, a download is written to ``.part`` and
renamed when complete, and a failure is recorded as ``failed`` with its reason and tried again on
the next run, never stored as content. One stream, about a second between requests to a host;
josephsmithpapers.org as the owner decided on 2026-10-25 (``docs/candidates.md``), which he
confirmed for this material on 2026-11-18.

Usage::

    python -m lab.sources list              # every source: group, test, terms, state
    python -m lab.sources fetch [NAME ...]   # fetch all, or the named sources or groups
    python -m lab.sources marc               # catalog records that mark translations (HathiTrust)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ingest import jsp
from lab.paths import FAST, NOTES, REGISTRY, out

OPEN = FAST / "sources"
PRIVATE = NOTES / "sources"
RECORD = REGISTRY / "sources.json"
UA = jsp.USER_AGENT
PAUSE = 1.0
IA = "https://archive.org"
ACL = "https://aclanthology.org/"
GH = "https://github.com/"
JSPB = "https://www.josephsmithpapers.org/paper-summary/"
BMC = "https://archive.bookofmormoncentral.org/sites/default/files/"
PD = "public domain"

# (name, group, tests, kind, address, terms). Kinds: file, git, ia (Internet Archive full text),
# jsp (Joseph Smith Papers document), figshare, links (every archive linked from a page), wiki.
_IA = {
    "prophets": {
        "BOM-99 BOM-105": [
            "strangeeffectsof00sout",
            "trueexplanationo00soutiala",
            "mrssouthcottswor01soutiala",
            "lifeandworksaco00soutgoog",
            "privatecommunica01wroe",
            "abridgmentofjohn00wroe",
            "abridgementofjoh01wroe",
            "ARevealedKnowledgeOfThePropheciesAndTimes",
            "journaloflifetra00scotiala",
            "journalofliferel00hick",
            "lettersofeliashi00hick",
            "testimoniesoflif00bish",
            "VoreeHerald1846",
            "GospelHerald18471850",
            "ZionsReveille18461847",
            "ancientmodernmic00stra",
            "lettersofwilliam00blak",
            "codeofhandsomela01hand",
        ],
    },
    "bible_style": {
        "BOM-102 BOM-106 BOM-107": [
            "bim_eighteenth-century_the-chronicle-of-the-kin_dodsley-robert_1741",
            "bib_fict_4103140",
            "firstbookofameri00unse",
            "americanrevoluti00snow",
            "firstbooknapole00gruagoog",
            "chroniclesoferib02ocon",
            "bookofnullificat00char",
        ],
    },
    "debates": {"BOM-103": ["millennialharbinger1831", "delusionsanalysi00camp"]},
    "names": {"BOM-108": ["americangazettee00mors"]},
    "speech": {"BOM-106": ["eighteensermonsp00whit"]},
    "rigdon": {"BOM-104": ["orationdelivered01rigd"]},
}
_JSP = {
    "ot_revision_1": "old-testament-revision-1",
    "ot_revision_2": "old-testament-revision-2",
    "visions_of_moses_1830": "visions-of-moses-june-1830-moses-1",
    "abraham_ms_a": "book-of-abraham-manuscript-circa-july-circa-november-1835-a-abraham-14-26",
    "abraham_ms_b": "book-of-abraham-manuscript-circa-july-circa-november-1835-b-abraham-14-22",
    "abraham_ms_c": "book-of-abraham-manuscript-circa-july-circa-november-1835-c-abraham-11-218",
    "abraham_1842": "book-of-abraham-and-facsimiles-1-march-16-may-1842",
    "rigdon_oration_1838": "appendix-3-discourse-circa-4-july-1838",
    "rigdon_appeal_1840": "sidney-rigdon-appeal-to-the-american-people-1840",
}
_PAPERS = {
    "BOM-102": {
        "koppel_ordan_2011.pdf": ACL + "P11-1132.pdf",
        "rabinovich_wintner_2015.pdf": ACL + "Q15-1030.pdf",
        "rabinovich_ordan_wintner_2017.pdf": ACL + "P17-1049.pdf",
        "pylypenko_2021.pdf": ACL + "2021.emnlp-main.676.pdf",
        "amponsah_kaakyire_2022.pdf": "https://arxiv.org/pdf/2210.13391",
        "tvedtnes_1991.pdf": BMC + "archive-files/pdf/tvedtnes/2017-08-02/"
        "08_john_a._tvedtnes_the_hebrew_background_of_the_book_of_mormon_1991.pdf",
        "tvedtnes_1970.pdf": BMC
        + "John%20A.%20Tvedtnes%2C%20Hebraisms%20in%20the%20Book%20of%20Mormon%2C%201970.pdf",
        "echoes_and_evidences_2002.pdf": BMC
        + "archive-files/pdf/parry/2019-09-18/echoes_and_evidences_of_the_book_of_mormon.pdf",
    },
    "BOM-103": {
        "hamilton_2016.pdf": ACL + "P16-1141.pdf",
        "niculae_2014.pdf": ACL + "E14-4004.pdf",
        "popescu_strapparava_2015.pdf": ACL + "S15-2147.pdf",
    },
    "BOM-105": {
        "holmes_1992.pdf": "https://www.physics.smu.edu/pseudo/ScienceReligion/"
        "MormonStylometric.pdf",
        "kestemont_2015_preprint.pdf": "https://core.ac.uk/download/55887776.pdf",
    },
    "BOM-107": {
        "dubremetz_nivre_2015.pdf": ACL + "W15-0703.pdf",
        "dubremetz_nivre_2017.pdf": ACL + "W17-0205.pdf",
        "schneider_2021.pdf": ACL + "2021.latechclfl-1.11.pdf",
        "figures_survey_2024.pdf": "https://arxiv.org/pdf/2406.16674",
    },
}
_RIGDON = {
    "index.htm": "http://sidneyrigdon.com/RigWrit1.htm",
    "millennium_1833_35.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3.htm",
    "gospel_1833_35.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3b.htm",
    "misc_1834_38.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3d.htm",
}
_GIT = {
    "wordtree_books": (
        "bible_style",
        "BOM-102 BOM-106 BOM-107",
        "wordtreefoundation/books",
        "no licence stated; transcriptions of public-domain books",
    ),
    "bible_data": ("names", "BOM-108", "BradyStephenson/bible-data", "CC BY 4.0"),
    "bible_geocoding": ("names", "BOM-108", "openbibleinfo/Bible-Geocoding-Data", "CC BY 4.0"),
    "theographic": ("names", "BOM-108", "robertrouse/theographic-bible-metadata", "CC BY-SA 4.0"),
    "chiasmus_detector_dubremetz": (
        "chiasmus",
        "BOM-107",
        "mardub1635/chiasmusDetector",
        "GPL-3.0 (code)",
    ),
    "chiasmus_detector_schneider": (
        "chiasmus",
        "BOM-107",
        "cvjena/chiasmus-detector",
        "no licence stated (code)",
    ),
}
# Evans TCP texts whose titles say they were taken in short-hand (hand-keyed, free).
_TCP = ["N25065", "N09159", "N27848", "N27958", "N28782", "N08994", "N15885", "N24754"]


def _sources() -> list[dict]:
    rows = []

    def add(name, group, tests, kind, url, terms, private=False):
        rows.append(
            {
                "name": name,
                "group": group,
                "tests": tests,
                "kind": kind,
                "url": url,
                "terms": terms,
                "private": private,
            }
        )

    for group, by_test in _IA.items():
        for tests, items in by_test.items():
            for item in items:
                add(item, group, tests, "ia", f"{IA}/details/{item}", PD + " (scan and OCR text)")
    for name, slug in _JSP.items():
        group = "rigdon" if name.startswith("rigdon") else "dictated"
        add(
            name,
            group,
            "BOM-104",
            "jsp",
            JSPB + slug + "/1",
            "copyright Intellectual Reserve; private, not redistributed",
            True,
        )
    for tests, papers in _PAPERS.items():
        for name, url in papers.items():
            add(name, "papers", tests, "file", url, "copyright the authors; private copy", True)
    for name, url in _RIGDON.items():
        add(
            name,
            "rigdon",
            "BOM-104",
            "file",
            url,
            "public-domain texts in an editor's transcription with his notes; private",
            True,
        )
    for name, (group, tests, repo, terms) in _GIT.items():
        add(name, group, tests, "git", GH + repo, terms)
    for tcp in _TCP:
        add(
            tcp + ".xml",
            "speech",
            "BOM-106",
            "file",
            f"https://raw.githubusercontent.com/textcreationpartnership/{tcp}/master/{tcp}.xml",
            "Text Creation Partnership, free",
        )
    add(
        "oldbailey_online_xml",
        "speech",
        "BOM-106",
        "figshare",
        "https://api.figshare.com/v2/articles/4775434",
        "CC BY-NC 4.0",
    )
    add(
        "oldbailey_corpus_2",
        "speech",
        "BOM-106",
        "links",
        "https://fedora.clarin-d.uni-saarland.de/oldbailey/downloads.html",
        "CC BY-NC-SA 4.0",
    )
    add(
        "turner_confessions_1831.html",
        "prophets",
        "BOM-99 BOM-105",
        "file",
        "https://docsouth.unc.edu/neh/turner/turner.html",
        PD + " text; DocSouth edition",
    )
    add(
        "pnao.zip",
        "names",
        "BOM-108",
        "file",
        "https://oracc.museum.upenn.edu/json/pnao.zip",
        "CC BY-SA 3.0",
    )
    add(
        "onomasticon_names.json",
        "names",
        "BOM-108",
        "wiki",
        "https://onoma.lib.byu.edu/api.php",
        "no licence stated; a list of names only",
    )
    return rows


def _dest(s: dict) -> Path:
    return (PRIVATE if s["private"] else OPEN) / s["group"] / s["name"]


def _get(url: str, agent: str = UA, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _download(url: str, dest: Path, agent: str = UA) -> None:
    """Stream ``url`` to ``dest`` through a ``.part`` file; an empty reply is an error."""
    part = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, out(part).open("wb") as fh:
            while chunk := r.read(1 << 20):
                fh.write(chunk)
    except urllib.error.URLError as exc:
        # Python's certificate bundle lacks some hosts' issuers; curl checks against the
        # system's. Verification stays on either way.
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        cmd = ["curl", "--fail", "-sSL", "-A", agent, "-o", str(out(part)), url]
        subprocess.run(cmd, check=True)
    if part.stat().st_size == 0:
        part.unlink()
        raise OSError("empty reply")
    part.rename(dest)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _ia(s: dict, dest: Path) -> None:
    """The item's OCR full text, and its metadata record (title, year, creator)."""
    out(dest / "x")
    meta = json.loads(_get(f"{IA}/metadata/{s['name']}"))
    names = [f["name"] for f in meta.get("files", [])]
    text = next((n for n in names if n.endswith("_djvu.txt")), None)
    if text is None:
        raise OSError("no OCR text file in the item")
    _download(f"{IA}/download/{s['name']}/{urllib.parse.quote(text)}", dest / "text.txt")
    out(dest / "metadata.json").write_text(json.dumps(meta.get("metadata", {}), indent=1))


def _jsp(s: dict, dest: Path) -> None:
    """Every page of a Joseph Smith Papers document: raw page JSON, then one record a page."""
    slug = s["url"].removeprefix(JSPB).removesuffix("/1")
    raw = dest / "raw"
    out(raw / "x")

    def page(n: int) -> dict:
        path = raw / f"{n:04d}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        props = jsp.page_props(
            jsp.fetch(f"{JSPB}{slug}/{n}", user_agent=jsp.JSP_USER_AGENT, backoff=jsp.JSP_BACKOFF)
        )
        out(path).write_text(json.dumps(props), encoding="utf-8")
        jsp.pause(jsp.JSP_DELAY)
        return props

    total = int(page(1)["summary"]["numberOfPages"])
    records = [jsp.extract(page(n), n) for n in range(1, total + 1)]
    lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    out(dest / "pages.jsonl").write_text(lines, encoding="utf-8")


def _git(s: dict, dest: Path) -> None:
    out(dest.parent / "x")
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", s["url"], str(dest)], check=True)


def _figshare(s: dict, dest: Path) -> None:
    for f in json.loads(_get(s["url"]))["files"]:
        if not (dest / f["name"]).exists():
            _download(f["download_url"], out(dest / f["name"]))


def _links(s: dict, dest: Path) -> None:
    """Every archive (.zip, .gz, .tgz, .xz) linked from the page."""
    page = _get(s["url"]).decode("utf-8", "replace")
    hrefs = re.findall(r'href="([^"]+\.(?:zip|gz|tgz|xz|bz2))"', page)
    if not hrefs:
        raise OSError("no archive links on the page")
    for href in dict.fromkeys(hrefs):
        name = href.rsplit("/", 1)[-1]
        if not (dest / name).exists():
            _download(urllib.parse.urljoin(s["url"], href), out(dest / name))
            time.sleep(PAUSE)


def _wiki(s: dict, dest: Path) -> None:
    """Page titles of a MediaWiki category (the Onomasticon's names), following continuation."""
    titles, cont = [], {}
    while True:
        q = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Names",
            "cmlimit": "500",
            "format": "json",
            **cont,
        }
        reply = json.loads(_get(s["url"] + "?" + urllib.parse.urlencode(q)))
        titles += [m["title"] for m in reply["query"]["categorymembers"]]
        cont = reply.get("continue", {})
        if not cont:
            break
        time.sleep(PAUSE)
    out(dest).write_text(json.dumps(sorted(set(titles)), ensure_ascii=False, indent=1))


KINDS = {
    "ia": _ia,
    "jsp": _jsp,
    "git": _git,
    "figshare": _figshare,
    "links": _links,
    "wiki": _wiki,
    "file": lambda s, dest: _download(s["url"], out(dest)),
}
# A folder kind is complete only when its last file exists; a half-fetched folder is resumed.
DONE = {"ia": "text.txt", "jsp": "pages.jsonl", "git": ".git"}


def _complete(s: dict, dest: Path) -> bool:
    if s["kind"] in DONE:
        return (dest / DONE[s["kind"]]).exists()
    if s["kind"] in ("figshare", "links"):
        return False  # the fetcher itself skips files already held
    return dest.is_file() and dest.stat().st_size > 0


def _load() -> dict:
    return json.loads(RECORD.read_text()) if RECORD.exists() else {}


def _save(record: dict) -> None:
    out(RECORD).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def fetch(names: list[str]) -> int:
    record, failed = _load(), 0
    for s in _sources():
        if names and s["name"] not in names and s["group"] not in names:
            continue
        dest, held = _dest(s), record.get(s["name"], {})
        if _complete(s, dest) and held.get("state") == "fetched":
            continue
        entry = {k: s[k] for k in ("group", "tests", "url", "terms")} | {"path": str(dest)}
        try:
            if not _complete(s, dest):
                KINDS[s["kind"]](s, dest)
                time.sleep(PAUSE)
            entry |= {"state": "fetched", "bytes": _size(dest), "date": time.strftime("%Y-%m-%d")}
            if dest.is_file():
                entry["sha256"] = _sha(dest)
            print(f"fetched {s['name']} ({entry['bytes']:,} bytes)", flush=True)
        except Exception as exc:  # noqa: BLE001  a failure is recorded and retried, never content
            failed += 1
            entry |= {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"[:200]}
            print(f"FAILED {s['name']}: {entry['reason']}", file=sys.stderr, flush=True)
        record[s["name"]] = entry
        _save(record)
    return failed


def marc(batch: int = 20) -> int:
    """For every HathiTrust record we hold: the catalog fields that mark a translation.

    MARC 041 (indicator 1 = is a translation; subfield h = language of the original; k =
    intermediate language), 240 subfield l, 765 and 546. One line a record; resumes from the file.
    """
    keys = sorted(
        {
            json.loads(line)["ht_bib_key"]
            for line in gzip.open("data/catalog/hathitrust.jsonl.gz", "rt")
        }
    )
    path = OPEN / "translation_labels" / "hathitrust_marc.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(line)["ht_bib_key"] for line in path.read_text().splitlines()}
    todo = [k for k in keys if k not in done]
    print(f"{len(keys):,} records, {len(done):,} held, {len(todo):,} to fetch", flush=True)
    field = re.compile(
        r'<datafield tag="(041|240|765|546)" ind1="(.)" ind2="(.)">(.*?)</datafield>', re.S
    )
    sub = re.compile(r'<subfield code="(.)">(.*?)</subfield>', re.S)
    with out(path).open("a", encoding="utf-8") as fh:
        for i in range(0, len(todo), batch):
            part = todo[i : i + batch]
            spec = "|".join(f"id:{n};recordnumber:{k}" for n, k in enumerate(part))
            url = "https://catalog.hathitrust.org/api/volumes/full/json/" + spec
            reply = json.loads(_get(url))
            for item in reply if isinstance(reply, list) else reply.values():
                for key, rec in item.get("records", {}).items():
                    fields = [
                        {"tag": t, "ind1": a, "subfields": sub.findall(body)}
                        for t, a, _b, body in field.findall(rec.get("marc-xml", ""))
                    ]
                    fh.write(json.dumps({"ht_bib_key": key, "fields": fields}) + "\n")
            fh.flush()
            if (i // batch) % 100 == 0:
                print(f"  {i + len(part):,}/{len(todo):,}", flush=True)
            time.sleep(PAUSE)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list")
    sp.add_parser("fetch").add_argument("names", nargs="*")
    sp.add_parser("marc")
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        return 1 if fetch(a.names) else 0
    if a.cmd == "marc":
        return marc()
    record = _load()
    for s in _sources():
        state = record.get(s["name"], {}).get("state", "not fetched")
        print(f"{s['group']:<12} {s['tests']:<24} {state:<12} {s['name']}  [{s['terms']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
