from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import List, AsyncIterator

from config import Config
from utils.validation import sanitize_prompt, sanitize_prompt_param
from repositories.media_repository import MediaRepository
from utils.api_clients import replicate_run, http_get
from utils.monitoring import collector, tracer
from monitoring.structured_logger import get_logger
from security.input_validator import InputValidator

logger = get_logger(__name__)
from .interfaces import MediaGeneratorInterface


class ImageGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, media_repo: MediaRepository) -> None:
        self.config = config
        self.media_repo = media_repo

    @sanitize_prompt_param
    async def generate(self, prompt: str, **kwargs) -> str:
        filename = f"image/flux_image_{int(time.time())}.png"
        loop = asyncio.get_event_loop()
        start = loop.time()
        logger.info("image_generate_start", extra={"prompt": prompt})
        inputs = {
            "width": 768,
            "height": 1344,
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "9:16",
            "safety_tolerance": 6,
        }
        try:
            with tracer.trace_api_call("replicate", "flux-pro"):
                url = await replicate_run("black-forest-labs/flux-pro", inputs, self.config)
            with tracer.trace_api_call("replicate", "download"):
                resp = await http_get(url, self.config)
            async def _reader() -> AsyncIterator[bytes]:
                yield await resp.read()
            await self.media_repo.save_media(filename, _reader())
            logger.info("image_generate_done", extra={"file": filename})
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


async def generate_image(prompt: str, config: Config, repo: MediaRepository) -> str:
    return await ImageGeneratorService(config, repo).generate(prompt)
