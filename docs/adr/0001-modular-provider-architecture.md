# ADR-0001: Model-agnostic Provider architecture

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

The platform must not be tied to one generation model (§17). MultiTalk, Wan,
Hallo2, and FaceFusion are named as future targets (§3, §17). The prior
system was effectively MultiTalk-specific; re-coupling the product to a single
model would force a rewrite at every model change. Model-dependent code is
explicitly **prohibited** outside a defined boundary (§17).

## Decision

Adopt the **Provider pattern**. Define one abstract interface,
`VideoProvider` (`providers/base.py`), exposing the §8 capabilities
(`generate`, `talking_avatar`, `dialogue`, `singing`, `extend_video`). All
model-specific code lives under `providers/<model>/` and nowhere else. The
Pipeline, REST API, CLI, and future Web UI depend only on the abstract
contract and resolve a concrete Provider by name through a registry.

Requests/results are plain serializable dataclasses; model-specific options
travel in an opaque `extra`/`options` field and are interpreted only inside
the Provider.

## Consequences

### Positive
- Adding a model = adding a Provider; no change to Pipeline/API/CLI (locked in
  by contract tests).
- One uniform REST/CLI surface across all models (§10).
- Clear, testable boundary; design is exercisable on CPU-only CI before any
  model is integrated.

### Negative / costs
- An adapter must be written per model to translate to/from the shared types.
- The shared contract must be expressive enough for diverse models; genuinely
  novel capabilities may require additive contract changes (new `GenerationMode`
  + request type) — additive, not rewrites.

## Alternatives considered

- **Direct model calls from the Pipeline** — fastest to first output, but
  violates §17 and guarantees a rewrite at the next model change. Rejected.
- **Plugin auto-discovery (entry points / import scanning)** — more "magic"
  than needed for a handful of in-repo models; hurts readability and makes a
  single Provider's missing GPU dep able to break import. Deferred; explicit
  registration chosen.
