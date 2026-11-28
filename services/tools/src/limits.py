"""Per-domain rate limit and a small response cache."""

import asyncio
import time
from collections import OrderedDict, defaultdict
from collections.abc import Awaitable, Callable, Mapping

Clock = Callable[[], float]
Sleep = Callable[[float], Awaitable[None]]


class RateLimiter:
    """Keeps a minimum interval between two requests to the same host."""

    def __init__(
        self,
        intervals: Mapping[str, float],
        clock: Clock = time.monotonic,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._intervals = intervals
        self._clock = clock
        self._sleep = sleep
        self._next: dict[str, float] = {}
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def wait(self, host: str) -> None:
        async with self._locks[host]:
            delay = self._next.get(host, 0.0) - self._clock()
            if delay > 0:
                await self._sleep(delay)
            self._next[host] = self._clock() + self._intervals.get(host, 1.0)


class TTLCache[Value]:
    """Least recently used cache whose entries expire."""

    def __init__(self, ttl: float, max_entries: int, clock: Clock = time.monotonic) -> None:
        self._ttl = ttl
        self._max = max_entries
        self._clock = clock
        self._items: OrderedDict[str, tuple[float, Value]] = OrderedDict()

    def get(self, key: str) -> Value | None:
        item = self._items.get(key)
        if item is None:
            return None
        if item[0] <= self._clock():
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return item[1]

    def put(self, key: str, value: Value) -> None:
        self._items[key] = (self._clock() + self._ttl, value)
        self._items.move_to_end(key)
        while len(self._items) > self._max:
            self._items.popitem(last=False)
