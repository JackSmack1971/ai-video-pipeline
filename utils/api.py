import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

from exceptions import (
    APIError,
    NetworkError,
    CircuitBreaker,
    CircuitBreakerOpenError,
    RetryPolicy,
    get_policy,
)
from utils.monitoring import API_RESPONSE_TIME

T = TypeVar("T")


async def api_call_with_retry(
    operation_name: str,
    api_call: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    timeout: int = 60,
    service: str | None = None,
    breaker: CircuitBreaker | None = None,
) -> T:
    logger = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()
    policy: RetryPolicy = get_policy(service) if service else RetryPolicy(max_retries, timeout * max_retries)
    start_total = loop.time()
    attempts = 0
    while attempts < policy.max_attempts and loop.time() - start_total < policy.max_time:
        start = loop.time()
        try:
            call = api_call if breaker is None else (lambda: breaker.call(api_call))
            result = await asyncio.wait_for(call(), timeout=timeout)
            API_RESPONSE_TIME.labels(operation=operation_name).observe(loop.time() - start)
            return result
        except CircuitBreakerOpenError as exc:
            raise APIError(f"{operation_name} unavailable") from exc
        except asyncio.TimeoutError as exc:
            logger.warning("%s timeout", operation_name, extra={"attempt": attempts + 1})
            if attempts == policy.max_attempts - 1:
                raise NetworkError(f"{operation_name} timed out") from exc
        except Exception as exc:
            logger.warning("%s failed: %s", operation_name, exc, extra={"attempt": attempts + 1})
            if attempts == policy.max_attempts - 1:
                raise APIError(f"{operation_name} failed: {exc}") from exc
        attempts += 1
        await asyncio.sleep((2 ** attempts) + random.random())
    raise APIError(f"{operation_name} failed after retries")
