import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from pathlib import Path

import pytest
import pytest_asyncio

from config import Config
from services import image_generator, video_generator, music_generator, voice_generator
from utils import file_operations
from tests import mocks


@pytest.fixture
def cfg() -> Config:
    return Config("sk", "sa", "rep", 60)


@pytest.fixture(autouse=True)
def patch_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(image_generator, "replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr(image_generator, "http_get", mocks.fake_http_get)
    monkeypatch.setattr(video_generator, "replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr(video_generator, "validate_file_path", lambda p, a: Path(p).resolve())
    monkeypatch.setattr(music_generator, "http_post", mocks.fake_http_post)
    monkeypatch.setattr(music_generator, "http_get", mocks.fake_http_get)
    monkeypatch.setattr(voice_generator, "openai_chat", mocks.fake_openai_chat)
    monkeypatch.setattr(voice_generator, "openai_speech", mocks.fake_openai_speech)
    monkeypatch.setattr("utils.validation.validate_file_path", lambda p, a: Path(p).resolve())


@pytest_asyncio.fixture(autouse=True)
async def patch_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def fake_save(path: str, data: bytes) -> None:
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(p.write_bytes, data)

    monkeypatch.setattr(file_operations, "save_file", fake_save)
    async def fake_speech(text: str, voice: str, instructions: str, config: Config):
        class S:
            def stream_to_file(self, filename: str) -> None:
                f = tmp_path / filename
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(b"v")

        return S()
    monkeypatch.setattr(voice_generator, "openai_speech", fake_speech)
    yield


def test_generate_image(cfg: Config) -> None:
    result = asyncio.run(image_generator.generate_image("prompt", cfg))
    assert result.startswith("image/")


def test_generate_video(cfg: Config, tmp_path: Path) -> None:
    img = tmp_path / "image" / "img.png"
    img.parent.mkdir(parents=True)
    img.write_bytes(b"data")
    result = asyncio.run(video_generator.generate_video(str(img), "prompt", cfg))
    assert result.startswith("video/")


def test_generate_music(cfg: Config) -> None:
    result = asyncio.run(music_generator.generate_music("idea", cfg))
    assert result.startswith("music/")


def test_generate_voice(cfg: Config) -> None:
    result = asyncio.run(voice_generator.generate_voice_dialog("idea", cfg))
    assert result["filename"].startswith("voice/")


def test_generate_voice_invalid(cfg: Config) -> None:
    with pytest.raises(ValueError):
        asyncio.run(voice_generator.generate_voice_dialog("", cfg))
