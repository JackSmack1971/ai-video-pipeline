import time
from pathlib import Path

from config import Config
from utils.validation import sanitize_prompt
from utils import file_operations
from utils.api_clients import replicate_run, http_get


async def generate_image(prompt: str, config: Config) -> str:
    prompt = sanitize_prompt(prompt)
    filename = f"image/flux_image_{int(time.time())}.png"
    inputs = {
        "width": 768,
        "height": 1344,
        "prompt": prompt,
        "output_format": "png",
        "aspect_ratio": "9:16",
        "safety_tolerance": 6,
    }
    url = await replicate_run("black-forest-labs/flux-pro", inputs, config)
    resp = await http_get(url, config)
    await file_operations.save_file(filename, resp.content)
    return filename
