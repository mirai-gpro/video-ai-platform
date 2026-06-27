#!/usr/bin/env bash
#
# Initialize / update the upstream model repositories as git submodules.
#
# Policy (proposal §7): SkyReels V3 and MultiTalk are NEVER forked. They are
# vendored as git submodules under third_party/ and pinned to a specific
# upstream commit so we can follow official updates deliberately. No upstream
# source is modified in place — all of our code lives under providers/.
#
# The submodule URLs/commits below are wired during Phase 1 (after design
# approval). Until then this script is the single source of truth for the
# intended layout. Replace the placeholder URLs with the official upstream
# remotes and uncomment the `git submodule add` calls to pin them.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- Upstream sources (confirm exact official URLs at Phase 1) --------------
SKYREELS_URL="${SKYREELS_URL:-https://github.com/SkyworkAI/SkyReels-V3.git}"
MULTITALK_URL="${MULTITALK_URL:-https://github.com/MeiGen-AI/MultiTalk.git}"

add_submodule() {
  local url="$1" path="$2"
  if [ -e "$path/.git" ] || git config --file .gitmodules --get-regexp "submodule.$path.url" >/dev/null 2>&1; then
    echo "[skip] $path already registered"
  else
    echo "[add ] $path <- $url"
    git submodule add "$url" "$path"
  fi
}

echo "Repo: $REPO_ROOT"
echo "NOTE: Phase 1 step. Uncomment the calls below once upstream pins are confirmed."

# add_submodule "$SKYREELS_URL"  third_party/SkyReels-V3
# add_submodule "$MULTITALK_URL" third_party/MultiTalk

# After adding, pin to reviewed commits and record them in
# docs/adr/0002-third-party-submodules.md, then:
git submodule update --init --recursive
echo "Done."
