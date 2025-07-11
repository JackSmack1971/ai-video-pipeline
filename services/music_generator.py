from __future__ import annotations

import asyncio
import time
from typing import Dict, List, AsyncIterator

from config import Config
from utils.validation import sanitize_prompt, sanitize_prompt_param
from repositories.media_repository import MediaRepository
from utils.api_clients import http_post, http_get
from utils.monitoring import collector, tracer
from monitoring.structured_logger import get_logger
from security.input_validator import InputValidator

logger = get_logger(__name__)
from exceptions import SonautoError, NetworkError
from .interfaces import MediaGeneratorInterface


class MusicGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, media_repo: MediaRepository) -> None:
        self.config = config
        self.media_repo = media_repo

    async def _wait_for_music(self, task_id: str, headers: Dict[str, str]) -> str:
        for _ in range(20):
            await asyncio.sleep(5)
            status = await http_get(
                f"https://api.sonauto.ai/v1/generations/status/{task_id}",
                self.config,
                headers,
            )
            if status.status != 200:
                raise SonautoError(await status.text())
            state = (await status.text()).strip('"')
            if state == "FAILURE":
                raise SonautoError("Music generation failed")
            if state == "SUCCESS":
                result = await http_get(
                    f"https://api.sonauto.ai/v1/generations/{task_id}",
                    self.config,
                    headers,
                )
                if result.status != 200:
                    raise SonautoError(await result.text())
                data = await result.json()
                return data["song_paths"][0]
        raise NetworkError("Music generation timed out")

    @sanitize_prompt_param
    async def generate(self, prompt: str, **kwargs) -> str:
        filename = f"music/sonauto_music_{int(time.time())}.mp3"
        loop = asyncio.get_event_loop(); start = loop.time()
        logger.info("music_generate_start")
        payload = {
            "prompt": prompt,
            "tags": ["ethereal", "chants"],
            "instrumental": True,
            "prompt_strength": 2.3,
            "output_format": "mp3",
        }
        headers = {"Authorization": f"Bearer {self.config.sonauto_api_key}", "Content-Type": "application/json"}
        try:
            with tracer.trace_api_call("sonauto", "create"):
                resp = await http_post("https://api.sonauto.ai/v1/generations", payload, headers, self.config)
            data = await resp.json()
            task_id = data["task_id"]
            url = await self._wait_for_music(task_id, headers)
            song = await http_get(url, self.config, None)
            async def _reader() -> AsyncIterator[bytes]:
                yield await song.read()
            await self.media_repo.save_media(filename, _reader())
            logger.info("music_generate_done", extra={"file": filename})
            return filename
        except Exception:
            collector.increment_error("music", "generate")
            raise
        finally:
            collector.observe_response("music", loop.time() - start)

    async def generate_batch(self, prompts: List[str]) -> List[str]:
        sem = asyncio.Semaphore(3)

        async def gen(p: str) -> str:
            async with sem:
                return await self.generate(p)

        return await asyncio.gather(*(gen(p) for p in prompts))

    async def get_supported_formats(self) -> List[str]:
        return ["mp3"]

    async def validate_input(self, **kwargs) -> bool:
        return bool(kwargs.get("prompt"))


async def generate_music(prompt: str, config: Config, repo: MediaRepository) -> str:
    return await MusicGeneratorService(config, repo).generate(prompt)
