import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from config import Config
from caching.cache_manager import CacheManager
from caching.content_deduplicator import ContentDeduplicator
from caching.cache_warmer import CacheWarmer


@pytest.mark.asyncio
async def test_cache_manager(tmp_path: Path) -> None:
    cfg = Config("sk", "sa", "rep", 60)
    cm = CacheManager(cfg)
    file = tmp_path / "f.txt"
    file.write_text("x")
    await cm.cache_generation_result("k", {"file": str(file)})
    assert await cm.get_cached_image("k") == str(file)


@pytest.mark.asyncio
async def test_deduplicator() -> None:
    dedup = ContentDeduplicator()
    k1, _ = dedup.check_prompt("hello world")
    k2, prev = dedup.check_prompt("hello world!")
    assert prev == "hello world"
    assert k1 == k2


@pytest.mark.asyncio
async def test_cache_warmer(tmp_path: Path) -> None:
    cfg = Config("sk", "sa", "rep", 60)
    cm = CacheManager(cfg)
    cm.dedup.prompts["a"] = "test"
    warmer = CacheWarmer(cm)
    await warmer.warm()
    key = cm.dedup.prompt_hash("test")
    assert key in cm._image_cache
