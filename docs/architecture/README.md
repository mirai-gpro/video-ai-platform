# Architecture Review

> Status: **For approval.** Per proposal §15, this review (with the ADRs and
> the design notes alongside it) is approved **before** model implementation
> (Phase 1) begins. The repository today contains the reviewed design plus an
> interface-level scaffold; no model is integrated yet.

## 1. Goal and the one design pressure that shapes everything

The product goal (§1, §18) is a **commercial-quality** platform for short
dramas, idol MVs, AI interviews, dialogue, and SNS shorts. The single
strongest engineering pressure is **§17: this is not a SkyReels system.** The
chosen generation model *will* change — SkyReels V4, Wan, Hallo2, FaceFusion
are already named. Therefore the architecture optimizes for **swapping the
model without rewriting the product.**

Every decision below follows from that pressure.

## 2. Layered architecture

```
  ┌─────────────┐   ┌──────┐   ┌──────────┐      (front-ends; common interface)
  │  REST API   │   │ CLI  │   │ Web UI*  │      * future
  └──────┬──────┘   └──┬───┘   └────┬─────┘
         └─────────────┼────────────┘
                       ▼
                 ┌───────────┐
                 │ Pipeline  │   model-agnostic orchestration (§9)
                 └─────┬─────┘
                       ▼
                 ┌───────────┐
                 │  Registry │   name -> Provider
                 └─────┬─────┘
                       ▼
              ┌────────────────┐
              │  VideoProvider │   common interface (§8)
              └───┬────────────┘
                  ▼        ┌············┐   the ONLY model-specific code (providers/)
          ┌──────────┐    : multitalk  :   (deferred — added later, ADR-0004)
          │ skyreels │    : wan/hallo2 :
          └────┬─────┘    └············┘
               ▼
        third_party/                       upstream repos as submodules (§7)
        SkyReels-V3                         never forked, never edited
```

**The Provider boundary is the architecture.** Everything above it is written
once and reused for every model; everything model-specific lives below it.

## 3. The contract (`providers/base.py`)

A `VideoProvider` exposes the §8 capabilities — `generate`, `talking_avatar`,
`dialogue`, `singing`, `extend_video` — and declares which it supports via
`ProviderInfo.modes`. Requests/results are plain serializable dataclasses so
they cross the API/CLI boundary unchanged and are reproducible in benchmarks.

Two rules make the boundary real rather than aspirational:

1. **No model concept leaks upward.** Shared types never mention checkpoints,
   samplers, or attention kernels. Model-specific knobs travel in
   `request.extra` (and `config.providers.options`) and are interpreted only
   inside the Provider.
2. **Capability is declared, then enforced.** The Pipeline checks
   `provider.supports(mode)` before doing any work, so an unsupported request
   fails fast with a clear message instead of a deep model traceback.

## 4. Data flow for `POST /generate`

1. API validates the JSON envelope (`provider`, `mode`, inputs) → `schemas.py`.
2. It maps the envelope onto the typed request for that mode (`app._build_mode_request`).
3. `Pipeline.run` resolves the Provider via the registry, validates mode +
   request type, and dispatches to the matching method.
4. The Provider returns a uniform `GenerationResult`; (Phase 3) the Pipeline
   wraps the call in benchmark capture.
5. API shapes the result back into JSON.

The same path 1-of serves the CLI (`cli/main.py`) — proving the
"common interface for API, CLI, and future Web UI" requirement (§17).

## 5. What the scaffold deliberately does **not** do yet

- No weights are downloaded; no CUDA/torch is imported at import time.
- Providers advertise their modes but their generation methods raise
  `NotYetImplementedError` ("awaiting Phase 1 / design approval").
- The Docker `gpu` extra and CUDA/torch pins are stubbed until Phase 1 locks
  them against the submodule requirements.

This keeps the design **runnable and testable on CPU-only CI** (16 contract
tests) while honoring "review before implementation."

## 6. Review checklist (proposal §15)

| Item                       | Where |
|----------------------------|-------|
| Architecture Review        | this document |
| ADRs                       | [`../adr/`](../adr/) |
| Directory-structure review | [`directory-structure.md`](directory-structure.md) |
| Provider design review     | [`provider-design.md`](provider-design.md) |
| Docker design review       | [`docker-design.md`](docker-design.md) |
| RunPod optimization review | [`runpod-optimization.md`](runpod-optimization.md) |
| RunPod RTX 4090 setup      | [`runpod-setup.md`](runpod-setup.md) |

## 7. Open questions for sign-off

1. **Upstream pin** — confirm the official SkyReels V3 repo URL and the exact
   commit to pin (ADR-0002). (MultiTalk is deferred — ADR-0004.)
2. **Output storage** — local `outputs/` only for now, or object storage
   (S3/GCS) from the start for the commercial service?

Resolved:

- ~~**API job model**~~ — **Decided: synchronous `POST /generate` for Phase 1**
  (internal validation), async queue deferred to Phase 3. See
  [ADR-0007](../adr/0007-api-job-model.md).

These do not block the architecture; they shape Phase 1 scope.
