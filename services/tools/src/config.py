"""Settings of the tool layer, read from environment variables (ConfigMap on Kubernetes)."""

from collections.abc import Mapping
from dataclasses import dataclass

USER_AGENT = "scd-idea-validator/0.1 (student project; +https://github.com/Artfever/SCD_Project)"

# host=minimum seconds between two requests. The hosts listed here are the allow-list.
DEFAULT_DOMAINS = "api.github.com=6.5,hn.algolia.com=1.0,dev.to=3.5"


@dataclass(frozen=True)
class Settings:
    intervals: Mapping[str, float]
    cache_ttl: float = 3600.0
    cache_entries: int = 128
    max_bytes: int = 5_000_000
    timeout: float = 20.0
    max_attempts: int = 3
    max_wait: float = 70.0
    github_token: str | None = None


def parse_domains(value: str) -> dict[str, float]:
    domains: dict[str, float] = {}
    for item in value.split(","):
        host, _, interval = item.strip().partition("=")
        if host:
            domains[host.lower()] = float(interval or 1.0)
    return domains


def load_settings(env: Mapping[str, str]) -> Settings:
    return Settings(
        intervals=parse_domains(env.get("ALLOWED_DOMAINS", DEFAULT_DOMAINS)),
        cache_ttl=float(env.get("CACHE_TTL_SECONDS", "3600")),
        github_token=env.get("GITHUB_TOKEN") or None,
    )
