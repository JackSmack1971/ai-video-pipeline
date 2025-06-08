from __future__ import annotations

from typing import Iterable

from .cache_manager import CacheManager


class CacheWarmer:
    """Analyze historical patterns and warm caches."""

    def __init__(self, manager: CacheManager) -> None:
        self.manager = manager

    async def analyze_history(self) -> Iterable[str]:
        return await self.manager.dedup.common_prompts()

    async def warm(self) -> None:
        prompts = await self.analyze_history()
        for p in prompts:
            key = self.manager.dedup.prompt_hash(p)
            if await self.manager.get_cached_image(key):
                continue
            await self.manager.cache_generation_result(key, {"file": f"warm/{key}.png"})
