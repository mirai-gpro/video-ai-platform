# Video AI Platform

A **model-agnostic, modular video generation platform** for producing
commercial-quality short dramas, idol music videos, AI interviews, and
SNS-oriented short-form video.

The platform is intentionally **not** a SkyReels-only system. Video
generation models are integrated behind a common **Provider** interface so
that today's models (SkyReels V3, MultiTalk) and tomorrow's (SkyReels V4,
Wan, Hallo2, FaceFusion, …) can be swapped in by adding a Provider — without
touching the Pipeline, REST API, CLI, or future Web UI.

> **Status: Design / Review phase.**
> Per the project policy (proposal §15), the architecture, ADRs, directory
> structure, Provider design, Docker design, and RunPod optimization are
> reviewed and approved **before** model implementation begins. This
> repository currently contains the **reviewed design artifacts and the
> interface-level scaffold**. Model integration (Phase 1) starts after design
> approval.

---

## Why model-agnostic

A single generation model is a moving target: capabilities, licenses, VRAM
budgets, and speed change with every release. Coupling the product to one
model means re-writing the product every time the frontier moves. Instead:

- **Pipeline / API / CLI** depend only on the abstract `VideoProvider`
  interface — never on a model-specific SDK.
- **Model-specific code lives only under `providers/`.**
- **Upstream model repos are vendored as git submodules** under
  `third_party/` and are never forked or modified.

See [`docs/architecture/README.md`](docs/architecture/README.md) for the full
Architecture Review and [`docs/adr/`](docs/adr/) for the Architecture Decision
Records.

---

## Repository layout

```
video-ai-platform/
├── third_party/         # upstream model repos as git submodules (never forked)
│   ├── SkyReels-V3/
│   └── MultiTalk/
├── providers/           # the ONLY place model-specific code is allowed
│   ├── base.py          # VideoProvider abstract interface + data contracts
│   ├── registry.py      # name -> provider resolution
│   ├── skyreels/
│   └── multitalk/
├── pipeline/            # model-agnostic orchestration
├── api/                 # REST API (FastAPI) — common interface
├── cli/                 # command-line entrypoint
├── config/             # YAML config + schema
├── docker/             # Dockerfiles + compose (RunPod-oriented)
├── benchmarks/         # benchmark capture + report generation
├── outputs/            # generated artifacts (git-ignored)
├── tests/
└── docs/               # architecture review + ADRs
```

A directory-by-directory rationale is in
[`docs/architecture/directory-structure.md`](docs/architecture/directory-structure.md).

---

## Core contract

Every model is exposed through one interface (`providers/base.py`):

```python
class VideoProvider(ABC):
    def generate(req: GenerationRequest) -> GenerationResult: ...
    def talking_avatar(req: TalkingAvatarRequest) -> GenerationResult: ...
    def singing(req: SingingRequest) -> GenerationResult: ...
    def extend_video(req: ExtendVideoRequest) -> GenerationResult: ...
```

The REST API is uniform across models:

```http
POST /generate
{ "provider": "skyreels",  "mode": "talking_avatar" }
POST /generate
{ "provider": "multitalk", "mode": "dialogue" }
```

---

## Target environments

| Role        | GPU            | Notes                                   |
|-------------|----------------|-----------------------------------------|
| Development | RunPod RTX 4090| 24 GB VRAM                              |
| Production  | RunPod L40S    | 48 GB VRAM                              |

GCP L4 is **not** used (insufficient VRAM, insufficient inference speed, poor
cost efficiency). See
[`docs/adr/0003-gpu-environment-runpod.md`](docs/adr/0003-gpu-environment-runpod.md).

Recommended stack: Python 3.12 · CUDA 12.x · latest PyTorch · `uv` · YAML
config · JSON logs · REST API + CLI.

---

## Getting started (design-phase scaffold)

```bash
# 1. Install uv (https://docs.astral.sh/uv/)
# 2. Sync the environment (CPU-only at this stage; GPU extras added in Phase 1)
uv sync

# 3. Initialize submodules once the upstream pins are added (Phase 1)
./scripts/init_submodules.sh
```

Until model integration lands, the Providers are registered but raise a clear
"not yet implemented — awaiting design approval" error, so the wiring
(registry → provider → request contracts) can be exercised end-to-end.

---

## Roadmap

| Phase | Scope |
|-------|-------|
| 1 | SkyReels V3 + MultiTalk integration · Provider impl · Docker · RunPod |
| 2 | Talking Avatar · Dialogue · Singing modes |
| 3 | Benchmark automation · REST API · CLI |
| 4 | Hallo2 |
| 5 | Wan |
| 6 | FaceFusion |

Full phase breakdown and the performance-optimization backlog
(FlashAttention, SageAttention, torch.compile, FP8, CPU offload, xDiT, …) are
in [`docs/architecture/runpod-optimization.md`](docs/architecture/runpod-optimization.md).
