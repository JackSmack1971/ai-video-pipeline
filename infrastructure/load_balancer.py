from __future__ import annotations

import asyncio
from itertools import cycle
from typing import Iterable


class LoadBalancer:
    """Round-robin load balancer for API endpoints."""

    def __init__(self, endpoints: Iterable[str]) -> None:
        self._endpoints = cycle(endpoints)
        self._lock = asyncio.Lock()

    async def get_endpoint(self) -> str:
        async with self._lock:
            return next(self._endpoints)

