#!/usr/bin/env bash
#
# Bump a third_party/ submodule pin to a reviewed upstream commit/tag.
#
# Policy (ADR-0002, option A — pinned + manual bump): upstream model repos are
# never forked and never auto-updated. We follow official updates deliberately:
# move the pin to a chosen ref, REVIEW the diff, RE-BENCHMARK, then commit the
# new gitlink. This script automates the mechanical part and prints the review
# checklist — it does NOT commit for you.
#
# Runs in a GitHub-reachable environment (RunPod / local dev), since this
# Claude session's git is routed to a repo-scoped proxy.
#
# Usage:
#   scripts/bump_submodule.sh third_party/OmniAvatar <git-ref>
#   scripts/bump_submodule.sh third_party/OmniAvatar v1.2.0
#   scripts/bump_submodule.sh third_party/OmniAvatar origin/main   # tip of main
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <submodule-path> <git-ref>" >&2
  exit 2
fi

SUB_PATH="$1"
TARGET_REF="$2"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -e "$SUB_PATH/.git" ]; then
  echo "error: '$SUB_PATH' is not an initialized submodule." >&2
  echo "       run scripts/init_submodules.sh first." >&2
  exit 1
fi

echo "== Bumping submodule: $SUB_PATH -> $TARGET_REF =="
OLD_COMMIT="$(git -C "$SUB_PATH" rev-parse HEAD)"

git -C "$SUB_PATH" fetch --tags origin
git -C "$SUB_PATH" checkout --quiet "$TARGET_REF"
NEW_COMMIT="$(git -C "$SUB_PATH" rev-parse HEAD)"

if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
  echo "No change: already at $NEW_COMMIT"
  exit 0
fi

echo
echo "  old: $OLD_COMMIT"
echo "  new: $NEW_COMMIT"
echo
echo "== Upstream changes in range =="
git -C "$SUB_PATH" --no-pager log --oneline "$OLD_COMMIT..$NEW_COMMIT" | head -50 || true

cat <<EOF

== Review checklist before committing (ADR-0002) ==
  [ ] Review the upstream diff above for breaking changes / new requirements.
  [ ] Update providers/ adapter if the upstream inference API changed.
  [ ] Re-run a benchmark and compare against the previous pin (quality first, §18).
  [ ] Record the new pinned commit in docs/adr/0002-third-party-submodules.md.

When satisfied, commit the new gitlink:
  git add $SUB_PATH docs/adr/0002-third-party-submodules.md
  git commit -m "Bump $SUB_PATH to ${TARGET_REF} (${NEW_COMMIT:0:12})"
EOF
