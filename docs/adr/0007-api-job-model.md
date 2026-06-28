# ADR-0007: API job model — synchronous for Phase 1, async queue later

- **Status:** Proposed
- **Date:** 2026-06-28
- **Deciders:** Platform team

## Context

Video generation takes minutes per clip (SkyReels V3 target single-digit
minutes; the prior MultiTalk/L4 baseline was ~40 min — §2). A single GPU
(RTX 4090 dev / L40S prod) is saturated by one generation at a time. The REST
API (§10) must decide how a caller waits for a multi-minute result:

- **A. Synchronous** — `POST /generate` holds the connection until the file is
  ready, then returns it.
- **B. Asynchronous queue** — `POST /generate` returns a `job_id` immediately;
  the caller polls `GET /jobs/{id}` (or receives a webhook); a worker drains a
  queue one job at a time.

This choice lives entirely in the `api/` layer — `Pipeline`, the Provider
contract, and the CLI are unaffected by it.

## Decision

**Phase 1 uses the synchronous `POST /generate`** (option A), as already
implemented in the scaffold. The goal of Phase 1 is to validate the SkyReels
V3 integration end-to-end internally, and the synchronous path is the simplest
thing that proves the request → Pipeline → Provider flow.

**The async queue (option B) is deferred to Phase 3** (commercial hardening),
where multi-user load, HTTP/proxy timeouts, progress reporting, and
backpressure make it effectively required. Migration is additive in the `api/`
layer: a worker calls the same `Pipeline.run()`; no change below the API.

Phase 1 constraints to stay within the synchronous model:
- Internal/controlled callers only (not public traffic).
- Keep validation clips short and run behind clients/proxies with generous
  timeouts; long generations may exceed default HTTP/proxy timeouts — this is
  an accepted Phase 1 limitation, and the trigger to move to B.

## Consequences

### Positive
- Zero extra infrastructure (no queue, worker, or job store) in Phase 1 →
  fastest path to a validated SkyReels pipeline.
- The scaffold already implements it; no API rework to start Phase 1.
- The Provider/Pipeline boundary is untouched, so the later move to B does not
  ripple into model code.

### Negative / costs
- Synchronous calls can hit HTTP/proxy/load-balancer timeouts on long
  generations — not suitable for public/commercial traffic.
- No progress reporting and no backpressure: concurrent requests contend on
  the single GPU with no queue to absorb bursts.
- These limits are the explicit signal to execute the Phase 3 migration.

## Alternatives considered

- **Async queue from day one (B)** — correct end state, but adds queue +
  worker + job-state + result-storage work that would slow Phase 1 validation
  on a single-GPU setup. Deferred to Phase 3.
- **Lightweight async middle ground** (FastAPI `BackgroundTasks` + SQLite job
  table, polling only) — gets timeout avoidance and progress cheaply; kept as
  the recommended first step of the Phase 3 migration if a full queue is
  overkill on one GPU.

## Follow-ups (Phase 3)

- Add `POST /generate` → `job_id`, `GET /jobs/{id}` status, and a worker that
  calls `Pipeline.run()`.
- Tie result delivery to the output-storage decision (S3/GCS) — async results
  need durable storage to hand back a URL.
- Decide job retention/cleanup and timeout/cancellation policy.
