import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest

from config import Config
from optimization.api_cache import APICache
from optimization.connection_pool import get_session, close_all
from optimization.streaming_io import stream_copy
from optimization.memory_manager import MemoryManager
from services.image_generator import ImageGeneratorService


@pytest.mark.asyncio
async def test_api_cache_image(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = APICache(ttl=60)
    cfg = Config("k", "s", "r", 60)
    calls = 0

    async def fake_generate(self: ImageGeneratorService, prompt: str, **kw) -> str:
        nonlocal calls
        calls += 1
        return f"img_{prompt}"

    monkeypatch.setattr(ImageGeneratorService, "generate", fake_generate)
    r1 = await cache.get_or_generate_image("a", cfg)
    r2 = await cache.get_or_generate_image("a", cfg)
    assert r1 == r2
    assert calls == 1


@pytest.mark.asyncio
async def test_connection_pool_reuse() -> None:
    s1 = await get_session(5)
    s2 = await get_session(5)
    assert s1 is s2
    await close_all()


@pytest.mark.asyncio
async def test_stream_copy(tmp_path: _Path) -> None:
    src = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    src.write_bytes(b"data")
    await stream_copy(src, dest)
    assert dest.read_bytes() == b"data"


@pytest.mark.asyncio
async def test_memory_manager(tmp_path: _Path) -> None:
    file = tmp_path / "big.bin"
    file.write_bytes(b"x" * 100)
    chunks = [chunk async for chunk in MemoryManager.stream_file(file)]
    assert b"".join(chunks) == b"x" * 100
    buf = await MemoryManager.get_buffer(10)
    MemoryManager.release_buffer(buf)
    buf2 = await MemoryManager.get_buffer(5)
    assert buf2 is buf
