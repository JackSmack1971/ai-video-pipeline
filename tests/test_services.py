import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from pathlib import Path

import pytest
import pytest_asyncio

from config import Config
import services.image_generator as image_module
import services.video_generator as video_module
import services.music_generator as music_module
import services.voice_generator as voice_module
from services.image_generator import ImageGeneratorService
from services.video_generator import VideoGeneratorService
from services.music_generator import MusicGeneratorService
from services.voice_generator import VoiceGeneratorService
from repositories.implementations.in_memory_media_repository import InMemoryMediaRepository
from utils import file_operations
from tests import mocks


@pytest.fixture
def cfg() -> Config:
    return Config("sk", "sa", "rep", 60)


@pytest.fixture(autouse=True)
def patch_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_module, "replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr(image_module, "http_get", mocks.fake_http_get)
    monkeypatch.setattr(video_module, "replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr(video_module, "validate_file_path", lambda p, a: Path(p).resolve())
    monkeypatch.setattr(music_module, "http_post", mocks.fake_http_post)
    monkeypatch.setattr(music_module, "http_get", mocks.fake_http_get)
    monkeypatch.setattr(voice_module, "openai_chat", mocks.fake_openai_chat)
    monkeypatch.setattr(voice_module, "openai_speech", mocks.fake_openai_speech)
    monkeypatch.setattr("utils.validation.validate_file_path", lambda p, a: Path(p).resolve())


@pytest_asyncio.fixture(autouse=True)
async def patch_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def fake_speech(text: str, voice: str, instructions: str, config: Config):
        class S:
            def stream_to_file(self, filename: str) -> None:
                f = tmp_path / filename
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(b"v")

        return S()
    monkeypatch.setattr(voice_module, "openai_speech", fake_speech)
    async def empty_stream():
        if False:
            yield b""
    async def read_file(_: str) -> str:
        return ""
    monkeypatch.setattr(file_operations, "read_file", read_file)
    monkeypatch.setattr(file_operations, "read_file_stream", lambda *a, **k: empty_stream())
    monkeypatch.setattr(file_operations, "BASE_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    yield


def test_generate_image(cfg: Config) -> None:
    repo = InMemoryMediaRepository()
    svc = ImageGeneratorService(cfg, repo)
    result = asyncio.run(svc.generate("prompt"))
    assert result.startswith("image/")


def test_generate_video(cfg: Config, tmp_path: Path) -> None:
    img = tmp_path / "image" / "img.png"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"data")
    repo = InMemoryMediaRepository()
    svc = VideoGeneratorService(cfg, repo)
    result = asyncio.run(svc.generate("prompt", image_path=str(img)))
    assert result.startswith("video/")


def test_generate_music(cfg: Config) -> None:
    repo = InMemoryMediaRepository()
    svc = MusicGeneratorService(cfg, repo)
    result = asyncio.run(svc.generate("idea"))
    assert result.startswith("music/")


def test_generate_voice(cfg: Config) -> None:
    repo = InMemoryMediaRepository()
    svc = VoiceGeneratorService(cfg, repo)
    result = asyncio.run(svc.generate("idea"))
    assert result["filename"].startswith("voice/")


def test_generate_voice_invalid(cfg: Config) -> None:
    repo = InMemoryMediaRepository()
    svc = VoiceGeneratorService(cfg, repo)
    with pytest.raises(ValueError):
        asyncio.run(svc.generate(""))
