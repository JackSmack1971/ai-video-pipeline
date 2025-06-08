from __future__ import annotations

import asyncio
from typing import Dict, List
import uuid

from config import Config
from services.container import Container
from utils.media_processing import merge_video_audio
from .stages import (
    PipelineContext,
    IdeaGeneration,
    ImageGeneration,
    VideoGeneration,
    MusicGeneration,
    VoiceGeneration,
    Composition,
)
from .scheduler import PipelineScheduler
from .state_manager import StateManager
from .progress import ProgressTracker


class ContentPipeline:
    def __init__(self, config: Config, container: Container) -> None:
        self.config = config
        self.container = container
        self.state = StateManager("pipeline_state.json")
        self.progress = ProgressTracker()
        self.scheduler = PipelineScheduler(self.config.pipeline.video_batch_large)
        self.stages = self._build_stages()

    def _build_stages(self) -> List:
        stages: List = [
            IdeaGeneration(self.container["idea_generator"]),
            ImageGeneration(self.container["image_generator"]),
            VideoGeneration(self.container["video_generator"]),
            MusicGeneration(self.container["music_generator"]),
        ]
        voice = self.container.get("voice_generator")
        if voice:
            stages.append(VoiceGeneration(voice))
        stages.append(Composition(self.config.pipeline.default_video_duration))
        return stages

    async def run_single_video(self) -> Dict[str, str]:
        from utils.monitoring import PIPELINE_SUCCESS, PIPELINE_FAILURE

        try:
            result = await self.scheduler.run_pipeline(
                self.stages, self.state, self.progress
            )
            PIPELINE_SUCCESS.inc()
            return {"idea": result.idea or "", "video": result.output or ""}
        except Exception:
            PIPELINE_FAILURE.inc()
            raise

    async def run_multiple_videos(self, count: int) -> List[Dict[str, str]]:
        async def single() -> Dict[str, str]:
            state = StateManager(f"state_{uuid.uuid4().hex}.json")
            scheduler = PipelineScheduler(self.config.pipeline.video_batch_large)
            result = await scheduler.run_pipeline(
                self.stages, state, ProgressTracker()
            )
            return {"idea": result.idea or "", "video": result.output or ""}

        return await asyncio.gather(*(single() for _ in range(count)))

    async def run_music_only(self, prompt: str) -> Dict[str, str]:
        stage = MusicGeneration(self.container["music_generator"])
        ctx = PipelineContext(idea=prompt)
        res = await self.scheduler.run_pipeline(
            [stage], self.state, ProgressTracker(), ctx
        )
        return {"music": res.music_path or ""}


async def run_pipeline(config: Config) -> Dict[str, str]:
    from services.factory import create_services
    from utils.logging_config import setup_logging
    from utils.monitoring import start_metrics_server, start_health_server

    setup_logging()
    start_metrics_server(8000)
    await start_health_server(8001)
    container = create_services(config)
    pipeline = ContentPipeline(config, container)
    return await pipeline.run_single_video()


if __name__ == "__main__":
    from config import load_config_async

    cfg = asyncio.run(load_config_async())
    result = asyncio.run(run_pipeline(cfg))
    print(result)

__all__ = [
    "ContentPipeline",
    "run_pipeline",
    "merge_video_audio",
]
