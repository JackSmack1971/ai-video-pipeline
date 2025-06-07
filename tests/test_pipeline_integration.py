import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from pathlib import Path

import pytest
import pytest_asyncio

from config import Config
from pipeline import ContentPipeline
from services.factory import create_services
from tests import mocks
from utils import file_operations


@pytest.fixture
def cfg() -> Config:
    return Config("sk", "sa", "rep", 1)


@pytest_asyncio.fixture(autouse=True)
def patch_external(monkeypatch: pytest.MonkeyPatch) -> None:
    targets = {
        "services.image_generator.replicate_run": mocks.fake_replicate_run,
        "services.image_generator.http_get": mocks.fake_http_get,
        "services.idea_generator.openai_chat": mocks.fake_openai_chat,
        "services.video_generator.replicate_run": mocks.fake_replicate_run,
        "services.music_generator.http_post": mocks.fake_http_post,
        "services.music_generator.http_get": mocks.fake_http_get,
        "services.voice_generator.openai_chat": mocks.fake_openai_chat,
        "services.voice_generator.openai_speech": mocks.fake_openai_speech,
        "services.idea_generator.openai_chat": mocks.fake_openai_chat,
        "pipeline.merge_video_audio": mocks.async_merge,
    }
    for path, func in targets.items():
        monkeypatch.setattr(path, func)


@pytest_asyncio.fixture(autouse=True)
async def patch_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async def fake_save(path: str, data: bytes) -> None:
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(p.write_bytes, data)

    monkeypatch.setattr(file_operations, "save_file", fake_save)

    monkeypatch.setattr(
        "services.video_generator.validate_file_path",
        lambda p, a: (tmp_path / p).resolve(),
    )
    async def fake_read(path: str) -> str:
        return "[]"
    monkeypatch.setattr(file_operations, "read_file", fake_read)
    yield


@pytest.mark.asyncio
async def test_pipeline_integration(cfg: Config) -> None:
    services = create_services(cfg)
    pipeline = ContentPipeline(cfg, services)
    result = await pipeline.run_single_video()
    assert result["video"].endswith("final_output.mp4")
