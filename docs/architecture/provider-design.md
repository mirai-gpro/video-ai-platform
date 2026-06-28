# Provider Design Review

The Provider is the seam that lets the product outlive any single model
(§8, §17). This document reviews the contract and shows how a new model is
added.

## The contract

`providers/base.py` defines:

- **`GenerationMode`** — closed enum of product capabilities
  (`text_to_video`, `talking_avatar`, `dialogue`, `singing`, `extend_video`).
  The REST `mode` field and the Pipeline dispatch table key off this.
- **`ProviderInfo`** — static identity: `name`, `model_version`, supported
  `modes`. Surfaced in `/providers` and stamped into every benchmark row.
- **Request dataclasses** — one per mode (`GenerationRequest`,
  `TalkingAvatarRequest`, `DialogueRequest`, `SingingRequest`,
  `ExtendVideoRequest`), all sharing `VideoSpec` (resolution/fps/duration/seed),
  an `output_path`, and a pass-through `extra` dict.
- **`GenerationResult`** — uniform return: output path, identity, the `spec`
  used, `inference_seconds`, and a free-form `metrics` map the benchmark layer
  reads.
- **`VideoProvider`** — ABC with one abstract member, `info`, plus the five
  capability methods. Defaults raise `UnsupportedModeError`; each Provider
  overrides exactly the modes it advertises.

## Why these shapes

- **Per-mode request types, not one mega-request.** A talking avatar needs an
  image + audio; a dialogue needs N speakers; text-to-video needs a prompt.
  Distinct types make each front-end self-documenting and let the Pipeline
  reject a mismatched `(mode, request)` pair before any model runs.
- **`extra` / `options` escape hatch.** Model-specific knobs (sampler, steps,
  attention impl, CPU-offload) must exist somewhere. Putting them in an opaque
  dict keeps them *out* of the shared types, so adding a knob to one model
  never changes the contract every other model implements.
- **Declared capabilities.** `supports(mode)` turns "does this model do
  singing?" into data the API can answer (`/providers`) and the Pipeline can
  enforce, instead of a try/except around a model call.

## Capability matrix

| Mode            | SkyReels V3 (active) | MultiTalk (deferred) |
|-----------------|:--------------------:|:--------------------:|
| text_to_video   | ✓                    |                      |
| talking_avatar  | ✓                    | ✓                    |
| dialogue        |                      | ✓                    |
| singing         |                      | ✓                    |
| extend_video    | ✓                    |                      |

SkyReels V3 is the only Provider integrated this phase. MultiTalk is deferred
(ADR-0004); its column shows the capabilities it will restore when
reintroduced. `dialogue` and `singing` modes exist in the contract now but are
unserved until MultiTalk returns. (Declared in each Provider's `info`; exact
coverage confirmed at Phase 1.)

## Adding a new model (the whole job)

To add e.g. **Wan** (proposal Phase 5):

1. Add the upstream repo as a submodule under `third_party/Wan/` (ADR-0002).
2. Create `providers/wan/__init__.py` with a `WanProvider(VideoProvider)`:
   - implement `info` (name, version, supported modes),
   - override only the supported capability methods, translating our request
     dataclasses into upstream calls and the upstream output into a
     `GenerationResult`.
3. Add a `register_provider()` and list it in `registry._bootstrap()`.
4. Add Wan's options block to `config/default.yaml`.

**No change** to `pipeline/`, `api/`, `cli/`, or any other Provider. That
invariant is the design's success criterion and is locked in by the contract
tests (`tests/test_provider_contract.py`, `tests/test_pipeline.py`).

## Error taxonomy

- `UnsupportedModeError` — requested mode not advertised (→ HTTP 400).
- `NotYetImplementedError` — advertised but not yet integrated; the
  design-phase state (→ HTTP 501).
- `ProviderError` — base for model-runtime failures (→ HTTP 5xx in Phase 1).

## Phase-1 follow-ups

- Decide whether Providers hold the model resident (warm) or load per request;
  the registry's lazy factory supports either, but warm models need a
  lifecycle/owner (likely the API app state).
- Standardize the well-known `metrics` keys (`peak_vram_gb`, `cpu_usage_percent`,
  …) so the benchmark layer reads them without per-model special-casing.
