from __future__ import annotations

import psutil
import time
from typing import Dict, List


def get_memory_usage() -> float:
    """Return process RSS memory usage in MB."""
    return psutil.Process().memory_info().rss / (1024 * 1024)


async def sample_resources(samples: List[Dict[str, float]]) -> None:
    """Record a single CPU and memory sample."""
    mem = get_memory_usage()
    cpu = psutil.cpu_percent(interval=None)
    samples.append({"timestamp": time.time(), "cpu": cpu, "memory": mem})
