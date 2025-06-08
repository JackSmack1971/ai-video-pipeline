from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Awaitable, Callable, TypeVar

from exceptions import ServiceError
from monitoring.structured_logger import correlation_id
from monitoring.metrics_collector import MetricsCollector
from utils.circuit_breaker import CircuitBreaker

T = TypeVar("T")
collector = MetricsCollector()


async def retry_async(
    operation: str,
    func: Callable[[], Awaitable[T]],
    retries: int = 3,
    timeout: int = 60,
    breaker: CircuitBreaker | None = None,
) -> T:
    logger = logging.getLogger(operation)
    start = time.time()
    for attempt in range(1, retries + 1):
        try:
            call = func if breaker is None else (lambda: breaker.call(func))
            return await asyncio.wait_for(call(), timeout=timeout)
        except Exception as exc:
            if attempt == retries:
                cid = correlation_id.get()
                err = ServiceError(str(exc), correlation_id=cid, context={"op": operation, "attempt": attempt, "elapsed": time.time() - start})
                collector.increment_error(operation, "retry")
                logger.error("%s failed", operation, extra={"cid": cid, "attempt": attempt})
                raise err from exc
            await asyncio.sleep(min(2 ** attempt + random.random(), 60))
    raise ServiceError(f"{operation} failed", correlation_id=correlation_id.get())
