from __future__ import annotations

import time
from pathlib import Path
from typing import List

from config import Config
from utils.validation import sanitize_prompt
from utils import file_operations
from utils.api_clients import replicate_run, http_get
from .interfaces import MediaGeneratorInterface


class ImageGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, prompt: str, **kwargs) -> str:
        prompt = sanitize_prompt(prompt)
        filename = f"image/flux_image_{int(time.time())}.png"
        inputs = {
            "width": 768,
            "height": 1344,
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "9:16",
            "safety_tolerance": 6,
        }
        url = await replicate_run("black-forest-labs/flux-pro", inputs, self.config)
        resp = await http_get(url, self.config)
        await file_operations.save_file(filename, await resp.read())
        return filename

    async def get_supported_formats(self) -> List[str]:
        return ["png"]

    async def validate_input(self, **kwargs) -> bool:
        return bool(kwargs.get("prompt"))


async def generate_image(prompt: str, config: Config) -> str:
    return await ImageGeneratorService(config).generate(prompt)
