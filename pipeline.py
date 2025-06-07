import asyncio
from typing import Dict

from config import load_config, Config
from services import (
    idea_generator,
    image_generator,
    video_generator,
    music_generator,
    voice_generator,
)
from utils.media_processing import merge_video_audio


async def run_pipeline(config: Config) -> Dict[str, str]:
    idea_data = await idea_generator.generate_idea(config)
    image_path = await image_generator.generate_image(idea_data["prompt"], config)
    voice = await voice_generator.generate_voice_dialog(idea_data["idea"], config)
    video_path = await video_generator.generate_video(image_path, idea_data["prompt"], config)
    music_path = await music_generator.generate_music(idea_data["idea"], config)
    output = await merge_video_audio(video_path, music_path, voice["filename"], "final_output.mp4")
    return {"idea": idea_data["idea"], "video": output}


if __name__ == "__main__":
    cfg = load_config()
    result = asyncio.run(run_pipeline(cfg))
    print(result)
