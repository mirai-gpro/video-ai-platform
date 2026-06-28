# Docker Design Review

Covers the container strategy for the RunPod target (proposal §11).

## Targets

| Role        | GPU             | VRAM  | Image base                     |
|-------------|-----------------|-------|--------------------------------|
| Development | RunPod RTX 4090 | 24 GB | `nvidia/cuda:12.x-*-ubuntu22.04` |
| Production  | RunPod L40S     | 48 GB | same image, larger GPU          |

One image runs on both; the GPU differs at deploy time. GCP L4 is excluded
(ADR-0003).

## Image layering (`docker/Dockerfile`)

Three stages so the slow layers cache independently of fast-moving app code:

1. **`base`** — CUDA 12.x runtime, Python 3.12, `git` (submodules), `ffmpeg`
   (video I/O), and `uv` (fast, reproducible installs — §11).
2. **`deps`** — `uv pip install` from `pyproject.toml` only. Rebuilds only
   when dependencies change. Phase 1 adds `--extra gpu` once torch/CUDA wheels
   are pinned here against the submodule requirements.
3. **`app`** — copies the source. This is the only layer that rebuilds on a
   normal code change.

### Deliberate choices

- **Weights are never baked into the image.** They are large, licensed, and
  model-version-specific. They are mounted (RunPod network volume) or fetched
  to a cache dir (`HF_HOME=/workspace/.cache/huggingface`) at deploy time.
- **Submodules are not vendored into the image build context.** `.dockerignore`
  excludes `third_party/*/.git`; the platform code references upstream through
  the Provider adapters, and upstream runtime deps are installed via the `gpu`
  extra. (If a submodule ships importable Python that we call directly, Phase 1
  decides between `pip install -e third_party/<m>` in the `deps` stage vs.
  `PYTHONPATH`.)
- **CUDA 12.x + Python 3.12** per §11. PyTorch is pinned to **2.4.0**
  (torchvision 0.19.0, torchaudio 2.4.0) to match OmniAvatar 1.3B's
  requirements (ADR-0004); optional flash-attn and the Wav2Vec2 audio encoder
  are added in the `gpu` extra. Exact patch pins are fixed in Phase 1 against
  the submodule commit (see RunPod optimization review).

## Runtime

- Default `CMD` serves the REST API (`uvicorn api.app:app`). Override `CMD` for
  CLI (`vap …`) or benchmark runs in the same image.
- `docker-compose.yaml` reproduces the API locally and on a CUDA host; the GPU
  reservation block is commented for CPU-only machines and enabled on RunPod.
- Config is mounted read-only from `config/`; `outputs/` and
  `benchmarks/runs/` are mounted writable so artifacts survive the container.

## Logging

JSON logs (§11) via `python-json-logger`, to stdout, so RunPod/its log
shipper can ingest structured events without a sidecar. Wired in Phase 1
alongside the API app startup.

## Phase-1 follow-ups

- Pin CUDA/torch/attention wheels and record them here.
- Decide image registry + tagging (`:dev`, `:l40s`, git-sha tags).
- Add a RunPod template / start command and a healthcheck hitting `/healthz`.
