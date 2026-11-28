"""Which URLs may be requested at all."""

from collections.abc import Container
from urllib.parse import urlsplit


class PolicyError(Exception):
    """The request breaks a rule of the tool layer."""


def check_url(url: str, allowed_hosts: Container[str]) -> str:
    """Return the host of an allowed URL, or raise PolicyError."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as error:
        raise PolicyError("malformed URL") from error
    if parts.scheme != "https":
        raise PolicyError("only https is allowed")
    if parts.username is not None or parts.password is not None:
        raise PolicyError("credentials in URLs are not allowed")
    if "\\" in url:
        raise PolicyError("malformed URL")
    host = (parts.hostname or "").lower()
    if host not in allowed_hosts:
        raise PolicyError(f"domain is not on the allow-list: {host or '(none)'}")
    if port not in (None, 443):
        raise PolicyError("only port 443 is allowed")
    return host
