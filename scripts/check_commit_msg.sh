#!/usr/bin/env bash
# Usage: check_commit_msg.sh <file>. Conventional title and no AI attribution.
set -euo pipefail

file=$1
ai='claude|anthropic|copilot|codex'
if grep -Eiq "^[[:space:]]*co-authored-by:.*($ai)|generated (with|by) .*($ai)|claude\.ai/code|^claude-session:" "$file"; then
  echo "Remove the AI attribution line(s)." >&2
  exit 1
fi
title=$(grep -v '^#' "$file" | head -n 1 | tr -d '\r')
if ! printf '%s' "$title" | grep -Eq '^((feat|fix|test|docs|chore|ci|build|refactor|perf|style|revert)(\([a-z0-9._-]+\))?!?: .+|Merge .+|Revert .+)'; then
  echo "Title is not a conventional commit: $title" >&2
  echo "Example: feat(verdict): add duplicate gate" >&2
  exit 1
fi
