# ADR-0002: Upstream models as git submodules (no forks)

- **Status:** Proposed
- **Date:** 2026-06-27
- **Deciders:** Platform team

## Context

§7 requires that SkyReels V3 and MultiTalk are **not forked**. They must be
managed via git submodule (or equivalent) to follow official updates, improve
maintainability, and keep custom modification minimal. Our own code is allowed
only under `providers/`.

## Decision

Vendor each upstream model repo as a **git submodule** under `third_party/`,
pinned to a specific reviewed commit. We never edit upstream in place;
adaptation happens entirely in the corresponding `providers/<model>/` package.
Submodules are added/pinned via `scripts/init_submodules.sh`; this ADR records
the chosen upstream URLs and commit pins once confirmed.

Active scope this phase: **SkyReels V3 only** (ADR-0004). MultiTalk is
deferred; its submodule is added under this same policy when it is
reintroduced.

| Submodule | Status | Upstream URL | Pinned commit |
|-----------|--------|--------------|---------------|
| SkyReels-V3 | active (Phase 1) | `https://github.com/SkyworkAI/SkyReels-V3` | _set on first add_ |
| MultiTalk   | deferred (later) | _TBD when reintroduced_ | _TBD_ |

> **Where the submodule is added.** The Claude Code session's git egress is
> scoped to the platform repository only, so external hosts (github.com) are
> denied by egress policy there. The submodule is therefore added in a
> GitHub-reachable environment (the RunPod / local dev box) by running
> `scripts/init_submodules.sh`; commit the resulting `.gitmodules` +
> gitlink and record the pinned commit in the table above.

## Consequences

### Positive
- Follow upstream by bumping the pin; diffs are reviewable.
- No divergent fork to maintain; clean separation of "theirs" vs "ours".
- Reproducible builds (commit-pinned).

### Negative / costs
- Submodules add contributor workflow friction (`--recurse-submodules`).
- Weights are not in the submodule; they are fetched/mounted separately at
  deploy (see Docker review).
- If upstream lacks a clean import surface, the adapter absorbs more glue.

## Alternatives considered

- **Fork and patch** — explicitly forbidden by §7; creates long-term merge
  burden. Rejected.
- **Vendor a copy (no submodule)** — loses upstream-tracking and provenance.
  Rejected.
- **`pip install` upstream as a package** — only viable if upstream publishes
  a suitable package + matching versioning; reconsider per-model at Phase 1 if
  it is cleaner than a submodule for that model.
