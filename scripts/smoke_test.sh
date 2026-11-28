#!/usr/bin/env bash
# Calls /ready on every service from inside the cluster.
set -euo pipefail
cd "$(dirname "$0")/.."

context=${KUBE_CONTEXT:-scd-project}
ns=idea-validator
targets=""
for f in services/*/Dockerfile; do
  service=$(basename "$(dirname "$f")")
  port=8000
  [ "$service" = ui ] && port=8080
  targets="$targets $service:$port"
done
kubectl --context "$context" -n "$ns" exec deploy/gateway -- python -c '
import socket, sys, urllib.request
failed = 0
for target in sys.argv[1:]:
    try:
        urllib.request.urlopen(f"http://{target}/ready", timeout=5).read()
        print("ok  ", target)
    except Exception as error:
        failed += 1
        print("FAIL", target, error)
for host, port in (("postgres", 5432), ("redis", 6379)):
    try:
        socket.create_connection((host, port), 5).close()
        print("ok  ", f"{host}:{port}")
    except OSError as error:
        failed += 1
        print("FAIL", host, error)
sys.exit(1 if failed else 0)
' $targets
