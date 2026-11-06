"""Public release of the time-locked models (BOM-66).

``convert`` maps a trained model (``runs/<size>/model.pt``) onto Hugging Face's GPT-2 class, which
has the same shape (pre-norm blocks, learned positions, tied embeddings) once the biases our model
lacks are set to zero and the activation is the exact GELU, then checks the converted model's
logits against the native one's on held-out tokens. ``card`` writes the model card and the loss
curves (step, train loss, validation loss; numbers only). ``upload`` sends the release folder to
a Hugging Face model repo. Nothing in a release folder is training text.

Usage::

    python -m timelocked_lm.release convert pilot|base|large
    python -m timelocked_lm.release card pilot|base|large --repo <owner/name>
    python -m timelocked_lm.release upload pilot|base|large --repo <owner/name>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

from metadata.config import load as load_config
from timelocked_lm.train import GPT, TOKENS

RUNS = Path("data/corpus/timelocked_lm/runs")
OUT = Path("data/corpus/timelocked_lm/release")
TOKENIZER = Path("data/timelocked_lm/tokenizer.json")
EOT = "<|endoftext|>"
CARD = Path(__file__).with_name("model_card.md")
TOKEN = Path.home() / ".config/huggingface/token"


def _native(size: str) -> tuple[GPT, dict]:
    cfg = load_config()["timelocked_lm"]
    shape = cfg[f"{size}_shape"]
    model = GPT(cfg["vocab_size"], cfg["context_length"], shape["layers"], shape["width"],
                shape["heads"])  # fmt: skip
    model.load_state_dict(torch.load(RUNS / size / "model.pt", map_location="cpu"))
    return model.eval(), {**shape, "vocab": cfg["vocab_size"], "context": cfg["context_length"]}


def _hf_state(sd: dict, layers: int) -> dict:
    """Our parameter names and layouts -> GPT-2's (Conv1D weights are transposed)."""
    out = {"transformer.wte.weight": sd["tok.weight"], "transformer.wpe.weight": sd["pos.weight"],
           "transformer.ln_f.weight": sd["ln.weight"]}  # fmt: skip
    out["transformer.ln_f.bias"] = torch.zeros_like(sd["ln.weight"])
    for i in range(layers):
        a, b = f"blocks.{i}.", f"transformer.h.{i}."
        pairs = {"ln_1": "ln1", "ln_2": "ln2"}
        for hf, ours in pairs.items():
            out[b + f"{hf}.weight"] = sd[a + f"{ours}.weight"]
            out[b + f"{hf}.bias"] = torch.zeros_like(sd[a + f"{ours}.weight"])
        conv = {"attn.c_attn": "qkv", "attn.c_proj": "proj", "mlp.c_fc": "fc", "mlp.c_proj": "out"}
        for hf, ours in conv.items():
            w = sd[a + f"{ours}.weight"].t().contiguous()
            out[b + f"{hf}.weight"] = w
            out[b + f"{hf}.bias"] = torch.zeros(w.shape[1], dtype=w.dtype)
    return out


