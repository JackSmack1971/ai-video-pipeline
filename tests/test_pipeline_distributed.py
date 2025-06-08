from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from pipeline import ContentPipeline
from config import Config
from services.container import Container


class DummyIdea:
    async def generate(self):
        return {"idea": "x", "prompt": "p"}


class DummyImage:
    async def generate(self, prompt: str):
        return "img.png"


class DummyVideo:
    async def generate(self, prompt: str, **kwargs):
        return "vid.mp4"


class DummyMusic:
    async def generate(self, prompt: str):
        return "music.mp3"


@pytest.mark.asyncio
async def test_run_multiple_videos_distributed(monkeypatch):
    cfg = Config("sk", "sa", "rep", 60)
    container = Container()
    container.register_singleton("idea_generator", lambda: DummyIdea())
    container.register_singleton("image_generator", lambda: DummyImage())
    container.register_singleton("video_generator", lambda: DummyVideo())
    container.register_singleton("music_generator", lambda: DummyMusic())
    pipeline = ContentPipeline(cfg, container)

    async def fake_merge(*args, **kwargs):
        return "f.mp4"

    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)

    result = await pipeline.run_multiple_videos_distributed(4, workers=2)
    assert len(result) == 4
