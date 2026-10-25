"""The hand-validation sample and its review view (BOM-12).

Amendment 3 registers this as the accuracy claim, and it is the only one the project has.
Everything else measured so far is *reliability* -- two models agreeing with each other, which
says nothing about whether either is right. The amendment fixes the design:

* 300 records, ``validation_sample``
* stratified, ``validation_sampling``, over-sampling the ambiguous categories **and the records
  where the two passes disagree**
* including records decided by rule as well as by model, because the published rate must cover
  the easy half too
* the rate reported separately for the rule-decided and model-decided halves

Deliberate over-sampling means the raw accuracy over these 300 is **not** a corpus estimate.
Each stratum carries its population size so a weighted figure can be computed, and the per
stratum rates are what get published.

The view writes a single self-contained page. Judgements live in the browser and are exported
as JSON, so the file can be closed and reopened across several sittings without losing work.

Usage::

    python -m metadata.validation build          # draw the sample, write the page
    python -m metadata.validation score FILE     # score an exported judgement file
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.genre import LABELS, excerpt_for
from metadata.genre_pass2 import compare

CATALOG = Path("data/catalog/catalog.parquet")
GENRE = Path("data/catalog/genre.parquet")
PASS2 = Path("data/catalog/genre_pass2.parquet")
# The sample INDEX is public: work ids, strata, and both model labels, which is everything a
# replicator needs to redraw the identical sample. The excerpts are NOT. Thirty of the 300
# records are Harvard Institutional Books, whose terms are noncommercial and no redistribution,
# and Internet Archive item rights vary and are not re-checked here. The page that carries the
# text is built locally and gitignored; `build` regenerates it from a corpus copy in seconds.
INDEX = Path("data/catalog/validation_index.json")
SAMPLE = Path("data/catalog/validation_sample.json")
PAGE = Path("data/catalog/validation.html")
PUBLIC_FIELDS = (
    "work_id",
    "stratum",
    "population",
    "source",
    "year",
    "pass1",
    "pass2",
    "decided_by",
)

# Stratum -> share of the 300. Fixed here before the sample is drawn.
PLAN = {
    "contradiction": 90,  # the two passes share no label: one of them is wrong
    "primary_differs": 60,  # sets overlap, primaries differ
    "ambiguous_agree": 45,  # two-label or uncertain, and the passes agree
    "rule_decided": 60,  # Amendment 3 requires the easy half be covered
    "ordinary_agree": 45,  # plain model-decided agreement, the baseline
}


def build() -> int:
    cfg = load_config()
    rng = random.Random(cfg["seed"])
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    g1 = {r["work_id"]: r for r in pq.read_table(GENRE).to_pylist()}
    p2 = {r["work_id"]: r for r in pq.read_table(PASS2).to_pylist() if r["pass2"]}

    pools: dict[str, list[str]] = {k: [] for k in PLAN}
    for wid, r in p2.items():
        verdict = compare(r["pass1"], r["pass2"])
        if verdict == "contradict":
            pools["contradiction"].append(wid)
        elif verdict in ("overlap", "primary"):
            pools["primary_differs"].append(wid)
        elif r["oversampled"]:
            pools["ambiguous_agree"].append(wid)
        else:
            pools["ordinary_agree"].append(wid)
    pools["rule_decided"] = [
        w for w, r in g1.items() if r["decided_by"] == "rule" and cat.get(w, {}).get("has_text")
    ]

    picked: list[dict] = []
    for stratum, want in PLAN.items():
        pool = pools[stratum]
        take = min(want, len(pool))
        if take < want:
            print(f"  {stratum}: only {len(pool):,} available, wanted {want}", file=sys.stderr)
        for wid in rng.sample(pool, take):
            row = cat[wid]
            picked.append(
                {
                    "work_id": wid,
                    "stratum": stratum,
                    "population": len(pool),
                    "source": row["source"],
                    "title": (row["title"] or "")[:300],
                    "author": (row["author"] or "")[:120],
                    "year": row["year"],
                    "pass1": g1[wid]["genre"],
                    "pass2": p2[wid]["pass2"] if wid in p2 else None,
                    "decided_by": g1[wid]["decided_by"],
                    "excerpt": excerpt_for(row, 700),
                }
            )
    rng.shuffle(picked)  # so a sitting is not all one stratum
    SAMPLE.write_text(json.dumps(picked, ensure_ascii=False, indent=1), encoding="utf-8")
    INDEX.write_text(
        json.dumps([{k: r[k] for k in PUBLIC_FIELDS} for r in picked], indent=1),
        encoding="utf-8",
    )
    PAGE.write_text(render(picked), encoding="utf-8")
    print(f"{len(picked)} records -> {SAMPLE}")
    for k in PLAN:
        n = sum(1 for r in picked if r["stratum"] == k)
        print(f"  {k:<18}{n:>4}  of {pools[k] and len(pools[k]) or 0:>8,} in the corpus")
    print(f"page -> {PAGE}  (local only)")
    print(f"index -> {INDEX}  (committed; no text)")
    return 0


def render(rows: list[dict]) -> str:
    data = json.dumps(rows, ensure_ascii=False)
    labels = json.dumps(list(LABELS) + ["uncertain"])
    return (
        _TEMPLATE.replace("__DATA__", data)
        .replace("__LABELS__", labels)
        .replace("__N__", str(len(rows)))
    )


def score(path: Path) -> int:
    """Score an exported judgement file: accuracy per pass, per stratum, weighted."""
    judged = {j["work_id"]: j for j in json.loads(path.read_text(encoding="utf-8"))}
    rows = json.loads(SAMPLE.read_text(encoding="utf-8"))
    done = [r for r in rows if r["work_id"] in judged]
    print(f"{len(done)} of {len(rows)} records judged\n")
    if not done:
        return 1

    def rate(sub: list[dict], key: str) -> str:
        n = sum(1 for r in sub if judged[r["work_id"]]["truth"])
        if not n:
            return "   -  "
        ok = sum(
            1
            for r in sub
            if judged[r["work_id"]]["truth"]
            and set(judged[r["work_id"]]["truth"]) == {x.strip() for x in (r[key] or "").split(",")}
        )
        return f"{ok / n:6.1%}"

    print(f"{'stratum':<20}{'n':>5}{'pass1':>9}{'pass2':>9}{'population':>13}")
    for st in PLAN:
        sub = [r for r in done if r["stratum"] == st]
        if sub:
            pop = sub[0]["population"]
            print(f"{st:<20}{len(sub):>5}{rate(sub, 'pass1'):>9}{rate(sub, 'pass2'):>9}{pop:>13,}")
    print()
    for name, sub in (
        ("rule-decided", [r for r in done if r["decided_by"] == "rule"]),
        ("model-decided", [r for r in done if r["decided_by"] != "rule"]),
    ):
        if sub:
            print(f"{name:<20}{len(sub):>5}{rate(sub, 'pass1'):>9}{rate(sub, 'pass2'):>9}")
    print("\nStratum rates are the published figures: the sample deliberately over-samples")
    print("disagreement, so the raw total over these records is not a corpus estimate.")
    return 0


_TEMPLATE = r"""<title>Genre validation — 300 records</title>
<style>
:root{
  --ink:#16171a; --ink-2:#4a4d55; --ink-3:#7c818c;
  --paper:#faf9f7; --card:#ffffff; --rule:#e2e0db;
  --accent:#1f4e79; --accent-soft:#e8eef4;
  --yes:#2d6a4f; --no:#9b2226; --maybe:#9a6700;
}
:root:not([data-theme="light"]){ @media (prefers-color-scheme: dark){
  --ink:#e9e8e4; --ink-2:#a9aeb8; --ink-3:#787d87;
  --paper:#15161a; --card:#1d1f24; --rule:#2e3138;
  --accent:#7fb3e0; --accent-soft:#1c2a38;
  --yes:#7fc8a0; --no:#e88b8e; --maybe:#d8b25c;
}}
:root[data-theme="dark"]{
  --ink:#e9e8e4; --ink-2:#a9aeb8; --ink-3:#787d87;
  --paper:#15161a; --card:#1d1f24; --rule:#2e3138;
  --accent:#7fb3e0; --accent-soft:#1c2a38;
  --yes:#7fc8a0; --no:#e88b8e; --maybe:#d8b25c;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--paper);
  border-bottom:1px solid var(--rule);padding:10px 20px;
  display:flex;gap:18px;align-items:center;flex-wrap:wrap}
