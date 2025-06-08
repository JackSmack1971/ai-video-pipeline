import asyncio
import sys
from pathlib import Path
import pytest
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from infrastructure.task_queue import TaskQueue
from infrastructure.worker_manager import WorkerManager


class DummyRequest(BaseModel):
    value: int = 1


async def worker(job_id: str, req: DummyRequest) -> None:
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_worker_manager_executes_job():
    queue = TaskQueue()
    manager = WorkerManager(queue, worker)
    await manager.start(1)
    job = await queue.enqueue_video_generation(DummyRequest())
    await queue._queue.join()
    status = await queue.get_job_status(job)
    assert status.status == "completed"
    await manager.stop()
