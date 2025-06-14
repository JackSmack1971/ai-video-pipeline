from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import List, AsyncIterator

from config import Config
from utils.validation import sanitize_prompt, validate_file_path, sanitize_prompt_param
from repositories.media_repository import MediaRepository
from utils.api_clients import replicate_run
from utils.monitoring import collector, tracer
from monitoring.structured_logger import get_logger
from security.input_validator import InputValidator

logger = get_logger(__name__)
from .interfaces import MediaGeneratorInterface


class VideoGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, media_repo: MediaRepository) -> None:
        self.config = config
        self.media_repo = media_repo

    @sanitize_prompt_param
    async def generate(self, prompt: str, **kwargs) -> str:
        image_path = kwargs.get("image_path")
        if not image_path:
            raise ValueError("image_path is required")
        img = validate_file_path(Path(image_path), [Path("image")])
        filename = f"video/kling_video_{int(time.time())}.mp4"
        settings = {
            "aspect_ratio": "9:16",
            "cfg_scale": 0.5,
            "duration": self.config.pipeline.default_video_duration,
        }
        loop = asyncio.get_event_loop()
        start = loop.time()
        logger.info("video_generate_start", extra={"image": image_path})
        async def call() -> bytes:
            with open(img, "rb") as f:
                inp = {**settings, "prompt": prompt, "start_image": f}
                return await replicate_run("kwaivgi/kling-v1.6-standard", inp, self.config)
        try:
            with tracer.trace_api_call("replicate", "kling"):
                output = await call()
            data = output.read()
            async def _reader() -> AsyncIterator[bytes]:
                yield data
            await self.media_repo.save_media(filename, _reader())
            logger.info("video_generate_done", extra={"file": filename})
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


async def generate_video(image_path: str, prompt: str, config: Config, repo: MediaRepository) -> str:
    return await VideoGeneratorService(config, repo).generate(prompt, image_path=image_path)
