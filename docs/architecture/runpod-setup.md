# RunPod RTX 4090 Setup (Development Environment)

Step-by-step procedure to prepare the **RunPod RTX 4090** development pod and
run the platform. This is the operational companion to
[`docker-design.md`](docker-design.md) and
[`runpod-optimization.md`](runpod-optimization.md).

> **Scope:** SkyReels V3 only (MultiTalk is deferred — ADR-0004). Steps that
> depend on confirming the upstream pin / weights are marked **(Phase 1)**;
> they execute once the design is approved and `scripts/init_submodules.sh` is
> wired.

```
RunPod Pod (RTX 4090)
  → Network Volume (persist weights & caches)
  → clone repo + init submodule (SkyReels V3)
  → uv install deps
  → verify CUDA / PyTorch
  → download SkyReels V3 weights
  → run API / CLI
```

---

## 1. Create the Pod

In the RunPod console: **GPU Cloud → Deploy**.

| Setting          | Recommended value                                  | Why |
|------------------|----------------------------------------------------|-----|
| GPU              | **RTX 4090 (24 GB)**                               | proposal §4 dev target |
| Template         | PyTorch / CUDA **12.x** base (e.g. `runpod/pytorch:2.x-cuda12.x`) | §11 CUDA 12.x |
| Container Disk   | 20–40 GB                                           | OS + Python deps |
| **Network Volume** | 50–100 GB, mounted at `/workspace`               | **persist weights/caches** across pod restarts |
| Exposed ports    | HTTP **8000** (API), TCP **22** (SSH)              | API served on 8000 (`api/app.py`) |

> RunPod pods are ephemeral — anything outside the Network Volume is lost when
> the pod is removed. SkyReels weights are tens of GB, so always put them on
> the Network Volume (`/workspace`).

---

## 2. Get the code (SkyReels V3 submodule)

SSH in (or use the web terminal), then:

```bash
cd /workspace
git clone <this-repo-url> video-ai-platform
cd video-ai-platform

# Initialize the SkyReels V3 submodule (Phase 1: pins confirmed in ADR-0002)
./scripts/init_submodules.sh
```

> **(Phase 1)** `init_submodules.sh` currently has the SkyReels URL commented
> out pending pin confirmation. Until then it is a no-op documenting intent.

---

## 3. Install dependencies (uv)

```bash
# Install uv if the template doesn't ship it
curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv --python 3.12
source .venv/bin/activate

# CPU-only deps work today; GPU extra (torch/flash-attn) is pinned in Phase 1
uv pip install -e ".[dev]"
# (Phase 1) uv pip install -e ".[gpu,dev]"
```

---

## 4. Verify the GPU runtime

```bash
nvidia-smi                       # RTX 4090 visible, 24 GB VRAM
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
vap providers                    # -> skyreels (V3): extend_video, talking_avatar, text_to_video
python -m pytest -q              # 16 contract tests (run without a GPU)
```

`vap providers` and the tests run **without** a GPU, so you can validate the
wiring on the pod before any weights are present.

---

## 5. Download SkyReels V3 weights  **(Phase 1)**

Store weights on the Network Volume and point the cache there (the Docker
image already sets `HF_HOME=/workspace/.cache/huggingface`):

```bash
export HF_HOME=/workspace/.cache/huggingface
mkdir -p /workspace/weights
# Fetch SkyReels V3 weights into /workspace/weights/SkyReels-V3
# (exact source/command confirmed when the upstream pin is set — ADR-0002)
```

Then set the path in config (copy `config/default.yaml` to a git-ignored
`config/local.yaml` or edit in place):

```yaml
providers:
  options:
    skyreels:
      weights_path: /workspace/weights/SkyReels-V3
      dtype: bfloat16
      attention: flash      # see runpod-optimization.md
      cpu_offload: true     # helps fit the 4090's 24 GB
```

---

## 6. Run

```bash
# REST API — reachable via the pod's exposed 8000 port
uvicorn api.app:app --host 0.0.0.0 --port 8000

# or one-shot CLI generation
vap generate --provider skyreels --prompt "..." --output outputs/test.mp4
```

In the design phase, `/generate` returns **HTTP 501** ("awaiting Phase 1
integration") and the CLI prints a clear "not available yet" message — the
full request path is exercisable before the model is wired in.

---

## 7. RTX 4090 (24 GB) notes

The 24 GB dev card is tight for video models. Apply the high-confidence wins
first (details and ordering in [`runpod-optimization.md`](runpod-optimization.md)):

- **FlashAttention + bf16** as the baseline.
- **CPU offload** (`cpu_offload: true`) to fit 24 GB when needed.
- Quality-sensitive optimizations (FP8, SageAttention) only **after** a
  benchmark A/B vs the prior setting (§18 — quality first).

Production runs on **L40S (48 GB)**: relax offload, raise resolution/duration.

---

## Alternative: run via Docker

Instead of the manual steps, build and run the image (see
[`docker-design.md`](docker-design.md)):

```bash
docker build -f docker/Dockerfile -t video-ai-platform:dev .
docker run --gpus all -p 8000:8000 \
  -v /workspace/weights:/workspace/weights \
  -v /workspace/.cache/huggingface:/workspace/.cache/huggingface \
  video-ai-platform:dev
```

---

## Checklist

- [ ] Pod: RTX 4090, CUDA 12.x template, Network Volume at `/workspace`, port 8000
- [ ] Repo cloned; SkyReels V3 submodule initialized **(Phase 1)**
- [ ] `uv` env created; deps installed
- [ ] `nvidia-smi` + `torch.cuda.is_available()` OK; `vap providers` lists skyreels
- [ ] SkyReels V3 weights on the volume; `weights_path` set in config **(Phase 1)**
- [ ] API up on 8000 / CLI runs
- [ ] First benchmark baseline captured before optimizing
