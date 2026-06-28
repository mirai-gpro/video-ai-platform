# ADR-0004: Initial model target — OmniAvatar 1.3B (SkyReels V3 cancelled)

- **Status:** Proposed
- **Date:** 2026-06-27 (updated 2026-06-28: SkyReels V3 cancelled → OmniAvatar 1.3B)
- **Deciders:** Platform team

## Context

The initial integration target has changed during the design phase:

- §3 originally named SkyReels V3 (and MultiTalk) as the first targets.
- 2026-06-28: **SkyReels V3 is cancelled/abandoned.** The first model is now
  **OmniAvatar 1.3B** (https://omni-avatar.github.io/,
  github.com/Omni-Avatar/OmniAvatar, Apache-2.0).

OmniAvatar is an **audio-driven avatar video** model: from a reference image +
an audio track + a text prompt it produces a single-person avatar video with
lip-sync and adaptive body animation (singing supported). It builds on
Wan2.1-T2V-1.3B. The **1.3B** variant is chosen over the 14B variant because it
fits the 24 GB RTX 4090 development GPU (§4); 14B is far heavier (36 GB
unoptimized on A800-class hardware).

This fit the project's core content targets directly — idol singing MV, AI
interview, talking/dialogue, SNS shorts (§1) — which are audio-driven avatar
use cases, more so than a generic text-to-video foundation model.

## Decision

Phase 1 integrates **exactly one Provider: `omniavatar`** (OmniAvatar 1.3B),
serving the audio-driven modes:

- `talking_avatar` — reference image + audio (+ prompt) → talking-head/body video.
- `singing` — reference image + vocal track (+ prompt) → singing performance.

OmniAvatar is single-person, so **`dialogue` (multi-person) remains unserved**
and deferred (it was MultiTalk's domain). `text_to_video` is not an OmniAvatar
mode; it stays in the contract for a future T2V provider (e.g. Wan).

Other models (MultiTalk, Hallo2, Wan, FaceFusion) are added later purely as new
Providers (ADR-0001), no architectural change.

## Consequences

### Positive
- Directly matches the §1 content targets (singing MV, interview, talking).
- 1.3B fits the 24 GB RTX 4090 dev card; lower VRAM/cost than 14B (§4, §16).
- Apache-2.0 license is permissive for commercial use (§18).
- One runtime to stand up in Phase 1 → fast path to a validated, benchmarked
  pipeline on RunPod.

### Negative / costs
- No text-to-video capability this phase (OmniAvatar is audio-driven only);
  generic T2V awaits a future provider.
- `dialogue` (multi-person) is unavailable until a multi-person model (e.g.
  MultiTalk) is added.
- Quality of 1.3B vs 14B should be evaluated; if 1.3B is insufficient for
  commercial quality, the 14B variant is added as `omniavatar-14b` (a config /
  weights change, possibly with CPU offload), measured via the benchmark
  system.

## Alternatives considered

- **SkyReels V3 (previous plan)** — cancelled by the team; superseded by
  OmniAvatar 1.3B. Rejected.
- **OmniAvatar 14B** — higher quality ceiling but 36 GB-class VRAM, a poor fit
  for the 24 GB RTX 4090 dev card; revisit on L40S (48 GB) prod if 1.3B quality
  is insufficient. Deferred.
- **Keep both an avatar model and a T2V model from day one** — broader
  capability, but two runtimes to stabilize at once. Rejected for Phase 1;
  T2V/dialogue providers are additive later.
