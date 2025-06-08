from __future__ import annotations

import time
from typing import Awaitable, Callable, TypeVar

from exceptions import CircuitBreakerOpenError

T = TypeVar("T")


class CircuitBreaker:
    def __init__(self, max_failures: int = 5, reset_timeout: float = 30.0) -> None:
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.open_until = 0.0

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        now = time.time()
        if self.failures >= self.max_failures and now < self.open_until:
            raise CircuitBreakerOpenError("Circuit breaker open")
        try:
            result = await func()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.max_failures:
                self.open_until = now + self.reset_timeout
            raise
