# RunPod / Performance Optimization Review

Reviews the §16 optimization backlog against the §4 hardware (RunPod RTX 4090
dev, L40S prod) and the §2 baseline problem: MultiTalk on GCP L4 took **~40
min for a 15 s clip** — commercially too slow. The target is to move
decisively below that while holding commercial quality (§18).

## Hardware framing

| GPU       | VRAM  | FP8 (Ada) | Role  | Implication                         |
|-----------|-------|-----------|-------|-------------------------------------|
| RTX 4090  | 24 GB | yes       | dev   | Tight VRAM → offload/quantization matter |
| L40S      | 48 GB | yes       | prod  | Headroom for higher res / batching  |
| ~~L4~~    | 24 GB | yes       | —     | Dropped: too slow, poor cost (ADR-0003) |

Both targets are **Ada Lovelace**, so FP8 and the latest FlashAttention /
SageAttention kernels are available — the optimization plan assumes Ada.

## Backlog, prioritized

Each technique is applied **inside Providers** (or via config), never in the
shared layers, so optimization never violates the model-agnostic boundary.

| # | Technique          | Expected effect                  | Risk / notes | Phase |
|---|--------------------|----------------------------------|--------------|-------|
| 1 | FlashAttention     | Large speed + VRAM win on attention | kernel/build pinning | 1 |
| 2 | bf16/fp16 baseline | Standard speed/VRAM baseline      | quality check vs fp32 | 1 |
| 3 | torch.compile      | 10-30% via fused kernels          | first-call compile cost; cache it | 1-2 |
| 4 | SageAttention      | Further attention speedup (Ada)   | numerical validation | 2 |
| 5 | CPU offload        | Fits 4090's 24 GB                 | slower; dev-tier tradeoff | 1 |
| 6 | FP8                | Speed + VRAM on Ada               | quality-sensitive; gate behind benchmark | 2 |
| 7 | VRAM optimization  | Larger res / longer clips         | tiling/slicing per model | 2 |
| 8 | CUDA optimization  | Allocator/stream tuning           | measure before/after | 2-3 |
| 9 | xDiT (where supported) | Multi-GPU diffusion parallel  | only models that support it | future |
|10 | Multi-GPU          | Throughput / longer content       | infra + cost | future |

**Sequencing principle:** land the high-confidence, low-risk wins first
(FlashAttention, bf16, CPU offload to fit the 4090), then the
quality-sensitive ones (FP8, SageAttention) **gated by the benchmark system**
so any quality regression is caught objectively (§§12-13).

## Quality is the gate, not just speed

§18 makes quality the top priority. Therefore no quality-affecting
optimization (FP8, aggressive quantization, step reduction) ships without a
benchmark run comparing it against the prior setting on the same inputs. The
benchmark record already captures `peak_vram_gb`, `inference_seconds`,
`output_file_size_mb`, and full `generation_settings` to support exactly this
A/B comparison.

## Dev → prod path

- **RTX 4090 (dev):** optimize to fit 24 GB — FlashAttention + bf16 + CPU
  offload as needed; accept some offload latency.
- **L40S (prod):** with 48 GB, relax offload, raise resolution/duration, and
  reassess torch.compile/FP8 with production-quality settings.

## Phase-1 follow-ups

- Establish the **first benchmark baseline** (SkyReels V3 on the 4090, default
  settings) before any optimization, so every later number is relative to a
  real starting point — the §12 "future model comparison" foundation. (MultiTalk
  is deferred — ADR-0004 — so initial comparisons are SkyReels setting-vs-setting.)
- Pin FlashAttention/SageAttention builds to the CUDA/torch versions chosen in
  the Docker review.
- Record an `attention`/`dtype`/`cpu_offload` option per provider in
  `config/default.yaml` (already stubbed) so optimizations are config-driven
  and benchmarkable.
