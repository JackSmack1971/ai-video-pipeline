from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Tuple
from uuid import uuid4

from pydantic import BaseModel


@dataclass
class JobStatus:
    status: str
    progress: int = 0
    error: str | None = None
    result: dict | None = None


class TaskQueue:
    """Simple in-memory task queue for video generation jobs."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Tuple[str, BaseModel]] = asyncio.Queue()
        self._jobs: Dict[str, JobStatus] = {}

    async def enqueue_video_generation(self, request: BaseModel) -> str:
        job_id = uuid4().hex
        self._jobs[job_id] = JobStatus("queued")
        await self._queue.put((job_id, request))
        return job_id

    async def get_job_status(self, job_id: str) -> JobStatus:
        return self._jobs[job_id]

    async def cancel_job(self, job_id: str) -> bool:
        status = self._jobs.get(job_id)
        if not status or status.status not in {"queued", "running"}:
            return False
        status.status = "cancelled"
        return True

    async def get_task(self) -> Tuple[str, BaseModel]:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()
