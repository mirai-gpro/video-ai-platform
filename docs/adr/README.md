# Architecture Decision Records

ADRs capture the significant, hard-to-reverse decisions and *why* they were
made, so future contributors (and future model swaps) understand the
constraints. Required by proposal §15.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-modular-provider-architecture.md) | Model-agnostic Provider architecture | Proposed |
| [0002](0002-third-party-submodules.md) | Upstream models as git submodules (no forks) | Proposed |
| [0003](0003-gpu-environment-runpod.md) | RunPod (RTX 4090 / L40S); drop GCP L4 | Proposed |
| [0004](0004-initial-model-targets.md) | Initial model: SkyReels V3 (MultiTalk deferred) | Proposed |
| [0005](0005-benchmark-system.md) | Benchmark system from day one | Proposed |
| [0006](0006-runtime-stack.md) | Runtime stack: Python 3.12, uv, FastAPI, Typer, YAML, JSON logs | Proposed |

All ADRs are **Proposed** pending design approval (§15). On approval they move
to **Accepted** and implementation (Phase 1) begins.

New ADRs: copy [`template.md`](template.md), number sequentially, add a row above.
