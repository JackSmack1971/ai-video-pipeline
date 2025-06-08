from __future__ import annotations

import random
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator


@asynccontextmanager
async def simulated_service_failures(cfg: dict) -> AsyncIterator[None]:
    """Randomly raise RuntimeError based on failure_rate."""
    rate = cfg.get("failure_rate", 0)
    if random.random() < rate:
        raise RuntimeError(f"{cfg.get('service', 'service')} failure")
    try:
        yield
    finally:
        return


@contextmanager
def simulated_low_disk_space(_: int) -> Iterator[None]:
    """Context manager placeholder for disk exhaustion."""
    yield
