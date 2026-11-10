"""Publish every model the study trained (owner, 2026-11-09: "publish everything"; BOM-37, BOM-72).

The 125M and 297M time-locked models are public already (``timelocked_lm.release``, GPT-2
format). This publishes the rest, weights and the numbers that came from them, never corpus text:

- ``etherfuse/timelocked-1830-590m``: the 590M (QK-norm, so native PyTorch with its own loader),
  its nine milestones, loss curves;
- ``etherfuse/bom-authorship-candidate-models``: the candidate and control models (BOM-28) at
  125M, 297M and 590M, with their validation;
- ``etherfuse/bom-authorship-benchmark-finetunes``: every kept benchmark fine-tune (Amendments 41,
  42) and every benchmark result file;
- ``etherfuse/bom-authorship-style-encoder``: the style encoder (BOM-30), 297M backbone (the
  590M's when trained);
- ``etherfuse/bom-authorship-dating-models``: the dating classifiers (BOM-29), their validation.

``stage`` (on the Mac) writes each repo's card, loader and small files to
``data/corpus/publish/<repo>/``. The weights are pulled on a pod from the private B2 backup, where
they already are; ``push`` (on the pod) hard-links them into place, uploads each repo, and writes
a SHA-256 list of every file it sent to ``data/manifests/hf_<repo>.jsonl``. The token-input
folders (``alm/candidates/inputs``: tokenised licensed text) are never staged.

Usage::

    python -m timelocked_lm.publish stage
    python -m timelocked_lm.publish push [--token-file /root/.hf_token]   # on the pod
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import shutil
import sys
from pathlib import Path

ROOT = Path("data/corpus/publish")
OWNER = "etherfuse"
GITHUB = "https://github.com/lifehug/book-of-mormon-authorship"
OSF = "https://osf.io/6ugxc/"
SIZES = {"pilot": "125M", "base": "297M", "mid": "590M"}

# repo -> (B2/corpus folder, path in the repo) pairs pulled on the pod; never alm/candidates/inputs
WEIGHTS = {
    "timelocked-1830-590m": [("data/corpus/timelocked_lm/runs/mid/milestones", "milestones")],
    "bom-authorship-candidate-models": [(f"data/corpus/alm/candidates/{z}", z) for z in SIZES],
    "bom-authorship-benchmark-finetunes": [("data/corpus/alm/benchmark", "runs")],
    "bom-authorship-style-encoder": [("data/corpus/style_embed/runs/style", "297m")],
}
SINGLE = {  # single weight files: corpus path -> path in the repo
    "timelocked-1830-590m": [("data/corpus/timelocked_lm/runs/mid/model.pt", "model.pt")],
}
PULL = sorted({src for v in WEIGHTS.values() for src, _ in v}
              | {str(Path(src).parent) for v in SINGLE.values() for src, _ in v})  # fmt: skip

COMMON = f"""Part of an open, pre-registered study of the authorship, borrowing and dating of the
earliest Book of Mormon text ({GITHUB}; pre-registration {OSF}). The project does not argue for or
against divine inspiration. Everything is published so it can be checked and redone; the corpus
texts we agreed to keep private are not, and the repository's `docs/replication.md` gives the
steps to obtain the same access.

