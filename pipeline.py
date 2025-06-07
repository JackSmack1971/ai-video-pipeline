from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Protocol

from config import Config
from utils.media_processing import merge_video_audio


class IdeaGenerator(Protocol):
    async def generate(self) -> Dict[str, str]:
        ...


class ImageGenerator(Protocol):
    async def generate(self, prompt: str) -> str:
        ...


class VideoGenerator(Protocol):
    async def generate(self, image_path: str, prompt: str) -> str:
        ...


class MusicGenerator(Protocol):
    async def generate(self, prompt: str) -> str:
        ...


class VoiceGenerator(Protocol):
    async def generate(self, idea: str) -> Dict[str, str]:
        ...


class ContentPipeline:
    def __init__(self, config: Config, services: Dict[str, Any]) -> None:
        self.config = config
        self.idea_service: IdeaGenerator = services["idea_generator"]
        self.image_service: ImageGenerator = services["image_generator"]
        self.video_service: VideoGenerator = services["video_generator"]
        self.music_service: MusicGenerator = services["music_generator"]
        self.voice_service: Optional[VoiceGenerator] = services.get("voice_generator")

    async def run_single_video(self) -> Dict[str, str]:
        idea = await self.idea_service.generate()
        media = await self._generate_media(idea)
        video = await self._merge(media)
        return {"idea": idea["idea"], "video": video}

    async def run_music_only(self, prompt: str) -> Dict[str, str]:
        music = await self.music_service.generate(prompt)
        return {"music": music}

    async def _generate_media(self, idea: Dict[str, str]) -> Dict[str, Any]:
        image_path = await self.image_service.generate(idea["prompt"])
        video_path = await self.video_service.generate(image_path, idea["prompt"])
        music_path = await self.music_service.generate(idea["idea"])
        voice = None
        if self.voice_service:
            voice = await self.voice_service.generate(idea["idea"])
        return {"video": video_path, "music": music_path, "voice": voice}

    async def _merge(self, media: Dict[str, Any]) -> str:
        voice_file = media["voice"]["filename"] if media["voice"] else None
        return await merge_video_audio(
            media["video"], media["music"], voice_file, "final_output.mp4"
        )


async def run_pipeline(config: Config) -> Dict[str, str]:
    from services.factory import create_services

    services = create_services(config)
    pipeline = ContentPipeline(config, services)
    return await pipeline.run_single_video()


if __name__ == "__main__":
    from config import load_config

    cfg = load_config()
    result = asyncio.run(run_pipeline(cfg))
    print(result)
