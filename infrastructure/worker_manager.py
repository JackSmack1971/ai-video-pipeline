from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Awaitable, Callable, List

from .task_queue import TaskQueue, JobStatus


class WorkerManager:
    def __init__(
        self,
        queue: TaskQueue,
        worker_fn: Callable[[str, object], Awaitable[None]],
    ) -> None:
        self.queue = queue
        self.worker_fn = worker_fn
        self.workers: List[asyncio.Task] = []

    @property
    def worker_count(self) -> int:
        return len(self.workers)

    async def start(self, count: int) -> None:
        for _ in range(count):
            self.workers.append(asyncio.create_task(self._worker_loop()))

    async def scale(self, count: int) -> None:
        diff = count - self.worker_count
        if diff > 0:
            await self.start(diff)
        else:
            for _ in range(-diff):
                task = self.workers.pop()
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    async def stop(self) -> None:
        await self.scale(0)

    async def _worker_loop(self) -> None:
        while True:
            job_id, req = await self.queue.get_task()
            status = await self.queue.get_job_status(job_id)
            if status.status == "cancelled":
                self.queue.task_done()
                continue
            status.status = "running"
            try:
                await self.worker_fn(job_id, req)
                status.status = "completed"
                status.progress = 100
            except Exception as exc:  # pragma: no cover - safety net
                status.status = "failed"
                status.error = str(exc)
            finally:
                self.queue.task_done()
