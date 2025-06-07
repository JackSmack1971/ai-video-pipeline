import asyncio
from pathlib import Path
from typing import Any, Dict

import pytest

from pipeline import ContentPipeline
from config import Config


class DummyIdea:
    async def generate(self) -> Dict[str, str]:
        return {"idea": "test", "prompt": "do it"}


class DummyImage:
    async def generate(self, prompt: str) -> str:
        return "image.png"


class DummyVideo:
    async def generate(self, image_path: str, prompt: str) -> str:
        return "video.mp4"


class DummyMusic:
    async def generate(self, prompt: str) -> str:
        return "music.mp3"


class DummyVoice:
    async def generate(self, idea: str) -> Dict[str, str]:
        return {"filename": "voice.mp3"}


@pytest.mark.asyncio
async def test_pipeline_run_single(monkeypatch):
    cfg = Config("sk", "sa", "rep", 1)
    services: Dict[str, Any] = {
        "idea_generator": DummyIdea(),
        "image_generator": DummyImage(),
        "video_generator": DummyVideo(),
        "music_generator": DummyMusic(),
        "voice_generator": DummyVoice(),
    }

    async def fake_merge(video, music, voice, out):
        return "final.mp4"

    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)

    pipe = ContentPipeline(cfg, services)
    result = await pipe.run_single_video()
    assert result["video"] == "final.mp4"


@pytest.mark.asyncio
async def test_pipeline_music_only(monkeypatch):
    cfg = Config("sk", "sa", "rep", 1)
    services: Dict[str, Any] = {
        "idea_generator": DummyIdea(),
        "image_generator": DummyImage(),
        "video_generator": DummyVideo(),
        "music_generator": DummyMusic(),
    }
    pipe = ContentPipeline(cfg, services)
    result = await pipe.run_music_only("prompt")
    assert result == {"music": "music.mp3"}


@pytest.mark.asyncio
async def test_pipeline_run_multiple(monkeypatch):
    cfg = Config("sk", "sa", "rep", 1)
    services: Dict[str, Any] = {
        "idea_generator": DummyIdea(),
        "image_generator": DummyImage(),
        "video_generator": DummyVideo(),
        "music_generator": DummyMusic(),
    }

    async def fake_merge(video, music, voice, out):
        return "final.mp4"

    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)

    pipe = ContentPipeline(cfg, services)
    result = await pipe.run_multiple_videos(2)
    assert len(result) == 2
    assert all(r["video"] == "final.mp4" for r in result)

