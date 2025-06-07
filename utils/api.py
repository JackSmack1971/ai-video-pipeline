import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

from exceptions import APIError, NetworkError
from utils.monitoring import API_RESPONSE_TIME

T = TypeVar("T")


async def api_call_with_retry(operation_name: str, api_call: Callable[[], Awaitable[T]], max_retries: int = 3, timeout: int = 60) -> T:
    logger = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()
    for attempt in range(max_retries):
        start = loop.time()
        try:
            result = await asyncio.wait_for(api_call(), timeout=timeout)
            API_RESPONSE_TIME.labels(operation=operation_name).observe(loop.time() - start)
            return result
        except asyncio.TimeoutError as exc:
            logger.warning("%s timeout", operation_name, extra={"attempt": attempt + 1})
            if attempt == max_retries - 1:
                raise NetworkError(f"{operation_name} timed out") from exc
        except Exception as exc:
            logger.warning("%s failed: %s", operation_name, exc, extra={"attempt": attempt + 1})
            if attempt == max_retries - 1:
                raise APIError(f"{operation_name} failed: {exc}") from exc
        await asyncio.sleep(2 ** attempt)
