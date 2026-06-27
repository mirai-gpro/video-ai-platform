# ADR-0004: Initial models — SkyReels V3 + MultiTalk

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

§3 sets the initial integration targets as SkyReels V3 and MultiTalk, with
Hallo2, Wan, and FaceFusion to follow (Phases 4-6). SkyReels V3's 2026 release
is the trigger to redesign the generation base (§2). MultiTalk is already
validated for two-person dialogue, singing lip-sync, and high-quality output
(§2).

## Decision

Phase 1 integrates exactly two Providers:

- **`skyreels`** — SkyReels V3: text-to-video foundation, plus talking avatar
  and video extension.
- **`multitalk`** — audio-driven talking avatar, multi-person dialogue, and
  singing lip-sync (reusing the validated capability).

Later models are added purely as new Providers (ADR-0001), no architectural
change. The benchmark system (ADR-0005) exists from day one specifically to
compare these two objectively (§12).

## Consequences

### Positive
- Complementary coverage: SkyReels for generative T2V, MultiTalk for
  audio-driven talking/singing — together they span the §1 target content.
- Two Providers immediately validate the model-agnostic boundary (more than
  one model is the real test of the abstraction).

### Negative / costs
- Two upstream runtimes to stand up and keep current in Phase 1.
- Capability overlap (both do talking avatar) requires the benchmark system to
  decide which to prefer per use case — which is the intended outcome.

## Alternatives considered

- **SkyReels only first** — simpler, but wouldn't exercise the abstraction and
  drops the validated MultiTalk dialogue/singing capability. Rejected.
- **Wait for SkyReels V4** — speculative timing; V3 is available now and the
  architecture makes a V4 swap cheap later. Rejected.
