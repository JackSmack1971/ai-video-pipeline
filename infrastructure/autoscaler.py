from __future__ import annotations

import asyncio
from contextlib import suppress

from .task_queue import TaskQueue
from .worker_manager import WorkerManager


class Autoscaler:
    def __init__(
        self,
        queue: TaskQueue,
        manager: WorkerManager,
        min_workers: int = 1,
        max_workers: int = 10,
        threshold: int = 5,
    ) -> None:
        self.queue = queue
        self.manager = manager
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.threshold = threshold
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._monitor())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _monitor(self) -> None:
        while True:
            depth = self.queue._queue.qsize()
            count = self.manager.worker_count
            if depth > self.threshold and count < self.max_workers:
                await self.manager.scale(count + 1)
            elif depth == 0 and count > self.min_workers:
                await self.manager.scale(count - 1)
            await asyncio.sleep(1)

