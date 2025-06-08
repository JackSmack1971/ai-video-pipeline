import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pytest
import pytest_asyncio

from config import Config
from pipeline import ContentPipeline, PipelineState, PipelineContext
from services.factory import create_services
from tests import mocks
from utils import file_operations

@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    c = Config("sk", "sa", "rep", 60)
    c.pipeline.history_file = str(tmp_path / "history.json")
    return c

@pytest_asyncio.fixture(autouse=True)
async def patch_external(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("services.image_generator.replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr("services.image_generator.http_get", mocks.fake_http_get)
    monkeypatch.setattr("services.video_generator.replicate_run", mocks.fake_replicate_run)
    monkeypatch.setattr("services.music_generator.http_post", mocks.fake_http_post)
    monkeypatch.setattr("services.music_generator.http_get", mocks.fake_http_get)
    monkeypatch.setattr("services.idea_generator.openai_chat", mocks.fake_openai_chat)
    monkeypatch.setattr("services.voice_generator.openai_chat", mocks.fake_openai_chat)
    monkeypatch.setattr("services.voice_generator.openai_speech", mocks.fake_openai_speech)
    monkeypatch.setattr("pipeline.merge_video_audio", mocks.async_merge)
    monkeypatch.setattr(
        "services.video_generator.validate_file_path",
        lambda p, a: (tmp_path / p).resolve(),
    )
    async def fake_save(path: str, data: bytes) -> None:
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(p.write_bytes, data)
    async def fake_read(path: str) -> str:
        return "[]"
    monkeypatch.setattr(file_operations, "save_file", fake_save)
    monkeypatch.setattr(file_operations, "read_file", fake_read)
    yield

@pytest.mark.asyncio
async def test_complete_single_video_pipeline(cfg: Config) -> None:
    pipe = ContentPipeline(cfg, create_services(cfg))
    res = await pipe.run_single_video()
    assert res["video"].endswith("final_output.mp4")

@pytest.mark.asyncio
async def test_batch_processing_with_failures(cfg: Config, monkeypatch: pytest.MonkeyPatch) -> None:
    called = 0

    async def bad_generate(*a, **k):
        nonlocal called
        called += 1
        if called == 2:
            raise RuntimeError("fail")
        return await mocks.fake_replicate_run(*a, **k)

    monkeypatch.setattr("services.video_generator.replicate_run", bad_generate)
    pipe = ContentPipeline(cfg, create_services(cfg))

    with pytest.raises(RuntimeError, match="fail"):
        await pipe.run_multiple_videos(3)

    assert called >= 2

@pytest.mark.asyncio
async def test_pipeline_recovery_from_each_stage(cfg: Config, tmp_path: Path) -> None:
    pipe = ContentPipeline(cfg, create_services(cfg))
    state = pipe.state_mgr
    await state.save_state(
        pipe.pipeline_id,
        PipelineState("image_generation", PipelineContext(image_path="img", prompt="p")),
    )
    res = await pipe.run_single_video()
    assert res["video"].endswith("final_output.mp4")

@pytest.mark.asyncio
async def test_configuration_changes_during_execution(cfg: Config, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = ContentPipeline(cfg, create_services(cfg))
    async def fake_merge(*a, **k):
        return "merged.mp4"
    monkeypatch.setattr("pipeline.merge_video_audio", fake_merge)
    cfg.pipeline.default_video_duration = 5
    res = await pipe.run_single_video()
    assert res["video"].endswith("merged.mp4")
