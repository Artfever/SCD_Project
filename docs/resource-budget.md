# Memory budget for a 24 GB laptop

Main machine: 23.7 GB usable RAM, 16 logical processors, RTX 3070 Laptop GPU (8 GB).

## Split between Windows and Linux

| Consumer | Memory | Setting |
| --- | --- | --- |
| Windows, editor, browser | about 10 GB measured with VS Code, Chrome and chat apps open | |
| WSL 2 (Docker and the cluster) | at most 12 GB | `memory=12GB` in `%USERPROFILE%\.wslconfig` |
| Spare | about 1.7 GB | |

Do not raise the WSL cap: Windows would start paging.

## Inside the 12 GB

| Part | Cap | Enforced by |
| --- | --- | --- |
| minikube node `scd-project` | 7 GB | container limit set by `scripts/lab.ps1` |
| Jenkins (issue #5) | 1.5 GB | container limit and JVM heap of 768 MB |
| Docker engine and image builds | about 3.5 GB | what is left |

## Run one mode at a time

| Mode | Command | Running | Upper bound in WSL |
| --- | --- | --- | --- |
| Develop | `.\scripts\lab.ps1 dev` | Postgres and Redis | about 0.7 GB |
| Develop, all services | `docker compose --profile app up --build` | Everything in Compose | about 7 GB |
| Cluster | `.\scripts\lab.ps1 cluster` | Full deployment | 7 GB |
| Delivery | cluster plus Jenkins | | 8.5 GB |
| Off | `.\scripts\lab.ps1 stop` | Nothing | quit Docker Desktop to release memory |

Never run the Compose application and the cluster together.

Models:

- During development Ollama runs on Windows and uses the GPU, so it costs little system RAM.
  Unload large models before running the cluster and Jenkins.
- In the cluster the scoring model runs quantised on CPU (decision record 0002).
- Train on Colab or Kaggle as the guide says, not while the cluster is running.

## Kubernetes budget

Starting estimates. Replace them with `kubectl top` measurements under load (issue #31).

| Workload | Request | Limit |
| --- | --- | --- |
| scorer (model) | 1792 Mi | 2304 Mi |
| kb | 768 Mi | 1280 Mi |
| analyst | 256 Mi | 768 Mi |
| postgres (with pgvector) | 256 Mi | 512 Mi |
| agentops | 192 Mi | 384 Mi |
| validators | 160 Mi | 320 Mi |
| orchestrator, ideation, critic (each) | 128 Mi | 256 Mi |
| gateway, profile, scouts, tools (each) | 96 Mi | 192 Mi |
| verdict (2 replicas, each) | 64 Mi | 128 Mi |
| redis | 64 Mi | 128 Mi |
| ui | 24 Mi | 64 Mi |
| **Total** | **4408 Mi** | **7552 Mi** |

The namespace quota (`k8s/base/quota.yaml`) allows 7 Gi of requests and 11 Gi of limits, which
leaves room for rolling updates, jobs and autoscaling. Limits can add up to more than the node
holds, so watch real usage.

## Measured with the skeleton (2026-11-28)

| Item | Memory |
| --- | --- |
| Each Python service | about 35 MiB |
| ui, postgres, redis | 6, 33 and 3 MiB |
| Kubernetes system, Calico, ingress, metrics | about 1.7 GiB |
| Whole node | 2.25 GiB of 7 GiB |

At the requested amounts the node would use about 6 GiB, so the scorer and knowledge base are the
two to watch.

## Teammate machine

To be filled in by `TahaSohail-Goat` (issue #2): RAM, operating system, GPU.
