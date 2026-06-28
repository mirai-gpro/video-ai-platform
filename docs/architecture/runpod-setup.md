# RunPod RTX 4090 Setup (Development Environment)

Step-by-step procedure to prepare the **RunPod RTX 4090** development pod and
run the platform. Operational companion to [`docker-design.md`](docker-design.md)
and [`runpod-optimization.md`](runpod-optimization.md).

> **Scope:** OmniAvatar 1.3B only (ADR-0004; SkyReels V3 cancelled). OmniAvatar
> is audio-driven — it generates avatar video from a **reference image + audio
> (+ prompt)**, serving the `talking_avatar` and `singing` modes. Steps that
> depend on the submodule/weights are marked **(Phase 1)**; they execute once
> the submodule is materialized and its API confirmed.

```
RunPod Pod (RTX 4090)
  → Network Volume (persist weights & caches)
  → clone repo + init submodule (OmniAvatar)
  → uv install deps (PyTorch 2.4.0)
  → verify CUDA / PyTorch
  → download OmniAvatar 1.3B + Wan2.1-1.3B + wav2vec2 weights
  → run talking-avatar / singing
```

---

## 1. Create the Pod

In the RunPod console: **GPU Cloud → Deploy**.

| Setting          | Recommended value                                  | Why |
|------------------|----------------------------------------------------|-----|
| GPU              | **RTX 4090 (24 GB)**                               | §4 dev target; 1.3B fits comfortably |
| Template         | PyTorch / CUDA **12.x** base                       | §11; OmniAvatar uses PyTorch 2.4.0 |
| Container Disk   | 20–40 GB                                           | OS + Python deps |
| **Network Volume** | 50–100 GB, mounted at `/workspace`               | **persist weights/caches** across restarts |
| Exposed ports    | HTTP **8000** (API), TCP **22** (SSH)              | API served on 8000 |

> RunPod pods are ephemeral — anything outside the Network Volume is lost when
> the pod is removed. OmniAvatar + Wan2.1 weights are several GB, so put them on
> the Network Volume (`/workspace`).

---

## 2. Get the code (OmniAvatar submodule)

```bash
cd /workspace
git clone <this-repo-url> video-ai-platform
cd video-ai-platform

# Initialize the OmniAvatar submodule (github.com/Omni-Avatar/OmniAvatar)
./scripts/init_submodules.sh
```

---

## 3. Install dependencies (uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12
source .venv/bin/activate

# CPU-only deps work today; the GPU extra (torch 2.4.0 etc.) is pinned in Phase 1
uv pip install -e ".[dev]"
# (Phase 1) uv pip install -e ".[gpu,dev]"   # PyTorch 2.4.0, transformers, optional flash-attn
```

---

## 4. Verify the GPU runtime

```bash
nvidia-smi                       # RTX 4090 visible, 24 GB VRAM
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
vap providers                    # -> omniavatar (1.3B): singing, talking_avatar
python -m pytest -q              # 22 tests (run without a GPU)
```

`vap providers` and the tests run **without** a GPU.

---

## 5. Download weights  **(Phase 1)**

OmniAvatar 1.3B needs three HuggingFace repos. Store them on the Network Volume
(`HF_HOME=/workspace/.cache/huggingface` is set by the Docker image):

```bash
export HF_HOME=/workspace/.cache/huggingface
mkdir -p /workspace/weights
# OmniAvatar/OmniAvatar-1.3B     (the avatar model)
# Wan-AI/Wan2.1-T2V-1.3B         (base model)
# facebook/wav2vec2-base-960h    (audio encoder)
# (exact download commands per the upstream README once the submodule is present)
```

Then set the options in config (copy `config/default.yaml` to a git-ignored
`config/local.yaml` or edit in place):

```yaml
providers:
  options:
    omniavatar:
      weights_path: /workspace/weights/OmniAvatar-1.3B
      config: configs/inference_1.3B.yaml
      num_steps: 25            # 20-50
      guidance_scale: 4.5
      audio_scale: 3.0
      dtype: bfloat16
      flash_attn: true
      # cpu_offload: false     # 1.3B fits 24GB; enable only if needed
```

---

## 6. Run

OmniAvatar is audio-driven, so generation takes a **reference image + audio**:

```bash
# REST API — reachable via the pod's exposed 8000 port
uvicorn api.app:app --host 0.0.0.0 --port 8000

# CLI: talking avatar
vap talking-avatar --provider omniavatar \
  --image inputs/face.png --audio inputs/speech.wav \
  --prompt "a calm news anchor" --output outputs/talk.mp4

# CLI: singing
vap singing --provider omniavatar \
  --image inputs/idol.png --audio inputs/vocal.wav --output outputs/song.mp4
```

REST equivalent:

```http
POST /generate
{ "provider": "omniavatar", "mode": "talking_avatar",
  "reference_image": "inputs/face.png", "audio": "inputs/speech.wav",
  "prompt": "a calm news anchor" }
```

In the design phase, `/generate` returns **HTTP 501** ("awaiting Phase 1
integration") and the CLI prints a clear "not available yet" message — the full
request path is exercisable before the model is wired in.

---

## 7. RTX 4090 (24 GB) notes

OmniAvatar **1.3B** is small enough to fit 24 GB comfortably, so the priority is
**speed**, not fitting VRAM (see [`runpod-optimization.md`](runpod-optimization.md)):

- **FlashAttention + bf16** as the baseline (`flash_attn: true`).
- CPU offload usually **not** needed at 1.3B (unlike 14B).
- Quality-sensitive optimizations (FP8) only **after** a benchmark A/B vs the
  prior setting (§18 — quality first).

If 1.3B quality is insufficient for commercial use, the **14B** variant is added
later (on L40S 48 GB, possibly with offload), measured via the benchmark system.

---

## Alternative: run via Docker

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
- [ ] Repo cloned; OmniAvatar submodule initialized **(Phase 1)**
- [ ] `uv` env created; deps installed
- [ ] `nvidia-smi` + `torch.cuda.is_available()` OK; `vap providers` lists omniavatar
- [ ] Weights (OmniAvatar-1.3B + Wan2.1-1.3B + wav2vec2) on the volume; options set **(Phase 1)**
- [ ] API up on 8000 / CLI runs talking-avatar + singing
- [ ] First benchmark baseline captured before optimizing
