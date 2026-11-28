"""Remove text aimed at language models from fetched content.

This is a first line of defence based on patterns. It cannot catch every injection, so consumers
must still treat fetched text as data (M12).
"""

import html
import re
from typing import Any

PLACEHOLDER = "[removed: instruction-like text]"

# Zero-width, bidirectional control and tag characters used to hide text from people
INVISIBLE = re.compile(
    "[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff\U000e0000-\U000e007f]"
)
HIDDEN_BLOCKS = re.compile(r"<!--.*?-->|<(script|style)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
# Split points that keep the separators, so untouched text is rebuilt exactly
SEGMENTS = re.compile(r"((?<=[.!?])[ \t]+|\n+|</?p>)")

PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|any|"
        r"your|system)\b.{0,40}\b(instructions?|prompts?|rules|guidelines)\b",
        r"\byou are now (a|an|the|in)\b.{0,40}\b(assistant|ai|model|agent|mode|dan)\b",
        r"\b(reveal|print|repeat|show|leak|output)\b.{0,40}\b(system|developer|hidden) "
        r"(prompt|instructions)\b",
        r"<\|[a-z_]+\|>|\[/?INST\]|<<\/?SYS>>|</?(system|assistant)>",
        r"^\s*(system|assistant)\s*:",
        r"\b(rate|score|mark|grade) (this|the) (idea|project|product|startup)\b.{0,40}"
        r"\b(5|five|highest|maximum|go)\b",
        r"\b(if you are|attention) (an? )?(ai|llm|language model|assistant|agent)\b",
    )
]


def sanitise_text(text: str) -> tuple[str, int]:
    """Return the cleaned text and the number of segments removed."""
    cleaned = HIDDEN_BLOCKS.sub(" ", INVISIBLE.sub("", html.unescape(text)))
    parts = SEGMENTS.split(cleaned)
    removed = 0
    for index in range(0, len(parts), 2):
        if any(pattern.search(parts[index]) for pattern in PATTERNS):
            parts[index] = PLACEHOLDER
            removed += 1
    return "".join(parts), removed


def sanitise_json(value: Any) -> tuple[Any, int]:
    """Sanitise every string inside a decoded JSON document."""
    if isinstance(value, str):
        return sanitise_text(value)
    if isinstance(value, list):
        results = [sanitise_json(item) for item in value]
        return [item for item, _ in results], sum(count for _, count in results)
    if isinstance(value, dict):
        pairs = {key: sanitise_json(item) for key, item in value.items()}
        return (
            {key: item for key, (item, _) in pairs.items()},
            sum(count for _, count in pairs.values()),
        )
    return value, 0
