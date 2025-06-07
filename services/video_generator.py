import time
from pathlib import Path

from config import Config
from utils.validation import sanitize_prompt, validate_file_path
from utils import file_operations
from utils.api_clients import replicate_run


async def generate_video(image_path: str, prompt: str, config: Config) -> str:
    img = validate_file_path(Path(image_path), [Path("image")])
    prompt = sanitize_prompt(prompt)
    filename = f"video/kling_video_{int(time.time())}.mp4"
    settings = {
        "aspect_ratio": "9:16",
        "cfg_scale": 0.5,
        "duration": config.pipeline.default_video_duration,
    }

    async def call() -> bytes:
        with open(img, "rb") as f:
            inp = {**settings, "prompt": prompt, "start_image": f}
            return await replicate_run("kwaivgi/kling-v1.6-standard", inp, config)

    output = await call()
    await file_operations.save_file(filename, output.read())
    return filename
