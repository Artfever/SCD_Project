#!/usr/bin/env bash
# Run the pull request checks that need no Docker.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python}
"$PYTHON" -m ruff check .
"$PYTHON" -m ruff format --check .
bash scripts/typecheck.sh
bash scripts/test.sh
bash scripts/check_files.sh
if command -v kubeconform >/dev/null; then
  kubectl kustomize k8s/base | kubeconform -strict -summary
else
  echo "kubeconform not on PATH: manifest validation skipped"
fi
