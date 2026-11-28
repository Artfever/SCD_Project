#!/usr/bin/env bash
# Run the tests of every Python service, one process per service.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=${PYTHON:-python}
for dir in services/*/ jobs/*/; do
  [ -d "${dir}tests" ] || continue
  echo "== pytest ${dir}"
  (cd "$dir" && "$PYTHON" -m pytest tests)
done
