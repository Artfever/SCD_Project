#!/usr/bin/env bash
# Usage: check_commits.sh <base> <head>. Checks every non-merge commit in the range.
set -euo pipefail
cd "$(dirname "$0")/.."

ai='claude|anthropic|copilot|codex'
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
for sha in $(git rev-list --no-merges "$1..$2"); do
  echo "== $(git log -1 --format='%h %s' "$sha")"
  if git log -1 --format='%an %ae %cn %ce' "$sha" | grep -Eiq "$ai"; then
    echo "Commit $sha has an AI identity as author or committer." >&2
    exit 1
  fi
  git log -1 --format=%B "$sha" > "$tmp"
  bash scripts/check_commit_msg.sh "$tmp"
done