**Licence:** CC BY-NC 4.0. **Training data:** English printed 1780-1830 (Internet Archive, Harvard
Institutional Books 1.0, HathiTrust public-domain volumes, Text Creation Partnership), with the
Book of Mormon and everything after 1830 removed; see the base model cards
(`{OWNER}/timelocked-1830-125m`). Contains derivatives of Harvard Institutional Books 1.0,
Institutional Data Initiative, Harvard Law School Library; used for noncommercial research.
**Checksums:** every file's SHA-256 is in the GitHub repository, `data/manifests/hf_<repo>.jsonl`.
"""


def _card(title: str, body: str, tags: str) -> str:
    return (f"---\nlicense: cc-by-nc-4.0\nlanguage: en\ntags: [{tags}, book-of-mormon-authorship, "
            f"1780-1830]\n---\n\n# {title}\n\n{body.strip()}\n\n## About\n\n{COMMON}")  # fmt: skip


def _loader() -> str:
    from timelocked_lm import train

    src = inspect.getsource(train.Block) + "\n\n" + inspect.getsource(train.GPT)
    return ('"""The time-locked model\'s architecture (copied from timelocked_lm/train.py)."""\n\n'
            "import math\n\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n"
            "\n\n" + src + '''

def load(path="model.safetensors", config="config.json"):
    """The model, ready to score text: ``load()(ids)`` gives next-token logits."""
    import json

    from safetensors.torch import load_file

    c = json.load(open(config))
    m = GPT(c["vocab"], c["context"], c["layers"], c["width"], c["heads"], c.get("qk_norm", False))
    m.load_state_dict(load_file(path), strict=False)  # the head is tied to the embedding
    m.head.weight = m.tok.weight
    return m.eval()
''')  # fmt: skip


