import asyncio
import time
from typing import Dict

from config import Config
from utils.validation import sanitize_prompt
from utils import file_operations
from utils.api_clients import http_post, http_get
from exceptions import APIError, NetworkError


async def _wait_for_music(task_id: str, headers: Dict[str, str], config: Config) -> str:
    for _ in range(20):
        await asyncio.sleep(5)
        status = await http_get(
            f"https://api.sonauto.ai/v1/generations/status/{task_id}",
            config,
            headers,
        )
        if status.status_code != 200:
            raise APIError(status.text)
        state = status.text.strip('"')
        if state == "FAILURE":
            raise APIError("Music generation failed")
        if state == "SUCCESS":
            result = await http_get(
                f"https://api.sonauto.ai/v1/generations/{task_id}",
                config,
                headers,
            )
            if result.status_code != 200:
                raise APIError(result.text)
            return result.json()["song_paths"][0]
    raise NetworkError("Music generation timed out")


async def generate_music(prompt: str, config: Config) -> str:
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
        "Authorization": f"Bearer {config.sonauto_api_key}",
        "Content-Type": "application/json",
    }
    resp = await http_post("https://api.sonauto.ai/v1/generations", payload, headers, config)
    task_id = resp.json()["task_id"]
    url = await _wait_for_music(task_id, headers, config)
    song = await http_get(url, config, None)
    await file_operations.save_file(filename, song.content)
    return filename
