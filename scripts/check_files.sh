#!/usr/bin/env bash
# Fail if a file that must stay local is tracked.
set -euo pipefail
cd "$(dirname "$0")/.."

bad=$(git ls-files | grep -Ei '(^|/)(Project|Project_Guide)\.pdf$|(^|/)\.env(\.[^/]*)?$|\.(gguf|safetensors|pem|key)$|(^|/)kubeconfig' | grep -v '\.env\.example$' || true)
if [ -n "$bad" ]; then
  echo "These files must not be committed:" >&2
  echo "$bad" >&2
  exit 1
fi
