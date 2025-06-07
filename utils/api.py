import asyncio
from typing import Callable, TypeVar

from ..exceptions import NetworkError

T = TypeVar("T")


async def api_call_with_retry(operation_name: str, api_call: Callable[[], T], max_retries: int = 3, timeout: int = 60) -> T:
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(api_call(), timeout=timeout)
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise NetworkError(f"{operation_name} failed after {max_retries} attempts")
            await asyncio.sleep(2 ** attempt)
