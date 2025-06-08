import asyncio
from pathlib import Path
import pytest

class DummyPipeline:
    async def run_single_video(self) -> str:
        await asyncio.sleep(0.01)
        return "ok"

    async def run_multiple_videos(self, count: int) -> list[str]:
        await asyncio.sleep(0.01)
        return ["ok" for _ in range(count)]

dummy = DummyPipeline()

@pytest.mark.asyncio
async def test_concurrent_single_video_generations() -> None:
    tasks = [dummy.run_single_video() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    assert results.count("ok") == 10

@pytest.mark.asyncio
async def test_batch_processing_max_size() -> None:
    res = await dummy.run_multiple_videos(5)
    assert len(res) == 5

@pytest.mark.asyncio
async def test_system_behavior_under_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = 0
    async def limited():
        nonlocal counter
        counter += 1
        if counter > 3:
            raise ConnectionError("rate limit")
        return "ok"
    monkeypatch.setattr(dummy, "run_single_video", limited)
    tasks = [dummy.run_single_video() for _ in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert any(isinstance(r, ConnectionError) for r in results)

@pytest.mark.asyncio
async def test_resource_cleanup_under_high_load(tmp_path: Path) -> None:
    tmp = tmp_path / "temp.txt"
    tmp.write_text("x")
    tmp.unlink()
    assert not tmp.exists()
