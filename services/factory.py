from __future__ import annotations

from typing import Any, Dict

from config import Config
from . import idea_generator, image_generator, video_generator, music_generator, voice_generator


class IdeaService:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self) -> Dict[str, str]:
        return await idea_generator.generate_idea(self.config)


class ImageService:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, prompt: str) -> str:
        return await image_generator.generate_image(prompt, self.config)


class VideoService:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, image_path: str, prompt: str) -> str:
        return await video_generator.generate_video(image_path, prompt, self.config)


class MusicService:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, prompt: str) -> str:
        return await music_generator.generate_music(prompt, self.config)


class VoiceService:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, idea: str) -> Dict[str, str]:
        return await voice_generator.generate_voice_dialog(idea, self.config)


def create_services(config: Config) -> Dict[str, Any]:
    return {
        "idea_generator": IdeaService(config),
        "image_generator": ImageService(config),
        "video_generator": VideoService(config),
        "music_generator": MusicService(config),
        "voice_generator": VoiceService(config),
    }
