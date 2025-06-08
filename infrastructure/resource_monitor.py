from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Dict


def _get_cpu_usage() -> float:
    try:
        load1, _, _ = os.getloadavg()
        return load1
    except OSError:
        return 0.0


def _get_memory_usage() -> float:
    try:
        with open('/proc/meminfo') as fh:
            meminfo = {line.split(':')[0]: int(line.split()[1]) for line in fh}
        used = meminfo['MemTotal'] - meminfo['MemAvailable']
        return used / meminfo['MemTotal'] * 100
    except Exception:
        return 0.0


@dataclass
class ResourceStats:
    cpu: float
    memory: float


class ResourceMonitor:
    async def get_stats(self) -> ResourceStats:
        loop = asyncio.get_event_loop()
        cpu, mem = await asyncio.gather(
            loop.run_in_executor(None, _get_cpu_usage),
            loop.run_in_executor(None, _get_memory_usage),
        )
        return ResourceStats(cpu=cpu, memory=mem)
