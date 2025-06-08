from __future__ import annotations

from typing import Dict, Optional

from config import Config

from .content_deduplicator import ContentDeduplicator
from .cdn_manager import CDNManager


class CacheManager:
    """Coordinate multi-level caching and CDN uploads."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._image_cache: Dict[str, str] = {}
        self._result_cache: Dict[str, Dict] = {}
        self.dedup = ContentDeduplicator()
        self.cdn = CDNManager(config)

    async def get_cached_image(self, prompt_hash: str) -> Optional[str]:
        return self._image_cache.get(prompt_hash)

    async def cache_generation_result(self, job_id: str, result: Dict) -> None:
        self._result_cache[job_id] = result
        path = result.get("file")
        if path:
            self._image_cache[job_id] = path
            await self.cdn.upload_file(path)

    async def warm_cache_for_common_prompts(self) -> None:
        prompts = await self.dedup.common_prompts()
        for prompt in prompts:
            key = self.dedup.prompt_hash(prompt)
            if key not in self._image_cache:
                self._image_cache[key] = f"precache/{key}.png"
                await self.cdn.upload_file(self._image_cache[key])
