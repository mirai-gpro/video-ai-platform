# ADR-0006: Runtime stack

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

§11 recommends Python 3.12, CUDA 12.x, latest PyTorch, `uv`, YAML config, JSON
logs, REST API, and CLI, with RunPod as the deployment premise. The platform
needs one orchestration layer behind two front-ends (API + CLI) that stay thin
and share all logic (§17).

## Decision

| Concern        | Choice            | Why |
|----------------|-------------------|-----|
| Language       | Python 3.12       | §11; modern typing, `StrEnum` |
| Packaging/env  | `uv` + `pyproject` | §11; fast, reproducible, used in Docker |
| REST API       | FastAPI + uvicorn | typed models, OpenAPI, async-ready (§10) |
| CLI            | Typer             | shares logic with API via the Pipeline (§11) |
| Config         | YAML → pydantic   | §11; declarative, typed, env-overridable |
| Logging        | JSON (python-json-logger) | §11; RunPod-friendly structured logs |
| GPU deps       | optional `gpu` extra | keeps base/CI CPU-only; CUDA pinned in Phase 1 |

Heavy ML/CUDA dependencies are intentionally kept out of the base dependency
set and pulled in via the `gpu` extra, so the design-phase scaffold installs
and tests on CPU-only CI.

## Consequences

### Positive
- API and CLI are thin shells over one `Pipeline` — no duplicated logic.
- CPU-only installability keeps CI fast and the design testable pre-integration.
- Config/logging choices match RunPod operational needs out of the box.

### Negative / costs
- Two dependency profiles (base vs `gpu`) to keep coherent.
- FastAPI's current sync `POST /generate` blocks for multi-minute generations;
  an async job/queue model is an open question for Phase 1 (see Architecture
  Review §7).

## Alternatives considered

- **Flask + argparse** — more boilerplate, no built-in typing/OpenAPI. Rejected.
- **poetry / pip-tools** — fine, but §11 calls for `uv` and it is faster in the
  Docker build. Rejected.
- **TOML/JSON config** — YAML chosen per §11 and for human-friendly nested
  provider options.