h1{font-size:14px;margin:0;font-weight:650;letter-spacing:.02em}
.bar{flex:1;min-width:140px;height:5px;background:var(--rule);border-radius:3px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent);width:0;transition:width .2s}
.count{font-variant-numeric:tabular-nums;color:var(--ink-2);font-size:13px}
main{max-width:860px;margin:0 auto;padding:22px 20px 120px}
.card{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:20px 22px}
.meta{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;color:var(--ink-3);margin-bottom:10px}
.chip{background:var(--accent-soft);color:var(--accent);padding:2px 8px;border-radius:20px;
  font-weight:600;letter-spacing:.02em}
.title{font:600 19px/1.35 ui-serif,Georgia,"Times New Roman",serif;margin:0 0 4px}
.byline{color:var(--ink-2);font-size:13px;margin-bottom:14px}
.excerpt{font:14px/1.6 ui-serif,Georgia,serif;color:var(--ink-2);background:var(--paper);
  border-left:3px solid var(--rule);padding:11px 14px;max-height:190px;overflow:auto;
  border-radius:0 6px 6px 0;white-space:pre-wrap;word-break:break-word}
.props{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin:16px 0}
.prop{border:1px solid var(--rule);border-radius:8px;padding:10px 12px}
.prop b{display:block;font-size:11px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:3px}
.prop span{font:600 14px ui-monospace,SFMono-Regular,Menlo,monospace}
.q{font-size:13px;color:var(--ink-2);margin:18px 0 8px}
.opts{display:flex;flex-direction:column;gap:7px}
button{font:inherit;cursor:pointer;text-align:left;border:1px solid var(--rule);
  background:var(--card);color:var(--ink);padding:10px 13px;border-radius:8px;
  display:flex;gap:11px;align-items:center}
