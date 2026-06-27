# ADR-0005: Benchmark system from day one

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

§12-13 require a benchmark system in the initial implementation to compare
SkyReels V3 and MultiTalk objectively and to form the baseline data for future
model comparisons. The original system's core problem was speed/cost (§2), so
measuring inference time, VRAM, and output characteristics is central — not an
afterthought. §18 makes quality the top priority, which means quality-affecting
optimizations must be decided on measured evidence.

## Decision

Define a canonical `BenchmarkRecord` (`benchmarks/record.py`) capturing every
§12 field — provider, model version, GPU, VRAM, CUDA version, resolution, fps,
length, inference time, peak VRAM, CPU usage, output size, and full generation
settings. Persist to **both CSV (append, for trend/compare) and JSON
(per-run)**. Render a human-readable report (`benchmarks/report.py`) per §13,
including a comparison block against a baseline record (% faster, VRAM delta,
bitrate delta).

The schema and writers ship with the scaffold; automatic capture is wired into
the Pipeline in Phase 3 (§14), but the schema is fixed now so early Phase-1
runs already produce comparable rows.

## Consequences

### Positive
- Model comparison and optimization decisions are evidence-based.
- Stable schema → longitudinal data across every future model.
- CSV for analysis, JSON for per-run provenance.

### Negative / costs
- Providers must report well-known metric keys (`peak_vram_gb`,
  `cpu_usage_percent`, …) uniformly; standardized in Phase 1.
- Accurate peak-VRAM/CPU capture is GPU-runtime-specific instrumentation
  (Phase 1/3).

## Alternatives considered

- **Ad-hoc logging** — not comparable across models/runs; fails the §12 intent.
  Rejected.
- **Third-party experiment tracker (W&B, MLflow)** — heavier dependency than
  needed for CSV/JSON records; can layer on later if desired. Deferred.
