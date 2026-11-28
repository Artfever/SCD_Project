#!/usr/bin/env bash
# Usage: deploy.sh <tag>
set -euo pipefail
cd "$(dirname "$0")/.."

tag=${1:?usage: deploy.sh <tag>}
context=${KUBE_CONTEXT:-scd-project}
ns=idea-validator
k() { kubectl --context "$context" "$@"; }

k create namespace "$ns" --dry-run=client -o yaml | k apply -f -
# The database password is generated once, kept in the cluster and never written to the repository
if ! k -n "$ns" get secret postgres-auth >/dev/null 2>&1; then
  k -n "$ns" create secret generic postgres-auth --from-literal=password="$(openssl rand -hex 24)"
fi
kubectl kustomize k8s/base \
  | sed -E "s#(image: scd/[a-z0-9-]+):dev#\1:${tag}#" \
  | k apply -f -
k -n "$ns" rollout status statefulset/postgres --timeout=300s
for deployment in $(k -n "$ns" get deployments -o name); do
  k -n "$ns" rollout status "$deployment" --timeout=300s
done
