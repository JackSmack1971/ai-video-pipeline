from __future__ import annotations

from config import Config

from .container import Container
from .idea_generator import IdeaGeneratorService
from .image_generator import ImageGeneratorService
from .video_generator import VideoGeneratorService
from .music_generator import MusicGeneratorService
from .voice_generator import VoiceGeneratorService
from caching.cache_manager import CacheManager


def create_services(config: Config, container: Container | None = None) -> Container:
    container = container or Container()
    cache = CacheManager(config)
    container.register_singleton("cache_manager", lambda: cache)
    container.register_singleton("idea_generator", lambda: IdeaGeneratorService(config))
    container.register_singleton("image_generator", lambda: ImageGeneratorService(config, cache))
    container.register_singleton("video_generator", lambda: VideoGeneratorService(config, cache))
    container.register_singleton("music_generator", lambda: MusicGeneratorService(config, cache))
    container.register_singleton("voice_generator", lambda: VoiceGeneratorService(config, cache))
    return container
