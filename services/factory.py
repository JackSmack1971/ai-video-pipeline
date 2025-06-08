from __future__ import annotations

from config import Config

from infrastructure.di_container import DIContainer
from repositories.implementations import (
    LocalMediaRepository,
    InMemoryMediaRepository,
    CachingMediaRepository,
)
from .idea_generator import IdeaGeneratorService
from .image_generator import ImageGeneratorService
from .video_generator import VideoGeneratorService
from .music_generator import MusicGeneratorService
from .voice_generator import VoiceGeneratorService


def create_services(
    config: Config,
    container: DIContainer | None = None,
    backend: str = "local",
) -> DIContainer:
    container = container or DIContainer()
    if backend == "memory":
        repo = InMemoryMediaRepository()
    else:
        repo = LocalMediaRepository()
    if backend == "cache":
        repo = CachingMediaRepository(repo)
    container.register_singleton("media_repository", lambda: repo)
    container.register_singleton("idea_generator", lambda: IdeaGeneratorService(config))
    container.register_singleton(
        "image_generator",
        lambda: ImageGeneratorService(config, container["media_repository"]),
    )
    container.register_singleton(
        "video_generator",
        lambda: VideoGeneratorService(config, container["media_repository"]),
    )
    container.register_singleton(
        "music_generator",
        lambda: MusicGeneratorService(config, container["media_repository"]),
    )
    container.register_singleton(
        "voice_generator",
        lambda: VoiceGeneratorService(config, container["media_repository"]),
    )
    return container
