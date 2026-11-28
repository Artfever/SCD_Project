"""One connector per source. Each turns pages of an official API into raw items."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from src.items import RawItem, clean

PER_PAGE = 100


@dataclass(frozen=True)
class Window:
    months: int  # how many months back to look
    pages: int  # page budget per month (per source for DEV.to)
    today: date


@dataclass(frozen=True)
class Page:
    url: str
    parse: Callable[[Any], list[RawItem]]
    group: str  # pages of one group stop at the first page that is not full


def month_ranges(window: Window) -> Iterator[tuple[date, date]]:
    """(first day, first day of the next month) for the last `months` months, newest first."""
    first = window.today.replace(day=1)
    for _ in range(window.months):
        following = (first + timedelta(days=32)).replace(day=1)
        yield first, following
        first = (first - timedelta(days=1)).replace(day=1)


def _epoch(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def parse_hn(document: Any) -> list[RawItem]:
    items = []
    for hit in document["hits"]:
        title = clean(hit.get("title")).removeprefix("Show HN:").strip()
        if not title:
            continue
        discussion = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        text = clean(hit.get("story_text"))
        items.append(
            RawItem(
                source="hackernews",
                external_id=str(hit["objectID"]),
                title=title,
                summary=title,
                text=text,
                url=hit.get("url") or discussion,
                published_at=hit["created_at"][:10],
                points=hit.get("points") or 0,
            )
        )
    return items


def hn_pages(window: Window) -> Iterator[Page]:
    for first, following in month_ranges(window):
        filters = f"created_at_i>={_epoch(first)},created_at_i<{_epoch(following)},points>=10"
        for page in range(window.pages):
            query = urlencode(
                {
                    "tags": "show_hn",
                    "hitsPerPage": PER_PAGE,
                    "page": page,
                    "numericFilters": filters,
                }
            )
            url = f"https://hn.algolia.com/api/v1/search_by_date?{query}"
            yield Page(url, parse_hn, f"{first}")


def parse_github(document: Any) -> list[RawItem]:
    items = []
    for repo in document["items"]:
        description = clean(repo.get("description"))
        if repo.get("fork") or not description:
            continue
        tags = list(repo.get("topics") or [])
        if repo.get("language"):
            tags.append(repo["language"].lower())
        items.append(
            RawItem(
                source="github",
                external_id=str(repo["id"]),
                title=repo["name"],
                summary=description,
                text=description,
                url=repo["html_url"],
                published_at=repo["created_at"][:10],
                points=repo.get("stargazers_count") or 0,
                tags=tags[:10],
            )
        )
    return items


def github_pages(window: Window) -> Iterator[Page]:
    for first, following in month_ranges(window):
        last = following - timedelta(days=1)
        for page in range(1, window.pages + 1):
            query = urlencode(
                {
                    "q": f"created:{first}..{last} stars:>=50",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": PER_PAGE,
                    "page": page,
                }
            )
            url = f"https://api.github.com/search/repositories?{query}"
            yield Page(url, parse_github, f"{first}")


def parse_devto(document: Any) -> list[RawItem]:
    items = []
    for article in document:
        title = clean(article.get("title"))
        if not title:
            continue
        description = clean(article.get("description"))
        items.append(
            RawItem(
                source="devto",
                external_id=str(article["id"]),
                title=title,
                summary=description or title,
                text=description,
                url=article["url"],
                published_at=article["published_at"][:10],
                points=article.get("public_reactions_count") or 0,
                tags=list(article.get("tag_list") or [])[:10],
            )
        )
    return items


def devto_pages(window: Window) -> Iterator[Page]:
    # `top` limits the listing to the most liked articles of the last N days
    days = window.months * 31
    for page in range(1, window.pages * window.months + 1):
        query = urlencode({"tag": "showdev", "top": days, "per_page": PER_PAGE, "page": page})
        yield Page(f"https://dev.to/api/articles?{query}", parse_devto, "showdev")


SOURCES: dict[str, Callable[[Window], Iterator[Page]]] = {
    "hackernews": hn_pages,
    "github": github_pages,
    "devto": devto_pages,
}
