#!/usr/bin/env bash
# Usage: build_images.sh <tag> [service ...]
set -euo pipefail
cd "$(dirname "$0")/.."

tag=${1:?usage: build_images.sh <tag> [service ...]}
shift
if [ "$#" -eq 0 ]; then
  set -- $(for f in services/*/Dockerfile jobs/*/Dockerfile; do basename "$(dirname "$f")"; done)
fi
for name in "$@"; do
  dir="services/${name}"
  [ -d "$dir" ] || dir="jobs/${name}"
  echo "== build scd/${name}:${tag}"
  docker build --quiet -t "scd/${name}:${tag}" "$dir"
done
