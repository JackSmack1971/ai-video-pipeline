import asyncio
from typing import Any, Dict, Optional

import aiohttp
import replicate
from openai import AsyncOpenAI

from config import Config
from utils.api import api_call_with_retry
from exceptions import (
    CircuitBreaker,
    OpenAIError,
    ReplicateError,
    SonautoError,
)
from exceptions import get_policy

_session: Optional[aiohttp.ClientSession] = None
_openai_breaker = CircuitBreaker()
_replicate_breaker = CircuitBreaker()
_sonauto_breaker = CircuitBreaker()


def _get_session(timeout: int) -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
    return _session


async def openai_chat(prompt: str, config: Config, model: str = "gpt-4o") -> Any:
    client = AsyncOpenAI(api_key=config.openai_api_key, timeout=config.api_timeout)

    async def call() -> Any:
        return await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        return await api_call_with_retry(
            "openai_chat",
            call,
            service="openai",
            timeout=config.api_timeout,
            breaker=_openai_breaker,
        )
    except Exception as exc:
        raise OpenAIError(str(exc)) from exc


async def openai_speech(
    text: str, voice: str, instructions: str, config: Config
) -> Any:
    client = AsyncOpenAI(api_key=config.openai_api_key, timeout=config.api_timeout)

    async def call() -> Any:
        return await client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            instructions=instructions,
        )

    try:
        return await api_call_with_retry(
            "openai_tts",
            call,
            service="openai",
            timeout=config.api_timeout,
            breaker=_openai_breaker,
        )
    except Exception as exc:
        raise OpenAIError(str(exc)) from exc


async def replicate_run(model: str, inputs: Dict[str, Any], config: Config) -> Any:
    client = replicate.Client(api_token=config.replicate_api_key)

    async def call() -> Any:
        return await replicate.async_run(client, model, input=inputs)

    try:
        return await api_call_with_retry(
            model,
            call,
            service="replicate",
            timeout=config.api_timeout,
            breaker=_replicate_breaker,
        )
    except Exception as exc:
        raise ReplicateError(str(exc)) from exc


async def http_get(
    url: str, config: Config, headers: Optional[Dict[str, str]] = None
) -> aiohttp.ClientResponse:
    session = _get_session(config.api_timeout)

    async def call() -> aiohttp.ClientResponse:
        resp = await session.get(url, headers=headers)
        resp.raise_for_status()
        return resp

    try:
        return await api_call_with_retry(
            "http_get",
            call,
            service="sonauto",
            timeout=config.api_timeout,
            breaker=_sonauto_breaker,
        )
    except Exception as exc:
        raise SonautoError(str(exc)) from exc


async def http_post(
    url: str, payload: Dict[str, Any], headers: Dict[str, str], config: Config
) -> aiohttp.ClientResponse:
    session = _get_session(config.api_timeout)

    async def call() -> aiohttp.ClientResponse:
        resp = await session.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp

    try:
        return await api_call_with_retry(
            "http_post",
            call,
            service="sonauto",
            timeout=config.api_timeout,
            breaker=_sonauto_breaker,
        )
    except Exception as exc:
        raise SonautoError(str(exc)) from exc
