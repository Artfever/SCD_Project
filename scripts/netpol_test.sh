#!/usr/bin/env bash
# Proves that only the tool layer (M5) can reach the internet.
set -euo pipefail
cd "$(dirname "$0")/.."

context=${KUBE_CONTEXT:-scd-project}
ns=idea-validator
target=${TARGET:-1.1.1.1}
failed=0
connect() { # <deployment> <host> <port>
  kubectl --context "$context" -n "$ns" exec "deploy/$1" -- \
    python -c 'import socket,sys; socket.create_connection((sys.argv[1], int(sys.argv[2])), 6)' "$2" "$3" >/dev/null 2>&1
}
ui_connect() { # <host> <port>
  kubectl --context "$context" -n "$ns" exec deploy/ui -- nc -z -w 6 "$1" "$2" >/dev/null 2>&1
}
expect() { # <allowed|blocked> <label> <command...>
  want=$1 label=$2
  shift 2
  if "$@"; then got=allowed; else got=blocked; fi
  if [ "$got" = "$want" ]; then echo "ok   $label: $got"; else echo "FAIL $label: $got, expected $want"; failed=1; fi
}
expect allowed "tools -> internet" connect tools "$target" 443
for service in verdict gateway scorer kb orchestrator scouts; do
  expect blocked "$service -> internet" connect "$service" "$target" 443
done
expect blocked "ui -> internet" ui_connect "$target" 443
expect allowed "ui -> gateway" ui_connect gateway 8000
expect blocked "ui -> postgres" ui_connect postgres 5432
exit $failed
