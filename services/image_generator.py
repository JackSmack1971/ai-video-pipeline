from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import List

from config import Config
from utils.validation import sanitize_prompt
from utils import file_operations
from caching.cache_manager import CacheManager
from utils.api_clients import replicate_run, http_get
from utils.monitoring import collector
from .interfaces import MediaGeneratorInterface


class ImageGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, cache: CacheManager | None = None) -> None:
        self.config = config
        self.cache = cache

    async def generate(self, prompt: str, **kwargs) -> str:
        prompt = sanitize_prompt(prompt)
        key = prompt
        if self.cache:
            key, existing = self.cache.dedup.check_prompt(prompt)
            cached = await self.cache.get_cached_image(key)
            if cached:
                return cached
        filename = f"image/flux_image_{int(time.time())}.png"
        loop = asyncio.get_event_loop()
        start = loop.time()
        inputs = {
            "width": 768,
            "height": 1344,
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "9:16",
            "safety_tolerance": 6,
        }
        try:
            url = await replicate_run("black-forest-labs/flux-pro", inputs, self.config)
            resp = await http_get(url, self.config)
            data = await resp.read()
            if self.cache:
                await file_operations.save_cached_file(filename, data)
                await self.cache.cache_generation_result(key, {"file": filename})
            else:
                await file_operations.save_file(filename, data)
            return filename
        except Exception:
            collector.increment_error("image", "generate")
            raise
        finally:
            collector.observe_response("image", loop.time() - start)

    async def generate_batch(self, prompts: List[str]) -> List[str]:
        sem = asyncio.Semaphore(5)

        async def gen(p: str) -> str:
            async with sem:
                return await self.generate(p)

        return await asyncio.gather(*(gen(p) for p in prompts))

    async def get_supported_formats(self) -> List[str]:
        return ["png"]

    async def validate_input(self, **kwargs) -> bool:
        return bool(kwargs.get("prompt"))


async def generate_image(prompt: str, config: Config, cache: CacheManager | None = None) -> str:
    return await ImageGeneratorService(config, cache).generate(prompt)
