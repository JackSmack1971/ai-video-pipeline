import asyncio
from typing import Callable, TypeVar, Awaitable

from exceptions import APIError, NetworkError

T = TypeVar("T")


async def api_call_with_retry(operation_name: str, api_call: Callable[[], Awaitable[T]], max_retries: int = 3, timeout: int = 60) -> T:
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(api_call(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            if attempt == max_retries - 1:
                raise NetworkError(f"{operation_name} timed out") from exc
        except Exception as exc:
            if attempt == max_retries - 1:
                raise APIError(f"{operation_name} failed: {exc}") from exc
        await asyncio.sleep(2 ** attempt)
