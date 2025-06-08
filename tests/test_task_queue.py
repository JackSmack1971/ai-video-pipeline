import sys
from pathlib import Path
import pytest
import pytest_asyncio
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from infrastructure.task_queue import TaskQueue


class DummyRequest(BaseModel):
    pass


@pytest.mark.asyncio
async def test_enqueue_status_cancel():
    queue = TaskQueue()
    job_id = await queue.enqueue_video_generation(DummyRequest())
    status = await queue.get_job_status(job_id)
    assert status.status == "queued"
    cancelled = await queue.cancel_job(job_id)
    assert cancelled
    status = await queue.get_job_status(job_id)
    assert status.status == "cancelled"
