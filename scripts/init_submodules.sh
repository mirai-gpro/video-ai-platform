#!/usr/bin/env bash
#
# Initialize / update the upstream model repositories as git submodules.
#
# Policy (proposal §7): upstream model repos are NEVER forked. They are
# vendored as git submodules under third_party/ and pinned to a specific
# upstream commit so we can follow official updates deliberately. No upstream
# source is modified in place — all of our code lives under providers/.
#
# Active scope this phase: OmniAvatar 1.3B only (ADR-0004). Other models
# (e.g. MultiTalk for multi-person dialogue) are deferred and added under the
# same policy when reintroduced.
#
# Run this in a GitHub-reachable environment (RunPod / local dev); the Claude
# Code session's git is routed to a repo-scoped proxy. After adding, pin to the
# reviewed commit and record it in docs/adr/0002-third-party-submodules.md.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- Upstream sources -------------------------------------------------------
OMNIAVATAR_URL="${OMNIAVATAR_URL:-https://github.com/Omni-Avatar/OmniAvatar.git}"
# MultiTalk deferred (ADR-0004); restore when reintroduced:
# MULTITALK_URL="${MULTITALK_URL:-https://github.com/MeiGen-AI/MultiTalk.git}"

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
echo "Adding/updating the OmniAvatar submodule (requires network access to github.com)."

# OmniAvatar 1.3B — upstream github.com/Omni-Avatar/OmniAvatar (ADR-0002).
add_submodule "$OMNIAVATAR_URL" third_party/OmniAvatar

# MultiTalk deferred (ADR-0004); restore when reintroduced:
# add_submodule "$MULTITALK_URL" third_party/MultiTalk

# After adding, pin to the reviewed commit and record it in
# docs/adr/0002-third-party-submodules.md:
git submodule update --init --recursive
echo "Done."