def stage() -> int:
    from metadata.config import load as load_config

    cfg = load_config()
    t = cfg["timelocked_lm"]
    if ROOT.exists():
        shutil.rmtree(ROOT)
    bench = Path("data/benchmark")

    # 1. the 590M base model
    d = ROOT / "timelocked-1830-590m"
    d.mkdir(parents=True)
    run = json.loads(Path("data/corpus/timelocked_lm/runs/mid/run.json").read_text())
    sh = run["shape"]
    conf = {**sh, "vocab": run["vocab"], "context": t["context_length"],
            "params": run["params"], "steps": run["steps"]}  # fmt: skip
    (d / "config.json").write_text(json.dumps(conf, indent=1) + "\n")
    (d / "modeling_timelocked.py").write_text(_loader())
    shutil.copy("data/timelocked_lm/tokenizer.json", d / "tokenizer.json")
    shutil.copy("data/corpus/timelocked_lm/runs/mid/run.json", d / "run.json")
    rows = [json.loads(ln) for ln in open("data/corpus/timelocked_lm/runs/mid/log.jsonl")]
    with (d / "loss_curves.csv").open("w") as f:
        f.write("step,train_loss,val_loss\n")
        for r in rows:
            f.write(f"{r['step']},{r['loss']},{r.get('val_loss', '')}\n")
    final = [r for r in rows if "val_loss" in r][-1]
    (d / "README.md").write_text(
        _card(
            "Time-locked English 1780-1830 (590M, QK-norm)",
            f"""
A GPT-style model trained from scratch only on English printed 1780-1830: {sh["layers"]} layers,
width {sh["width"]}, {sh["heads"]} heads, QK-norm (each head's queries and keys layer-normalised,
Amendment 39), {run["params"]:,} parameters, {run["steps"]:,} steps of 524,288 tokens (one pass
over 25.7B tokens), peak learning rate 2.5e-4, bf16 on two H100s. Final validation loss
{final["val_loss"]:.4f} at step {final["step"]:,} (the 297M reached 2.3248).

QK-norm is not in the GPT-2 class, so the weights are native PyTorch with their own loader:

```python
from modeling_timelocked import load   # this repo's file
from tokenizers import Tokenizer
model, tok = load(), Tokenizer.from_file("tokenizer.json")
```

`model.pt` is the training run's own state dict; `model.safetensors` the same weights;
`milestones/stepNNNNNN_model.pt` the weights every 5,000 steps; `loss_curves.csv` every step.
Benchmark (110 held-out tests, `data/benchmark/alm_mid.json` in the GitHub repository): the
primary method picks the right author 0.982 of the time with 0.218 false matches.
""",
            "time-locked, historical, pytorch",
        )
    )

    # 2. candidate and control models
    d = ROOT / "bom-authorship-candidate-models"
    d.mkdir(parents=True)
    shutil.copy(bench / "alm_candidates_plan.json", d / "alm_candidates_plan.json")
    for z in SIZES:
        if (bench / f"alm_candidates_{z}.json").exists():
            shutil.copy(bench / f"alm_candidates_{z}.json", d / f"alm_candidates_{z}.json")
    (d / "README.md").write_text(
        _card(
            "Candidate and control models (BOM-28)",
            """
One fine-tuned copy of the time-locked model per candidate author's sample (`cand__...`) and per
control group (`ctrl__...`), at 125M (`pilot/`), 297M (`base/`) and 590M (`mid/`), as scored on the
sealed Book of Mormon text in the blind run (Amendment 30). Each `.pt` is a state dict for the
base model's architecture (load with `torch.load(path, weights_only=True)` into the matching
time-locked model); the `.json` beside it is its training record and held-out scores (numbers
only). `alm_candidates_<size>.json` is each size's validation, `alm_candidates_plan.json` the
units. Some candidate samples come from Joseph Smith Papers transcripts, which are not published;
the models are (owner's decision, 2026-11-09).
""",
            "authorship, fine-tuned",
        )
    )

    # 3. benchmark fine-tunes
    d = ROOT / "bom-authorship-benchmark-finetunes"
    (d / "results").mkdir(parents=True)
    for f in sorted(bench.glob("alm_*.json")) + sorted(bench.glob("lr_select_*.json")):
        if "candidates" not in f.name:
            shutil.copy(f, d / "results" / f.name)
    (d / "README.md").write_text(
        _card(
            "Benchmark fine-tunes (BOM-28, Amendments 41-42)",
            """
The language models fine-tuned for the validation benchmark (110 held-out tests), kept so every
benchmark number can be checked without retraining. `runs/<size>_<variant>/weights/` holds one
fine-tuned copy per benchmark author (V1, the primary method's procedure) or per task (V2, with its
classifier head), and the folder's `.json` files their scores; `results/alm_*.json` are the
benchmark results. Sizes: `pilot` 125M, `base` 297M, `mid` 590M. Runs: `_v1_lrsel` and `_v2_lrsel`
at the learning rate chosen on held-out training text (Amendment 41); `_v2_seed1..5` V2 with five
further seeds (Amendment 42; V2's false-match rate ranged 9-98% across seeds). The registered
runs' copies (primary, V1, V2 as first run) were scored and discarded at the time; they are being
rebuilt (BOM-72) and will be added here; their scores are in `runs/` and `results/`.
""",
            "authorship, fine-tuned, benchmark",
        )
    )

    # 4. style encoder
    d = ROOT / "bom-authorship-style-encoder"
    d.mkdir(parents=True)
    shutil.copy(bench / "style_embed.json", d / "benchmark_297m.json")
    (d / "README.md").write_text(
        _card(
            "Style encoder (BOM-30)",
            """
Authorship style embeddings (Amendment 24): the time-locked model fine-tuned with a contrastive
objective so that passages by the same author land close together. `297m/style.pt` is the
encoder on the 297M backbone (`style_embed.train.StyleEncoder` in the GitHub repository;
`load_encoder(path, cfg, "base")`), `297m/log.jsonl` its training log. Benchmark
(`benchmark_297m.json`): 0.839 right author, 0.500 false matches. The 590M backbone's encoder
will be added when trained.
""",
            "authorship, embeddings",
        )
    )

    # 5. dating models (small: from the Mac)
    d = ROOT / "bom-authorship-dating-models"
    d.mkdir(parents=True)
    for f in ("models.joblib", "transformer.joblib"):
        shutil.copy(Path("data/corpus/dating") / f, d / f)
    for f in ("models.json", "validation.json", "transformer.json", "transformer_validation.json"):
        if (Path("data/dating") / f).exists():
            shutil.copy(Path("data/dating") / f, d / f)
    (d / "README.md").write_text(
        _card(
            "Dating models (BOM-29)",
            """
Classifiers that date English prose to a 1473-1830 bin (Amendments 17, 19, 29): `models.joblib`
holds the grammar model (61 grammatical features; decides H3) and the lexical model,
`transformer.joblib` the cross-check on the 297M time-locked model's hidden states. Load with
`joblib.load` and use with `dating.classifier` in the GitHub repository. Validation
(`validation.json`, `transformer_validation.json`): held-out mean error 23 years (grammar),
13 (lexical), 10.1 (transformer).
""",
            "dating, historical-linguistics",
        )
    )
    print(f"staged {len(list(ROOT.iterdir()))} repos in {ROOT}; weights pulled on the pod: {PULL}")
    return 0


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def push(token_file: Path) -> int:
    """Upload each repo straight from where its files are (2026-11-09: hard links into the staging
    folder counted against the pod volume's quota as full copies)."""
    from huggingface_hub import HfApi

    api = HfApi(token=token_file.read_text().strip())
    for repo_dir in sorted(ROOT.iterdir()):
        name = repo_dir.name
        if name == "timelocked-1830-590m" and not (repo_dir / "model.safetensors").exists():
            import torch
            from safetensors.torch import save_file

            sd = torch.load(SINGLE[name][0][0], map_location="cpu", weights_only=True)
            sd = {k: v.contiguous() for k, v in sd.items() if k != "head.weight"}
            save_file(sd, repo_dir / "model.safetensors")
        # (folder, path in the repo, its own files only): weight folders a sub-folder at a time
        parts: list[tuple[Path, str, bool]] = []
        for src, dst in WEIGHTS.get(name, []):
            sp = Path(src)
            parts += [(p, f"{dst}/{p.name}", False) for p in sorted(sp.iterdir())
                      if p.is_dir() and p.name != "inputs"]  # fmt: skip
            if any(p.is_file() for p in sp.iterdir()):
                parts.append((sp, dst, True))
        files = [(p, str(p.relative_to(repo_dir))) for p in sorted(repo_dir.rglob("*"))
                 if p.is_file() and ".cache" not in p.parts]  # fmt: skip
        for folder, dst, own in parts:
            found = folder.glob("*") if own else folder.rglob("*")
            files += [(p, f"{dst}/{p.relative_to(folder)}") for p in sorted(found) if p.is_file()]
        files += [(Path(src), dst) for src, dst in SINGLE.get(name, [])]
        man = Path("data/manifests") / f"hf_{name}.jsonl"
        man.parent.mkdir(parents=True, exist_ok=True)
        with man.open("w") as f:
            for p, dst in files:
                f.write(json.dumps({"path": dst, "bytes": p.stat().st_size, "sha256": _sha(p)})
                        + "\n")  # fmt: skip
        repo = f"{OWNER}/{name}"
        api.create_repo(repo, repo_type="model", private=False, exist_ok=True)
        # one commit per folder; a rerun re-sends only what the Hub does not already hold
        # (content-addressed), so an interrupted push resumes
        for folder, dst, own in parts:
            api.upload_folder(repo_id=repo, folder_path=str(folder), path_in_repo=dst,
                              repo_type="model", commit_message=f"{dst}/",
                              ignore_patterns=["*/*"] if own else None)  # fmt: skip
        for src, dst in SINGLE.get(name, []):
            api.upload_file(path_or_fileobj=src, path_in_repo=dst, repo_id=repo,
                            repo_type="model", commit_message=dst)  # fmt: skip
        api.upload_folder(repo_id=repo, folder_path=str(repo_dir), repo_type="model",
                          commit_message="cards, loader and results")  # fmt: skip
        print(f"{repo}: {len(files)} files, {sum(p.stat().st_size for p, _ in files) / 1e9:.1f} "
              f"GB -> https://huggingface.co/{repo}", flush=True)  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stage")
    p = sub.add_parser("push")
    p.add_argument("--token-file", type=Path, default=Path("/root/.hf_token"))
    a = ap.parse_args(argv)
    return stage() if a.cmd == "stage" else push(a.token_file)


if __name__ == "__main__":
    sys.exit(main())
