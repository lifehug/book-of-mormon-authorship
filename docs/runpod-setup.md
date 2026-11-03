# The rented GPU (RunPod): how the BOM-27 run was set up

Written 2026-11-03, while the run was starting. The owner rents; everything on the pod is driven
from the Mac mini over SSH.

## Account

- One RunPod account, logged in with the owner's work address. The API key is in
  `~/.config/runpod/token` on the Mac (never in git or chat). A second, empty account was created
  by accident; it holds nothing.
- The Mac mini's public SSH key (`~/.ssh/id_ed25519.pub`) is under Settings, SSH Public Keys;
  RunPod puts it on every new pod.

## What we found choosing a machine

- Secure Cloud (RunPod's own datacenters) for anything carrying corpus text: the token files are
  Harvard and HathiTrust text in another form. Community Cloud is other people's machines.
- Secure H100 SXM is $3.99/h (Community $2.69). On 2026-11-03 no US datacenter with free H100s
  supported network volumes, so the pod uses its own 200 GB disk instead of a network volume, and
  the token files are uploaded straight to it. The pod landed in AP-IN-1 (India).
- The image `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` ships NumPy 1.26: install
  `pyarrow<18` (newer pyarrow needs NumPy 2), plus `tokenizers pyyaml`, and `apt-get install
  rsync tmux`.
- The pod's `/workspace` is a network filesystem that refuses `chown`: rsync with `-rt --no-o
  --no-g`, not `-a` (code 23 otherwise, even though the data arrives).
- RunPod's REST API rejects Python's default user agent (403); the watcher sends its own.

## Measured

- Upload: 48 GB at about 7-11 MB/s from the Mac (8 rsync streams).
- Pilot (124.5M): about 420,000 tokens/s with micro-batch 64 (407,000 at 32), so about 17 h for
  25.7B tokens; about $68. Base (297M): about 40 h by work per token, about $160.

## Running and watching

1. Create the pod (REST `POST /v1/pods`: Secure, `NVIDIA H100 80GB HBM3`, 60 GB container, 200 GB
   volume at `/workspace`, port `22/tcp`) and add its SSH line to `~/.ssh/config` as `bompod`.
2. Clone the repo on the pod into `/workspace/repo`; link `data/corpus/timelocked_lm` to
   `/workspace/corpus/timelocked_lm`; install the packages above.
3. `scripts/pod_upload.sh` in tmux `podupload` on the Mac.
4. Smoke test: `python -m timelocked_lm.train tiny --out /workspace/runs/tiny --max-steps 20`.
5. `scripts/pod_watch.py --pod <id> --issue <n>` in tmux `podwatch` on the Mac. From there it
   starts the pilot once every file checks out, then the base, and at the end deletes the token
   files and terminates the pod. Status: the GitHub issue "Run status".

## Afterwards

Only the models, their logs and run records come home (`data/corpus/timelocked_lm/runs/`). The
token files are deleted from the pod and the deletion verified before it is terminated.
