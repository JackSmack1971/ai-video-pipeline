from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import List

import psutil

from .resource_tracker import ResourceTracker, ResourceSnapshot
from exceptions import ServiceError


@dataclass
class MemoryLeak:
    pid: int
    mem_mb: float


@dataclass
class PerformanceReport:
    cpu: float
    memory: float
    disk_write: float
    net_sent: float


class ApplicationProfiler:
    def __init__(self, tracker: ResourceTracker | None = None, interval: float = 1.0) -> None:
        self.tracker = tracker or ResourceTracker()
        self.interval = interval
        self._task: asyncio.Task | None = None

    async def profile_pipeline_execution(self, pipeline_id: str) -> None:
        async def _collect() -> None:
            while True:
                await self.profile_service_calls(pipeline_id)
                await asyncio.sleep(self.interval)
        if not self._task or self._task.done():
            self._task = asyncio.create_task(_collect())

    async def profile_service_calls(self, service: str) -> ResourceSnapshot:
        try:
            return await self.tracker.collect_once()
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"profiling failed for {service}: {exc}") from exc

    async def generate_performance_report(self) -> PerformanceReport:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        avg = await self.tracker.average_usage()
        return PerformanceReport(avg.cpu, avg.memory, avg.disk_write, avg.net_sent)

    async def detect_memory_leaks(self) -> List[MemoryLeak]:
        leaks: List[MemoryLeak] = []
        for proc in psutil.process_iter():
            try:
                mem = proc.memory_info().rss / (1024 * 1024)
                if mem > 100:
                    leaks.append(MemoryLeak(proc.pid, mem))
            except Exception:
                continue
        return leaks
