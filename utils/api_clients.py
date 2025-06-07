import asyncio
from typing import Any, Dict, Optional

import requests
import replicate
from openai import OpenAI

from config import Config
from utils.api import api_call_with_retry


async def openai_chat(prompt: str, config: Config, model: str = "gpt-4o") -> Any:
    client = OpenAI(api_key=config.openai_api_key)

    async def call() -> Any:
        return await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

    return await api_call_with_retry("openai_chat", call, timeout=config.api_timeout)


async def openai_speech(
    text: str, voice: str, instructions: str, config: Config
) -> Any:
    client = OpenAI(api_key=config.openai_api_key)

    async def call() -> Any:
        return await asyncio.to_thread(
            client.audio.speech.create,
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            instructions=instructions,
        )

    return await api_call_with_retry("openai_tts", call, timeout=config.api_timeout)


async def replicate_run(model: str, inputs: Dict[str, Any], config: Config) -> Any:
    async def call() -> Any:
        return await asyncio.to_thread(replicate.run, model, input=inputs)

    return await api_call_with_retry(model, call, timeout=config.api_timeout)


async def http_get(
    url: str, config: Config, headers: Optional[Dict[str, str]] = None
) -> requests.Response:
    async def call() -> requests.Response:
        return await asyncio.to_thread(
            requests.get, url, headers=headers, timeout=config.api_timeout
        )

    return await api_call_with_retry("http_get", call, timeout=config.api_timeout)


async def http_post(
    url: str, payload: Dict[str, Any], headers: Dict[str, str], config: Config
) -> requests.Response:
    async def call() -> requests.Response:
        return await asyncio.to_thread(
            requests.post, url, json=payload, headers=headers, timeout=config.api_timeout
        )

    return await api_call_with_retry("http_post", call, timeout=config.api_timeout)
