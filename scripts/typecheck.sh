#!/usr/bin/env bash
# Type check every Python service.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python}
for dir in services/*/; do
  [ -d "${dir}src" ] || continue
  echo "== mypy ${dir}"
  (cd "$dir" && "$PYTHON" -m mypy --config-file ../../pyproject.toml src tests)
done
