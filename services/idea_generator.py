from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, List

from config import Config
from utils import file_operations
from utils.api_clients import openai_chat
from utils.monitoring import collector, tracer
from security.input_validator import InputValidator
from monitoring.structured_logger import get_logger

logger = get_logger(__name__)
from .interfaces import IdeaGeneratorInterface


class IdeaGeneratorService(IdeaGeneratorInterface):
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self) -> Dict[str, str]:
        history = await self.get_history()
        base = await file_operations.read_file("prompts/idea_gen.txt")
        prompt = base
        loop = asyncio.get_event_loop(); start = loop.time()
        logger.info("idea_generate_start")
        if history:
            avoid = "\n\nPlease avoid generating ideas similar to:\n" + "\n".join(
                f"{i+1}. {idea}" for i, idea in enumerate(history)
            )
            prompt += avoid
        with tracer.trace_api_call("openai", "ideas"):
            response = await openai_chat(prompt, self.config)
        content = response.choices[0].message.content
        idea_part, _, prompt_part = content.partition("Prompt:")
        idea = " ".join(idea_part.replace("Idea:", "").replace("*", "").split())
        idea = await InputValidator.sanitize_text(idea.strip())
        prompt_clean = await InputValidator.sanitize_text(prompt_part.strip())
        result = {"idea": idea, "prompt": prompt_clean}
        history.append(result["idea"])
        history = history[-self.config.pipeline.max_stored_ideas :]
        try:
            await file_operations.save_file(
                self.config.pipeline.history_file, json.dumps(history).encode()
            )
            logger.info("idea_generate_done")
            return result
        except Exception:
            collector.increment_error("idea", "generate")
            raise
        finally:
            collector.observe_response("idea", loop.time() - start)

    async def get_history(self) -> List[str]:
        try:
            data = await file_operations.read_file(self.config.pipeline.history_file)
            return json.loads(data)
        except Exception:
            return []

    async def clear_history(self) -> None:
        await file_operations.save_file(self.config.pipeline.history_file, b"[]")


async def generate_idea(config: Config) -> Dict[str, str]:
    return await IdeaGeneratorService(config).generate()
