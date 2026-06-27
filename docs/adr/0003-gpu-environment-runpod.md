# ADR-0003: RunPod (RTX 4090 / L40S); drop GCP L4

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

The prior MultiTalk work ran on GCP L4 and took ~40 min for a 15 s clip — too
slow and cost-inefficient for a commercial service (§2). §4 sets the target
environments and explicitly excludes GCP L4 for insufficient VRAM, insufficient
inference speed, and poor cost efficiency.

## Decision

- **Development:** RunPod **RTX 4090** (24 GB).
- **Production:** RunPod **L40S** (48 GB).
- **GCP L4 is not used.**

Both targets are Ada Lovelace, so the optimization plan (FP8, latest
FlashAttention/SageAttention kernels) assumes Ada (see RunPod optimization
review).

## Consequences

### Positive
- Faster, more cost-efficient generation than L4.
- Single Ada-based image serves dev and prod; only the GPU differs at deploy.
- L40S's 48 GB gives prod headroom for higher resolution / longer clips.

### Negative / costs
- RTX 4090's 24 GB is tight for large video models → CPU offload / quantization
  needed at the dev tier.
- RunPod operational specifics (volumes, templates) to be standardized in
  Phase 1.

## Alternatives considered

- **Keep GCP L4** — rejected per §4 (VRAM/speed/cost).
- **A100/H100** — more capable but higher cost; not required to beat the L4
  baseline and outside the proposal's stated targets. Revisit only if prod
  throughput demands it.
