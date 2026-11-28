#!/usr/bin/env bash
# Usage: build_images.sh <tag> [service ...]
set -euo pipefail
cd "$(dirname "$0")/.."

tag=${1:?usage: build_images.sh <tag> [service ...]}
shift
if [ "$#" -eq 0 ]; then
  set -- $(for f in services/*/Dockerfile; do basename "$(dirname "$f")"; done)
fi
for service in "$@"; do
  echo "== build scd/${service}:${tag}"
  docker build --quiet -t "scd/${service}:${tag}" "services/${service}"
done
