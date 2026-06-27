# third_party/

Upstream model repositories live here as **git submodules** and are **never
forked or modified** (proposal §7).

| Path                     | Upstream            | Purpose                                  |
|--------------------------|---------------------|------------------------------------------|
| `third_party/SkyReels-V3`| SkyReels V3 (TBD)   | Text-to-video foundation model           |
| `third_party/MultiTalk`  | MultiTalk (TBD)     | Audio-driven dialogue & singing lip-sync |

Submodules are added and pinned during **Phase 1** via
[`scripts/init_submodules.sh`](../scripts/init_submodules.sh). The exact
upstream URLs and pinned commits are recorded in
[`docs/adr/0002-third-party-submodules.md`](../docs/adr/0002-third-party-submodules.md).

**Rule:** all of our own code lives under `providers/`. Nothing in this
directory is edited; we adapt to upstream, not the reverse. This keeps us able
to follow official updates by bumping the submodule pin.
