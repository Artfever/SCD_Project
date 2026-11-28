# 0002. Serve the scoring model quantised on CPU

- **Status:** Proposed
- **Context:** M10 must run in its own container on Kubernetes. The local cluster has no GPU access.
- **Options:** (1) GGUF on CPU with llama.cpp, (2) GPU pass-through to minikube, (3) Ollama on the host.
- **Decision:** A 1B to 3B model, GGUF 4-bit, on CPU in the cluster.
- **Why:** Keeps the whole system on Kubernetes with predictable memory.
- **Cost:** Slower scoring. Memory and latency still to be measured.
- **AI use:** Drafted by Claude Code. Options and numbers still to be checked by both members.
