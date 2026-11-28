# 0004. Use minikube with Calico

- **Status:** Accepted by Artfever, awaiting TahaSohail-Goat
- **Context:** The local cluster must enforce NetworkPolicy.
- **Options:** (1) minikube with Calico, (2) kind, (3) k3d.
- **Decision:** minikube, Docker driver, Calico.
- **Why:** scripts/netpol_test.sh passed on 2026-11-28: only the tool layer reached the internet.
- **Cost:** About 1.7 GiB of memory for the system components.
- **AI use:** Drafted by Claude Code. Options and numbers still to be checked by both members.
