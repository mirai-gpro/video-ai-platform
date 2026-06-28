# ADR-0008: Output storage — local `outputs/` for Phase 1

- **Status:** Proposed
- **Date:** 2026-06-28
- **Deciders:** Platform team

## Context

Generated videos must be written somewhere and handed back to the caller. Two
options were considered: write to the local filesystem (`outputs/`), or push
to object storage (S3 / GCS) from the start for the eventual commercial
service. This interacts with the API job model (ADR-0007): a future async
queue needs durable storage to return a result URL.

## Decision

**Phase 1 writes to the local `outputs/` directory** (already the default in
`config/default.yaml` → `output_dir: outputs`). On RunPod this is the Network
Volume mounted at `/workspace`, so artifacts survive pod restarts.

Object storage (S3 / GCS) is **deferred** to the commercial-hardening phase,
introduced alongside the async job model (ADR-0007), since durable result URLs
become necessary once generation is decoupled from the HTTP response.

## Consequences

### Positive
- Simplest path for Phase 1 internal validation — no storage SDK, credentials,
  or bucket setup.
- `output_path` already flows through the request/result contract; the Provider
  writes a file and returns its path unchanged.
- On RunPod the Network Volume gives persistence without extra work.

### Negative / costs
- Not durable/shareable beyond the pod; fine for internal validation, not for a
  multi-user commercial service.
- The move to object storage is a Phase-3 follow-up (paired with the async job
  model).

## Migration path (Phase 3)

- Add an output-sink abstraction in the **API/Pipeline layer** (not in
  Providers): the Provider keeps writing a local file; the sink uploads it to
  S3/GCS and the API returns the object URL.
- Because Providers only know `output_path`, this change does not touch model
  code — consistent with the model-agnostic boundary (ADR-0001).

## Alternatives considered

- **Object storage from day one** — correct end state, but adds credentials,
  SDK, and bucket lifecycle work that does not help Phase 1 validation on a
  single box. Deferred.
