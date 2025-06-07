import asyncio
import time
from pathlib import Path
from typing import Dict

import requests
import replicate
from openai import OpenAI

from config import Config
from utils import file_operations
from utils.validation import sanitize_prompt, validate_file_path
from utils.api import api_call_with_retry
from exceptions import APIError, NetworkError, FileError


async def generate_image(prompt: str, config: Config) -> str:
    try:
        prompt = sanitize_prompt(prompt)
    except ValueError:
        prompt = "A cinematic scene"
    filename = f"image/flux_image_{int(time.time())}.png"
    data = {"width": 768, "height": 1344, "prompt": prompt,
            "output_format": "png", "aspect_ratio": "9:16", "safety_tolerance": 6}

    async def run() -> str:
        return await asyncio.to_thread(replicate.run, "black-forest-labs/flux-pro", input=data)

    try:
        url = await api_call_with_retry("flux_image", run, timeout=config.api_timeout)
        resp = await api_call_with_retry(
            "download_image",
            lambda: asyncio.to_thread(requests.get, url, timeout=config.api_timeout),
        )
        await file_operations.save_file(filename, resp.content)
        return filename
    except (APIError, NetworkError, FileError):
        raise
    except Exception as exc:
        raise APIError(str(exc)) from exc


async def generate_video(image_path: str, prompt: str, config: Config) -> str:
    img = validate_file_path(Path(image_path), [Path("image")])
    try:
        prompt = sanitize_prompt(prompt)
    except ValueError:
        prompt = "cinematic video"
    filename = f"video/kling_video_{int(time.time())}.mp4"
    settings = {"aspect_ratio": "9:16", "cfg_scale": 0.5, "duration": 10}

    async def run() -> bytes:
        with open(img, "rb") as f:
            input_d = {**settings, "prompt": prompt, "start_image": f}
            return await asyncio.to_thread(
                replicate.run, "kwaivgi/kling-v1.6-standard", input=input_d
            )

    try:
        output = await api_call_with_retry("kling_video", run, timeout=config.api_timeout)
        await file_operations.save_file(filename, output.read())
        return filename
    except (APIError, NetworkError, FileError):
        raise
    except Exception as exc:
        raise APIError(str(exc)) from exc


async def generate_music(prompt: str, config: Config) -> str:
    try:
        prompt = sanitize_prompt(prompt)
    except ValueError:
        prompt = "ambient"
    filename = f"music/sonauto_music_{int(time.time())}.mp3"
    payload = {"prompt": prompt, "tags": ["ethereal", "chants"], "instrumental": True,
              "prompt_strength": 2.3, "output_format": "mp3"}
    headers = {"Authorization": f"Bearer {config.sonauto_api_key}", "Content-Type": "application/json"}
    start = lambda: asyncio.to_thread(
        requests.post,
        "https://api.sonauto.ai/v1/generations",
        json=payload,
        headers=headers,
        timeout=config.api_timeout,
    )
    resp = await api_call_with_retry("sonauto_start", start, timeout=config.api_timeout)
    if resp.status_code != 200:
        raise APIError(resp.text)
    task_id = resp.json()["task_id"]
    song_url = await _wait_for_music(task_id, headers, config)
    song = await api_call_with_retry(
        "download_music",
        lambda: asyncio.to_thread(requests.get, song_url, timeout=config.api_timeout),
        timeout=config.api_timeout,
    )
    await file_operations.save_file(filename, song.content)
    return filename


async def _wait_for_music(task_id: str, headers: dict, config: Config) -> str:
    for _ in range(20):
        await asyncio.sleep(5)
        status_resp = await api_call_with_retry(
            "sonauto_status",
            lambda: asyncio.to_thread(requests.get,
                                      f"https://api.sonauto.ai/v1/generations/status/{task_id}",
                                      headers=headers, timeout=config.api_timeout),
            timeout=config.api_timeout,
        )
        if status_resp.status_code != 200:
            raise APIError(status_resp.text)
        status = status_resp.text.strip('"')
        if status == "FAILURE":
            raise APIError("Music generation failed")
        if status == "SUCCESS":
            result_resp = await api_call_with_retry(
                "sonauto_result",
                lambda: asyncio.to_thread(requests.get,
                                          f"https://api.sonauto.ai/v1/generations/{task_id}",
                                          headers=headers, timeout=config.api_timeout),
                timeout=config.api_timeout,
            )
            if result_resp.status_code != 200:
                raise APIError(result_resp.text)
            return result_resp.json()["song_paths"][0]
    raise NetworkError("Music generation timed out")


async def generate_voice_dialog(idea: str, config: Config) -> Dict[str, str]:
    examples = await file_operations.read_file("prompts/voice_examples.txt")
    prompt = f"Create a brief question for: {idea}\n{examples}"
    client = OpenAI(api_key=config.openai_api_key)
    chat_resp = await api_call_with_retry(
        "openai_chat",
        lambda: asyncio.to_thread(client.chat.completions.create, model="gpt-4o", messages=[{"role": "user", "content": prompt}]),
        timeout=config.api_timeout,
    )
    content = chat_resp.choices[0].message.content
    fields = {
        k.lower(): v.strip().strip('"')
        for line in content.split("\n") if ':' in line
        for k, v in [line.split(':', 1)]
    }
    dialog = fields.get('dialog', '')
    instructions = fields.get('instructions', 'Speak naturally')
    voice = 'shimmer' if 'shimmer' in fields.get('voice', '').lower() else 'onyx'
    speech = await api_call_with_retry(
        "openai_tts",
        lambda: asyncio.to_thread(client.audio.speech.create, model="gpt-4o-mini-tts", voice=voice, input=dialog, instructions=instructions),
        timeout=config.api_timeout,
    )
    filename = f"voice/openai_voice_{int(time.time())}.mp3"
    await api_call_with_retry(
        "save_voice", lambda: asyncio.to_thread(speech.stream_to_file, filename), timeout=config.api_timeout
    )
    return {"filename": filename, "dialog": dialog, "voice": voice, "instructions": instructions}
