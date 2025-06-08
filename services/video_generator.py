from __future__ import annotations

import time
from pathlib import Path
from typing import List

from config import Config
from utils.validation import sanitize_prompt, validate_file_path
from utils import file_operations
from utils.api_clients import replicate_run
from .interfaces import MediaGeneratorInterface


class VideoGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, prompt: str, **kwargs) -> str:
        image_path = kwargs.get("image_path")
        if not image_path:
            raise ValueError("image_path is required")
        img = validate_file_path(Path(image_path), [Path("image")])
        prompt = sanitize_prompt(prompt)
        filename = f"video/kling_video_{int(time.time())}.mp4"
        settings = {
            "aspect_ratio": "9:16",
            "cfg_scale": 0.5,
            "duration": self.config.pipeline.default_video_duration,
        }
        async def call() -> bytes:
            with open(img, "rb") as f:
                inp = {**settings, "prompt": prompt, "start_image": f}
                return await replicate_run("kwaivgi/kling-v1.6-standard", inp, self.config)
        output = await call()
        await file_operations.save_file(filename, output.read())
        return filename

    async def get_supported_formats(self) -> List[str]:
        return ["mp4"]

    async def validate_input(self, **kwargs) -> bool:
        return Path(kwargs.get("image_path", "")).suffix in {".png", ".jpg", ".jpeg"}


async def generate_video(image_path: str, prompt: str, config: Config) -> str:
    return await VideoGeneratorService(config).generate(prompt, image_path=image_path)
