from __future__ import annotations

import asyncio
import time
from typing import Dict, List, AsyncIterator

from config import Config
from utils import file_operations
from repositories.media_repository import MediaRepository
from utils.api_clients import openai_chat, openai_speech
from utils.monitoring import collector, tracer
from monitoring.structured_logger import get_logger
from utils.validation import sanitize_prompt, sanitize_prompt_param
from security.input_validator import InputValidator

logger = get_logger(__name__)
from .interfaces import MediaGeneratorInterface


class VoiceGeneratorService(MediaGeneratorInterface):
    def __init__(self, config: Config, media_repo: MediaRepository) -> None:
        self.config = config
        self.media_repo = media_repo

    @sanitize_prompt_param
    async def generate(self, prompt: str, **kwargs) -> Dict[str, str]:
        idea = prompt
        examples = await file_operations.read_file("prompts/voice_examples.txt")
        loop = asyncio.get_event_loop(); start = loop.time()
        logger.info("voice_generate_start")
        chat_prompt = f"Create a brief question for: {idea}\n{examples}"
        with tracer.trace_api_call("openai", "chat"):
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
            with tracer.trace_api_call("openai", "tts"):
                speech = await openai_speech(dialog, voice, instructions, self.config)
            filename = f"voice/openai_voice_{int(time.time())}.mp3"
            await asyncio.to_thread(speech.stream_to_file, filename)
            async def _reader() -> AsyncIterator[bytes]:
                async for chunk in file_operations.read_file_stream(filename):
                    yield chunk
            await self.media_repo.save_media(filename, _reader())
            logger.info("voice_generate_done", extra={"file": filename})
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


async def generate_voice_dialog(idea: str, config: Config, repo: MediaRepository) -> Dict[str, str]:
    return await VoiceGeneratorService(config, repo).generate(idea)
