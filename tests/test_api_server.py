import asyncio
from pathlib import Path as _Path
import sys

sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from ai_video_pipeline import api_app


@pytest.fixture(autouse=True)
def patch_run(monkeypatch):
    async def fake_run(job_id, req):
        api_app._jobs[job_id]["status"] = "completed"
    monkeypatch.setattr(api_app, '_run_job', fake_run)


def test_generate_and_status(monkeypatch):
    client = TestClient(api_app.app)
    resp = client.post('/generate', json={})
    assert resp.status_code == 200
    job = resp.json()['job_id']
    status = client.get(f'/status/{job}')
    assert status.json()['status'] == 'completed'
