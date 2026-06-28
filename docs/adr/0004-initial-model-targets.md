# ADR-0004: Initial model target — SkyReels V3 (MultiTalk deferred)

- **Status:** Proposed
- **Date:** 2026-06-27 (updated 2026-06-28: MultiTalk deferred)
- **Deciders:** Platform team

## Context

§3 originally named SkyReels V3 **and** MultiTalk as the initial integration
targets, with Hallo2, Wan, and FaceFusion to follow (Phases 4-6). SkyReels
V3's 2026 release is the trigger to redesign the generation base (§2).

Updated decision (2026-06-28): MultiTalk will **not** be tested or used in the
current phase. The team wants to focus the first integration on SkyReels V3
and validate the platform end-to-end on one model before taking on a second
runtime.

## Decision

Phase 1 integrates **exactly one Provider: `skyreels`** (SkyReels V3) —
text-to-video, talking avatar, and video extension.

**MultiTalk is deferred** to a later phase. It remains a first-class part of
the long-term vision (audio-driven talking avatar, multi-person dialogue, and
singing lip-sync, already validated on GCP L4 — §2). Because of the
model-agnostic architecture (ADR-0001), re-introducing it is purely additive:
add the submodule, add `providers/multitalk/`, register it. Nothing upstream
of the Provider boundary changes.

Consequences for product modes:

- `dialogue` and `singing` are audio-driven capabilities that MultiTalk
  serves; they move to the "later" phase **with MultiTalk**. Their request
  contracts (`DialogueRequest`, `SingingRequest`) and `GenerationMode` entries
  already exist, so no contract change is needed when MultiTalk returns.

## Consequences

### Positive
- A single runtime to stand up in Phase 1 → faster path to a validated,
  benchmarked SkyReels pipeline on RunPod.
- Less surface area to debug; the L4-validated MultiTalk setup is not blocked
  on, and is re-added cleanly when prioritized.
- The architecture is still proven model-agnostic by tests (a `FakeProvider`
  exercises the boundary) and by the contract that future Providers slot into.

### Negative / costs
- Only one real Provider is live this phase, so cross-model benchmark
  comparison (§12) starts as **setting-vs-setting** on SkyReels (e.g. baseline
  vs FlashAttention/FP8) rather than model-vs-model until MultiTalk returns.
- Dialogue/singing product capabilities are not available until MultiTalk is
  reintroduced.

## Alternatives considered

- **Integrate both now (the original §3 plan)** — broader capability sooner,
  but two runtimes to stabilize at once and MultiTalk is not currently a
  testing priority. Rejected for this phase.
- **Drop MultiTalk permanently** — loses the validated dialogue/singing
  capability central to the §1 content targets. Rejected; deferred, not
  dropped.
- **Wait for SkyReels V4** — speculative timing; V3 is available now and a V4
  swap is cheap later. Rejected.
