from __future__ import annotations

import asyncio
import time
from typing import Dict, List

from config import Config
from utils import file_operations
from utils.api_clients import openai_chat, openai_speech
from caching.cache_manager import CacheManager
from utils.monitoring import collector
from utils.validation import sanitize_prompt
from .interfaces import MediaGeneratorInterface


class VoiceGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, cache: CacheManager | None = None) -> None:
        self.config = config
        self.cache = cache

    async def generate(self, prompt: str, **kwargs) -> Dict[str, str]:
        idea = sanitize_prompt(prompt)
        key = idea
        if self.cache:
            key, _ = self.cache.dedup.check_prompt(idea)
            cached = await self.cache.get_cached_image(key)
            if cached:
                return {"filename": cached, "dialog": idea, "voice": "cached", "instructions": ""}
        examples = await file_operations.read_file("prompts/voice_examples.txt")
        loop = asyncio.get_event_loop()
        start = loop.time()
        chat_prompt = f"Create a brief question for: {idea}\n{examples}"
        chat = await openai_chat(chat_prompt, self.config)
        content = chat.choices[0].message.content
        fields = {
            k.lower(): v.strip().strip('"')
            for line in content.split("\n")
            if ':' in line
            for k, v in [line.split(':', 1)]
        }
        dialog = fields.get("dialog", "")
        instructions = fields.get("instructions", "Speak naturally")
        voice = "shimmer" if "shimmer" in fields.get("voice", "").lower() else "onyx"
        try:
            speech = await openai_speech(dialog, voice, instructions, self.config)
            filename = f"voice/openai_voice_{int(time.time())}.mp3"
            await asyncio.to_thread(speech.stream_to_file, filename)
            if self.cache:
                await self.cache.cache_generation_result(key, {"file": filename})
            return {"filename": filename, "dialog": dialog, "voice": voice, "instructions": instructions}
        except Exception:
            collector.increment_error("voice", "generate")
            raise
        finally:
            collector.observe_response("voice", loop.time() - start)

    async def generate_batch(self, prompts: List[str]) -> List[Dict[str, str]]:
        sem = asyncio.Semaphore(3)

        async def gen(p: str) -> Dict[str, str]:
            async with sem:
                return await self.generate(p)

        return await asyncio.gather(*(gen(p) for p in prompts))

    async def get_supported_formats(self) -> List[str]:
        return ["mp3"]

    async def validate_input(self, **kwargs) -> bool:
        return bool(kwargs.get("prompt"))


async def generate_voice_dialog(idea: str, config: Config, cache: CacheManager | None = None) -> Dict[str, str]:
    return await VoiceGeneratorService(config, cache).generate(idea)
