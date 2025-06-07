from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Protocol

from config import Config
from utils.media_processing import merge_video_audio
from utils.monitoring import FILE_PROCESS_TIME, PIPELINE_FAILURE, PIPELINE_SUCCESS


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
        logger = logging.getLogger(__name__)
        logger.info("Starting video generation")
        idea: Dict[str, str] | None = None
        try:
            idea = await self.idea_service.generate()
            logger.info("Idea generated", extra={"idea": idea["idea"]})
            media = await self._generate_media(idea)
            video = await self._merge(media)
            PIPELINE_SUCCESS.inc()
            logger.info(
                "Video generation complete",
                extra={"idea_id": idea["idea"], "api_provider": "kling"},
            )
            return {"idea": idea["idea"], "video": video}
        except Exception:
            PIPELINE_FAILURE.inc()
            logger.exception("Pipeline failed", extra={"idea": idea})
            raise

    async def run_multiple_videos(self, count: int) -> list[Dict[str, str]]:
        logging.getLogger(__name__).info("Starting batch", extra={"count": count})
        return await asyncio.gather(*(self.run_single_video() for _ in range(count)))

    async def run_music_only(self, prompt: str) -> Dict[str, str]:
        logging.getLogger(__name__).info("Music only generation")
        music = await self.music_service.generate(prompt)
        return {"music": music}

    async def _generate_media(self, idea: Dict[str, str]) -> Dict[str, Any]:
        logger = logging.getLogger(__name__)
        start = asyncio.get_event_loop().time()
        img_task = asyncio.create_task(self.image_service.generate(idea["prompt"]))
        music_task = asyncio.create_task(self.music_service.generate(idea["idea"]))
        voice_task = (
            asyncio.create_task(self.voice_service.generate(idea["idea"]))
            if self.voice_service
            else None
        )
        image_path = await img_task
        video_task = asyncio.create_task(
            self.video_service.generate(image_path, idea["prompt"])
        )
        video_path = await video_task
        music_path = await music_task
        voice = await voice_task if voice_task else None
        FILE_PROCESS_TIME.labels(operation="generate_media").observe(asyncio.get_event_loop().time() - start)
        logger.info("Media generated", extra={"idea": idea["idea"]})
        return {"video": video_path, "music": music_path, "voice": voice}

    async def _merge(self, media: Dict[str, Any]) -> str:
        voice_file = media["voice"]["filename"] if media["voice"] else None
        start = asyncio.get_event_loop().time()
        result = await merge_video_audio(
            media["video"],
            media["music"],
            voice_file,
            "final_output.mp4",
            self.config.pipeline.default_video_duration,
        )
        FILE_PROCESS_TIME.labels(operation="merge").observe(asyncio.get_event_loop().time() - start)
        return result


async def run_pipeline(config: Config) -> Dict[str, str]:
    from services.factory import create_services
    from utils.logging_config import setup_logging
    from utils.monitoring import start_metrics_server, start_health_server

    setup_logging()
    start_metrics_server(8000)
    await start_health_server(8001)
    services = create_services(config)
    pipeline = ContentPipeline(config, services)
    return await pipeline.run_single_video()


if __name__ == "__main__":
    from config import load_config

    cfg = load_config()
    result = asyncio.run(run_pipeline(cfg))
    print(result)
