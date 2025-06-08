import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest

from config import Config
from pipeline import ContentPipeline


class SleepService:
    async def generate(self, *args, **kwargs):
        await asyncio.sleep(0.05)
        return "x"


class DummyIdea:
    async def generate(self):
        return {"idea": "x", "prompt": "x"}


@pytest.mark.asyncio
async def test_pipeline_concurrent_speed(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Config("sk", "sa", "rep", 60)
    services = {
        "idea_generator": DummyIdea(),
        "image_generator": SleepService(),
        "video_generator": SleepService(),
        "music_generator": SleepService(),
    }
    async def fake_merge(*a, **k):
        return "out.mp4"
    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)
    pipe = ContentPipeline(cfg, services)
    start = asyncio.get_event_loop().time()
    await pipe.run_multiple_videos(3)
    duration = asyncio.get_event_loop().time() - start
    assert duration < 0.6