button:hover{border-color:var(--accent)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
kbd{font:600 11px ui-monospace,Menlo,monospace;background:var(--paper);color:var(--ink-3);
  border:1px solid var(--rule);border-radius:4px;padding:2px 6px;min-width:20px;text-align:center}
.picker{display:none;flex-wrap:wrap;gap:6px;margin-top:10px}
.picker.on{display:flex}
.picker button{padding:6px 11px;font-size:13px}
.picker button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
footer{position:fixed;bottom:0;left:0;right:0;background:var(--card);
  border-top:1px solid var(--rule);padding:10px 20px;display:flex;gap:10px;
  align-items:center;justify-content:center;flex-wrap:wrap}
footer button{padding:7px 14px}
.note{color:var(--ink-3);font-size:12px;max-width:860px;margin:16px auto 0;padding:0 20px}
.done{text-align:center;padding:60px 20px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<header>
  <h1>Genre validation</h1>
  <div class="bar"><i id="pbar"></i></div>
  <div class="count" id="count"></div>
  <button id="theme" style="padding:5px 10px;font-size:12px">◐</button>
</header>

<main id="main"></main>

<footer>
  <button id="back">← Back</button>
  <button id="skip">Skip</button>
  <button id="save"><b>Export judgements</b></button>
  <span class="count" id="saved"></span>
</footer>

<p class="note">Judgements are kept in this browser and survive a reload. Export when you stop;
the file goes to <code>python -m metadata.validation score FILE</code>. Pick what the work
<em>actually is</em> — the two model answers are shown only so you can see where they differ,
and either or both may be wrong.</p>

<script>
const DATA = __DATA__, LABELS = __LABELS__, N = __N__;
const KEY = "bom-genre-validation";
let judged = JSON.parse(localStorage.getItem(KEY) || "{}");
let i = DATA.findIndex(r => !judged[r.work_id]); if (i < 0) i = 0;
let chosen = [];

const ENT = {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"};
const esc = s => (s ?? "").replace(/[&<>"]/g, c => ENT[c]);
const setOf = s => new Set((s || "").split(",").map(x => x.trim()).filter(Boolean));

function save(truth){
  judged[DATA[i].work_id] = {work_id: DATA[i].work_id, truth, at: new Date().toISOString()};
  localStorage.setItem(KEY, JSON.stringify(judged));
  i = Math.min(i + 1, DATA.length); chosen = []; draw();
}

function draw(){
  const n = Object.keys(judged).length;
  document.getElementById("pbar").style.width = (100 * n / N) + "%";
  document.getElementById("count").textContent = n + " / " + N + " judged";
  document.getElementById("saved").textContent = n ? "saved locally" : "";
  const m = document.getElementById("main");
  if (i >= DATA.length){
    m.innerHTML = '<div class="done"><h2>All ' + N + ' done.</h2>' +
      '<p>Export below, then run the score command.</p></div>'; return;
  }
  const r = DATA[i], s1 = setOf(r.pass1), s2 = setOf(r.pass2);
  const same = s1.size === s2.size && [...s1].every(x => s2.has(x));
  const opts = [];
  opts.push(["1", "Pass 1 is right", r.pass1, [...s1]]);
  if (!same && r.pass2) opts.push(["2", "Pass 2 is right", r.pass2, [...s2]]);
  opts.push(["3", "Neither — I'll choose", "", null]);
  opts.push(["4", "Can't tell from this", "", []]);
  m.innerHTML =
    '<div class="card">' +
      '<div class="meta"><span class="chip">' + esc(r.stratum.replace(/_/g," ")) + '</span>' +
      '<span>' + esc(r.source) + '</span><span>' + (r.year || "no year") + '</span>' +
      '<span>' + esc(r.decided_by) + '</span><span>record ' + (i+1) + ' of ' + N + '</span></div>' +
      '<p class="title">' + esc(r.title || "(untitled)") + '</p>' +
      '<p class="byline">' + esc(r.author || "no author recorded") + '</p>' +
      '<div class="excerpt">' + esc(r.excerpt || "(no text)") + '</div>' +
      '<div class="props">' +
        '<div class="prop"><b>Pass 1 · llama 3.1 8b</b><span>' +
          esc(r.pass1 || "—") + '</span></div>' +
        '<div class="prop"><b>Pass 2 · sonnet</b><span>' + esc(r.pass2 || "—") + '</span></div>' +
      '</div>' +
      '<p class="q">What is this work, actually?</p>' +
      '<div class="opts">' + opts.map(([k, lab, val]) =>
        '<button data-k="' + k + '"><kbd>' + k + '</kbd><span>' + lab +
        (val ? ' — <code>' + esc(val) + '</code>' : '') + '</span></button>').join("") +
      '</div>' +
      '<div class="picker" id="picker">' + LABELS.map(l =>
        '<button data-l="' + l + '" aria-pressed="false">' + l + '</button>').join("") +
      '<button id="confirm" style="font-weight:650">Confirm →</button></div>' +
    '</div>';

  m.querySelectorAll(".opts button").forEach(b => b.onclick = () => pick(b.dataset.k));
  m.querySelectorAll(".picker [data-l]").forEach(b => b.onclick = () => {
    const l = b.dataset.l;
    if (chosen.includes(l)) chosen = chosen.filter(x => x !== l);
    else if (chosen.length < 2) chosen.push(l);
    m.querySelectorAll(".picker [data-l]").forEach(x =>
      x.setAttribute("aria-pressed", chosen.includes(x.dataset.l)));
  });
  const c = document.getElementById("confirm");
  if (c) c.onclick = () => { if (chosen.length) save(chosen); };
}

function pick(k){
  const r = DATA[i], s1 = setOf(r.pass1), s2 = setOf(r.pass2);
  const same = s1.size === s2.size && [...s1].every(x => s2.has(x));
  if (k === "1") return save([...s1]);
  if (k === "2" && !same && r.pass2) return save([...s2]);
  if (k === "4") return save([]);
  if (k === "3") document.getElementById("picker").classList.add("on");
}

document.onkeydown = e => {
  if (e.target.tagName === "INPUT") return;
  if (["1","2","3","4"].includes(e.key)) { pick(e.key); e.preventDefault(); }
  if (e.key === "ArrowLeft") { i = Math.max(0, i - 1); chosen = []; draw(); }
  if (e.key === "ArrowRight") { i = Math.min(DATA.length, i + 1); chosen = []; draw(); }
};
document.getElementById("back").onclick = () => { i = Math.max(0, i-1); chosen=[]; draw(); };
document.getElementById("skip").onclick = () => {
  i = Math.min(DATA.length, i+1); chosen=[]; draw(); };
document.getElementById("save").onclick = () => {
  const body = JSON.stringify(Object.values(judged), null, 1);
  const blob = new Blob([body], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "genre-judgements.json"; a.click();
};
document.getElementById("theme").onclick = () => {
  const cur = document.documentElement.getAttribute("data-theme");
  document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
};
draw();
</script>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    s = sub.add_parser("score")
    s.add_argument("path", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build()
    if a.cmd == "score":
        return score(a.path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
