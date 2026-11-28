# 0003. Show metrics on our own page instead of Prometheus and Grafana

- **Status:** Proposed
- **Context:** M13 needs a dashboard. Both options are allowed by the guide.
- **Options:** (1) Prometheus and Grafana, (2) a page reading /metrics.
- **Decision:** A page reading /metrics.
- **Why:** Saves two containers and their memory.
- **Cost:** No long-term history or ready-made charts.
- **AI use:** Drafted by Claude Code. Options and numbers still to be checked by both members.
