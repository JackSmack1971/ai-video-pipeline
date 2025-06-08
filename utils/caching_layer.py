from __future__ import annotations

import time
from typing import Any, Dict, Tuple, Callable, Awaitable


class ResponseCache:
    def __init__(self, ttl: int = 300, max_items: int = 256) -> None:
        self.ttl = ttl
        self.max_items = max_items
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _prune(self) -> None:
        now = time.time()
        keys = [k for k, (t, _) in self._cache.items() if now - t > self.ttl]
        for k in keys:
            self._cache.pop(k, None)
        while len(self._cache) > self.max_items:
            self._cache.pop(next(iter(self._cache)))

    def get(self, key: str) -> Any | None:
        item = self._cache.get(key)
        if item and time.time() - item[0] < self.ttl:
            return item[1]
        return None

    async def get_or_set(
        self, key: str, func: Callable[[], Awaitable[Any]]
    ) -> Any:
        hit = self.get(key)
        if hit is not None:
            return hit
        value = await func()
        self._cache[key] = (time.time(), value)
        self._prune()
        return value

    def clear(self) -> None:
        self._cache.clear()
