from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Tuple

from config import Config
from services.image_generator import ImageGeneratorService
from services.music_generator import MusicGeneratorService
from utils.validation import sanitize_prompt


class APICache:
    """Simple in-memory cache for image and music generation."""

    def __init__(self, ttl: int = 300, max_items: int = 128) -> None:
        self.ttl = ttl
        self.max_items = max_items
        self._image_cache: Dict[str, Tuple[float, str]] = {}

    def _prune(self) -> None:
        now = time.time()
        keys = [k for k, (t, _) in self._image_cache.items() if now - t > self.ttl]
        for k in keys:
            self._image_cache.pop(k, None)
        while len(self._image_cache) > self.max_items:
            self._image_cache.pop(next(iter(self._image_cache)))

    async def get_or_generate_image(self, prompt: str, config: Config) -> str:
        """Cache similar image prompts to reduce API calls."""
        key = sanitize_prompt(prompt)
        cached = self._image_cache.get(key)
        if cached and time.time() - cached[0] < self.ttl:
            return cached[1]
        result = await ImageGeneratorService(config).generate(key)
        self._image_cache[key] = (time.time(), result)
        self._prune()
        return result

    async def _generate_music(self, prompt: str, config: Config) -> str:
        return await MusicGeneratorService(config).generate(prompt)

    async def batch_music_generation(self, prompts: List[str], config: Config) -> List[str]:
        """Batch multiple music requests when possible."""
        tasks = [self._generate_music(sanitize_prompt(p), config) for p in prompts]
        return await asyncio.gather(*tasks)
