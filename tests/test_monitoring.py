import asyncio
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from config import Config
from pipeline import ContentPipeline
from utils.monitoring import PIPELINE_SUCCESS, PIPELINE_FAILURE


class DummyIdea:
    async def generate(self):
        return {"idea": "x", "prompt": "x"}


class DummyGen:
    async def generate(self, *args, **kwargs):
        return "x"


@pytest.mark.asyncio
async def test_pipeline_metrics(monkeypatch):
    cfg = Config("k1", "k2", "k3", 60)
    services = {
        "idea_generator": DummyIdea(),
        "image_generator": DummyGen(),
        "video_generator": DummyGen(),
        "music_generator": DummyGen(),
    }
    async def fake_merge(*a, **k):
        return "out.mp4"
    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)
    start_success = PIPELINE_SUCCESS._value.get()
    pipe = ContentPipeline(cfg, services)
    await pipe.run_single_video()
    assert PIPELINE_SUCCESS._value.get() == start_success + 1
    assert PIPELINE_FAILURE._value.get() == 0
