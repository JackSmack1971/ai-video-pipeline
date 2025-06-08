from __future__ import annotations

import asyncio
import time
from typing import Dict, List

from config import Config
from utils.validation import sanitize_prompt
from utils import file_operations
from utils.api_clients import http_post, http_get
from exceptions import APIError, NetworkError
from .interfaces import MediaGeneratorInterface


class MusicGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def _wait_for_music(self, task_id: str, headers: Dict[str, str]) -> str:
        for _ in range(20):
            await asyncio.sleep(5)
            status = await http_get(
                f"https://api.sonauto.ai/v1/generations/status/{task_id}",
                self.config,
                headers,
            )
            if status.status != 200:
                raise APIError(await status.text())
            state = (await status.text()).strip('"')
            if state == "FAILURE":
                raise APIError("Music generation failed")
            if state == "SUCCESS":
                result = await http_get(
                    f"https://api.sonauto.ai/v1/generations/{task_id}",
                    self.config,
                    headers,
                )
                if result.status != 200:
                    raise APIError(await result.text())
                data = await result.json()
                return data["song_paths"][0]
        raise NetworkError("Music generation timed out")

    async def generate(self, prompt: str, **kwargs) -> str:
        prompt = sanitize_prompt(prompt)
        filename = f"music/sonauto_music_{int(time.time())}.mp3"
        payload = {
            "prompt": prompt,
            "tags": ["ethereal", "chants"],
            "instrumental": True,
            "prompt_strength": 2.3,
            "output_format": "mp3",
        }
        headers = {
            "Authorization": f"Bearer {self.config.sonauto_api_key}",
            "Content-Type": "application/json",
        }
        resp = await http_post("https://api.sonauto.ai/v1/generations", payload, headers, self.config)
        data = await resp.json()
        task_id = data["task_id"]
        url = await self._wait_for_music(task_id, headers)
        song = await http_get(url, self.config, None)
        await file_operations.save_file(filename, await song.read())
        return filename

    async def get_supported_formats(self) -> List[str]:
        return ["mp3"]

    async def validate_input(self, **kwargs) -> bool:
        return bool(kwargs.get("prompt"))


async def generate_music(prompt: str, config: Config) -> str:
    return await MusicGeneratorService(config).generate(prompt)
