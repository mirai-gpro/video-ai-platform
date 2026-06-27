# Directory Structure Review

Maps the proposal §6 layout to the implemented scaffold and gives the
rationale for each top-level directory. The guiding rule: **a reader should be
able to tell, from the path alone, whether code is allowed to be
model-specific.** Only `providers/` is.

```
video-ai-platform/
├── third_party/         # upstream model repos as submodules — never forked (§7)
│   ├── SkyReels-V3/
│   └── MultiTalk/
├── providers/           # the ONLY model-specific code (§7, §8)
│   ├── base.py          #   VideoProvider contract + request/result dataclasses
│   ├── registry.py      #   name -> provider factory resolution
│   ├── skyreels/        #   SkyReels V3 adapter
│   └── multitalk/       #   MultiTalk adapter
├── pipeline/            # model-agnostic orchestration (§9)
├── api/                 # FastAPI REST surface (§10)
├── cli/                 # Typer CLI (§11) — same Pipeline as the API
├── config/             # YAML config + typed settings (§11)
├── docker/             # Dockerfile + compose, RunPod-oriented (§11)
├── benchmarks/         # record schema, CSV/JSON store, report (§§12-13)
├── outputs/            # generated artifacts (git-ignored)
├── scripts/            # operational scripts (submodule init, …)
├── tests/             # CPU-only contract/dispatch/API/benchmark tests
└── docs/
    ├── architecture/   # this review + design notes
    └── adr/            # Architecture Decision Records
```

## Notes vs. the proposal

- **Added `cli/`** — §11 requires a CLI as a first-class front-end. Splitting
  it from `api/` keeps each front-end thin while both call one `Pipeline`.
- **Added `scripts/`** — houses `init_submodules.sh` so the §7 submodule
  policy is executable, not just documented.
- **`providers/base.py` + `registry.py`** — the proposal showed `providers/`
  containing only model subfolders; the shared contract and the resolver are
  the load-bearing additions that make "add a model = add a Provider" real.

## Dependency direction (enforced by convention + tests)

```
api/ cli/  ──►  pipeline/  ──►  providers/ (base, registry)  ──►  providers/<model>  ──►  third_party/
config/    ──►  (used by api, cli, providers)
benchmarks/──►  (used by pipeline at Phase 3)
```

- Nothing above the Provider boundary imports a concrete provider module.
- `providers/<model>` is the only code permitted to import from
  `third_party/`.
- Import-time safety: the registry registers providers lazily and tolerates a
  Provider whose GPU deps are missing, so the API/CLI start on CPU-only hosts.

## `.gitignore` boundaries

Weights (`*.safetensors`, `checkpoints/`, `weights/`), generated media
(`outputs/*`), and benchmark run data (`benchmarks/runs/*`) are excluded;
`.gitkeep` files preserve the empty directories. Model artifacts are mounted
or downloaded at deploy time, never committed.
