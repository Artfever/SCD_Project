#!/usr/bin/env bash
# Usage: load_images.sh <tag>. Copies built images into minikube.
set -euo pipefail
cd "$(dirname "$0")/.."

tag=${1:?usage: load_images.sh <tag>}
profile=${MINIKUBE_PROFILE:-scd-project}
for f in services/*/Dockerfile; do
  service=$(basename "$(dirname "$f")")
  echo "== load scd/${service}:${tag}"
  minikube -p "$profile" image load "scd/${service}:${tag}"
done
