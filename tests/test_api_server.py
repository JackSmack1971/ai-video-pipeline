import asyncio
from pathlib import Path as _Path
import sys

sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from ai_video_pipeline import api_app


@pytest.fixture(autouse=True)
def patch_queue_and_auth(monkeypatch):
    async def fake_enqueue(req):
        job_id = "test_job"
        api_app.queue._jobs[job_id] = api_app.JobStatus("completed")
        return job_id

    async def fake_status(job_id: str):
        return api_app.queue._jobs[job_id]

    monkeypatch.setattr(api_app.queue, "enqueue_video_generation", fake_enqueue)
    monkeypatch.setattr(api_app.queue, "get_job_status", fake_status)

    from security.auth_manager import User

    test_user = User(id="tester", roles=["admin"])

    async def fake_authenticate_api_key(api_key: str):
        return test_user

    async def fake_validate_token(token: str):
        return test_user

    monkeypatch.setattr(api_app.auth, "authenticate_api_key", fake_authenticate_api_key)
    monkeypatch.setattr(api_app.auth, "validate_token", fake_validate_token)


def test_generate_and_status(monkeypatch):
    client = TestClient(api_app.app)
    headers = {"Authorization": "Bearer test"}
    resp = client.post('/generate', json={}, headers=headers)
    assert resp.status_code == 200
    job = resp.json()['job_id']
    status = client.get(f'/status/{job}', headers=headers)
    assert status.json()['status'] == 'completed'
