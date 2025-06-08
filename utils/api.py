import asyncio
from typing import Awaitable, Callable, TypeVar

from exceptions import APIError, NetworkError
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from utils.retry_logic import retry_async
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
    async def wrapped() -> T:
        start = asyncio.get_event_loop().time()
        result = await api_call()
        API_RESPONSE_TIME.labels(operation=operation_name).observe(asyncio.get_event_loop().time() - start)
        return result

    try:
        return await retry_async(operation_name, wrapped, retries=max_retries, timeout=timeout, breaker=breaker)
    except CircuitBreakerOpenError as exc:
        raise APIError(f"{operation_name} unavailable") from exc
    except asyncio.TimeoutError as exc:
        raise NetworkError(f"{operation_name} timed out") from exc
