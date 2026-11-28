"""robots.txt matching as described in RFC 9309, including the * and $ wildcards.

The standard library parser treats wildcards literally, which gives wrong answers for real files.
"""

import re

Rule = tuple[bool, str]

ALLOW_ALL: list[Rule] = []
DENY_ALL: list[Rule] = [(False, "/")]


def parse(text: str, agent: str) -> list[Rule]:
    """Return the rules of the group that names `agent`, else the rules of the `*` group."""
    groups: dict[str, list[Rule]] = {}
    names: list[str] = []
    in_rules = False
    for line in text.splitlines():
        key, separator, value = line.split("#", 1)[0].partition(":")
        if not separator:
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if in_rules:
                names, in_rules = [], False
            names.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif key in ("allow", "disallow"):
            in_rules = True
            if value:
                for name in names:
                    groups[name].append((key == "allow", value))
    for name, rules in groups.items():
        if name != "*" and name in agent.lower():
            return rules
    return groups.get("*", [])


def _matches(pattern: str, path: str) -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    expression = ".*".join(re.escape(part) for part in body.split("*"))
    return re.match(expression + ("$" if anchored else ""), path) is not None


def is_allowed(rules: list[Rule], path: str) -> bool:
    """The longest matching rule wins; Allow wins a tie; no match means allowed."""
    best: tuple[int, bool] | None = None
    for allow, pattern in rules:
        if _matches(pattern, path):
            candidate = (len(pattern), allow)
            if best is None or candidate > best:
                best = candidate
    return True if best is None else best[1]
