"""The raw item a scout produces, and the cleaning applied before it is stored."""

import html
import re
from datetime import UTC, date, datetime

from pydantic import BaseModel, Field

MAX_TEXT = 2000
TAGS = re.compile(r"<[^>]+>")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<![\w.])\+\d[\d ()-]{8,}\d")


def clean(text: str | None) -> str:
    """Plain text without markup or contact details."""
    plain = TAGS.sub(" ", html.unescape(text or ""))
    plain = PHONE.sub("[phone]", EMAIL.sub("[email]", plain))
    return " ".join(plain.split())[:MAX_TEXT]


class RawItem(BaseModel):
    """Only what an idea card needs. Author names are deliberately not collected."""

    source: str
    external_id: str
    title: str = Field(min_length=1)
    summary: str = ""
    text: str = ""
    url: str
    published_at: date
    points: int = 0
    tags: list[str] = []
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
