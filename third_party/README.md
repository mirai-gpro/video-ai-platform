# third_party/

Upstream model repositories live here as **git submodules** and are **never
forked or modified** (proposal §7).

| Path                     | Status            | Purpose                                  |
|--------------------------|-------------------|------------------------------------------|
| `third_party/OmniAvatar` | active (Phase 1)  | Audio-driven avatar video (talking / singing), 1.3B |
| `third_party/MultiTalk`  | deferred (later)  | Multi-person dialogue (ADR-0004)         |

Submodules are added and pinned during **Phase 1** via
[`scripts/init_submodules.sh`](../scripts/init_submodules.sh). The exact
upstream URLs and pinned commits are recorded in
[`docs/adr/0002-third-party-submodules.md`](../docs/adr/0002-third-party-submodules.md).

**Rule:** all of our own code lives under `providers/`. Nothing in this
directory is edited; we adapt to upstream, not the reverse. This keeps us able
to follow official updates by bumping the submodule pin.

## Updating (bumping the pin)

Submodules are **pinned to a reviewed commit** and **never auto-updated**
(ADR-0002, policy A). To follow an official update deliberately:

```bash
# 1. Move the pin to a chosen commit/tag and print the upstream diff
scripts/bump_submodule.sh third_party/OmniAvatar <git-ref>

# 2. Review the diff, update providers/omniavatar if the API changed,
#    re-benchmark vs the previous pin, then record + commit:
git add third_party/OmniAvatar docs/adr/0002-third-party-submodules.md
git commit -m "Bump OmniAvatar to <ref>"
```

Run this in a GitHub-reachable environment (RunPod / local dev); the Claude
Code session's git is routed to a repo-scoped proxy. A given build always uses
the exact pinned commit — runtime never fetches "latest".