def convert(size: str) -> int:
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

    model, s = _native(size)
    tok = PreTrainedTokenizerFast(tokenizer_file=str(TOKENIZER), bos_token=EOT, eos_token=EOT,
                                  unk_token=EOT)  # fmt: skip
    eot = tok.convert_tokens_to_ids(EOT)
    conf = GPT2Config(vocab_size=s["vocab"], n_positions=s["context"], n_embd=s["width"],
                      n_layer=s["layers"], n_head=s["heads"], activation_function="gelu",
                      resid_pdrop=0.0, embd_pdrop=0.0, attn_pdrop=0.0, layer_norm_epsilon=1e-5,
                      bos_token_id=eot, eos_token_id=eot, tie_word_embeddings=True)  # fmt: skip
    hf = GPT2LMHeadModel(conf)
    missing, unexpected = hf.load_state_dict(_hf_state(model.state_dict(), s["layers"]),
                                             strict=False)  # fmt: skip
    missing = [m for m in missing if m != "lm_head.weight"]  # tied to wte
    if missing or unexpected:
        raise SystemExit(f"weight mapping incomplete: missing {missing}, unexpected {unexpected}")
    hf.eval()
    val = np.memmap(sorted(TOKENS.glob("validation_*.bin"))[0], dtype=np.uint16, mode="r")
    x = torch.from_numpy(np.asarray(val[: 4 * 512], dtype=np.int64).reshape(4, 512))
    with torch.no_grad():
        diff = (model(x) - hf(x).logits).abs().max().item()
    print(f"{size}: max |logit difference| native vs Hugging Face = {diff:.2e}", flush=True)
    if diff > 1e-3:
        raise SystemExit("converted model does not match the native one")
    dest = OUT / size
    if dest.exists():
        shutil.rmtree(dest)
    hf.save_pretrained(dest)
    tok.save_pretrained(dest)
    check = {"max_abs_logit_diff": diff, "tokens_checked": int(x.numel()),
             "source": f"held-out validation tokens, {x.shape[0]} x {x.shape[1]}"}  # fmt: skip
    (dest / "conversion_check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(f"-> {dest}")
    return 0


def _curves(size: str) -> list[dict]:
    rows = []
    for ln in (RUNS / size / "log.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if r["step"] % 100 == 0 or "val_loss" in r:
            v = round(r["val_loss"], 4) if "val_loss" in r else None
            rows.append({"step": r["step"], "train_loss": round(r["loss"], 4), "val_loss": v})
    return rows


def card(size: str, repo: str) -> int:
    run = json.loads((RUNS / size / "run.json").read_text())
    sel = json.loads(Path("data/timelocked_lm/selection.json").read_text())
    rows = _curves(size)
    dest = OUT / size
    with (dest / "loss_curves.csv").open("w") as f:
        f.write("step,train_loss,val_loss\n")
        for r in rows:
            v = "" if r["val_loss"] is None else r["val_loss"]
            f.write(f"{r['step']},{r['train_loss']},{v}\n")
    final_val = [r for r in rows if r["val_loss"] is not None][-1]
    tokens = run["train_windows"] * (run["seq"] + 1)
    by = sel["by_source"]
    kept = sum(by.values())
    sh = run["shape"]
    name = {"pilot": "125M pilot", "base": "300M base", "large": "1B large"}[size]
    text = CARD.read_text().format(
        repo=repo,
        size=size,
        name=name,
        sh=sh,
        run=run,
        tokens_b=f"{tokens / 1e9:.1f}",
        final=final_val,
        by=by,
        kept=kept,
        ex=sel["excluded"],
    )
    (dest / "README.md").write_text(text)
    print(f"-> {dest / 'README.md'}; {len(rows)} loss-curve rows")
    return 0


def upload(size: str, repo: str) -> int:
    from huggingface_hub import HfApi

    dest = OUT / size
    for need in ("README.md", "model.safetensors", "tokenizer.json", "loss_curves.csv"):
        if not (dest / need).exists():
            raise SystemExit(f"{dest / need} missing; run convert and card first")
    token = TOKEN.read_text().strip()  # the owner's etherfuse account (owner, 2026-11-05)
    api = HfApi(token=token)
    api.create_repo(repo, repo_type="model", private=False, exist_ok=True)
    api.upload_folder(folder_path=str(dest), repo_id=repo, repo_type="model",
                      commit_message=f"BOM-66: {size} model release")  # fmt: skip
    print(f"-> https://huggingface.co/{repo}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["convert", "card", "upload"])
    ap.add_argument("size", choices=["pilot", "base", "large"])
    ap.add_argument("--repo")
    a = ap.parse_args(argv)
    if a.cmd == "convert":
        return convert(a.size)
    if not a.repo:
        ap.error("--repo is required")
    return {"card": card, "upload": upload}[a.cmd](a.size, a.repo)


if __name__ == "__main__":
    sys.exit(main())
