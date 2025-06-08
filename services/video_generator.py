from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import List

from config import Config
from utils.validation import sanitize_prompt, validate_file_path
from utils import file_operations
from caching.cache_manager import CacheManager
from utils.api_clients import replicate_run
from utils.monitoring import collector
from .interfaces import MediaGeneratorInterface


class VideoGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, cache: CacheManager | None = None) -> None:
        self.config = config
        self.cache = cache

    async def generate(self, prompt: str, **kwargs) -> str:
        image_path = kwargs.get("image_path")
        if not image_path:
            raise ValueError("image_path is required")
        img = validate_file_path(Path(image_path), [Path("image")])
        prompt = sanitize_prompt(prompt)
        key = prompt
        if self.cache:
            key, _ = self.cache.dedup.check_prompt(prompt)
            cached = await self.cache.get_cached_image(key)
            if cached:
                return cached
        filename = f"video/kling_video_{int(time.time())}.mp4"
        settings = {
            "aspect_ratio": "9:16",
            "cfg_scale": 0.5,
            "duration": self.config.pipeline.default_video_duration,
        }
        loop = asyncio.get_event_loop()
        start = loop.time()
        async def call() -> bytes:
            with open(img, "rb") as f:
                inp = {**settings, "prompt": prompt, "start_image": f}
                return await replicate_run("kwaivgi/kling-v1.6-standard", inp, self.config)
        try:
            output = await call()
            data = output.read()
            if self.cache:
                await file_operations.save_cached_file(filename, data)
                await self.cache.cache_generation_result(key, {"file": filename})
            else:
                await file_operations.save_file(filename, data)
            return filename
        except Exception:
            collector.increment_error("video", "generate")
            raise
        finally:
            collector.observe_response("video", loop.time() - start)

    async def generate_batch(self, items: List[dict]) -> List[str]:
        sem = asyncio.Semaphore(2)

        async def gen(it: dict) -> str:
            async with sem:
                return await self.generate(it["prompt"], image_path=it["image_path"])

        return await asyncio.gather(*(gen(i) for i in items))

    async def get_supported_formats(self) -> List[str]:
        return ["mp4"]

    async def validate_input(self, **kwargs) -> bool:
        return Path(kwargs.get("image_path", "")).suffix in {".png", ".jpg", ".jpeg"}


async def generate_video(image_path: str, prompt: str, config: Config, cache: CacheManager | None = None) -> str:
    return await VideoGeneratorService(config, cache).generate(prompt, image_path=image_path)
