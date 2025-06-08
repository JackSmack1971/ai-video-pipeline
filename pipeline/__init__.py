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
from storage.persistence import PipelineStateManager, PipelineState
from .progress import ProgressTracker


class ContentPipeline:
    def __init__(self, config: Config, container: Container) -> None:
        self.config = config
        self.container = container
        self.pipeline_id = uuid.uuid4().hex
        self.state_mgr = PipelineStateManager()
        self.state = StateManager(f"{self.pipeline_id}_runtime.json")
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
            saved = await self.state_mgr.load_state(self.pipeline_id)
            result = await self.scheduler.run_pipeline(
                self.stages, self.state, self.progress, saved.context
            )
            await self.state_mgr.save_state(
                self.pipeline_id, PipelineState("completed", result)
            )
            PIPELINE_SUCCESS.inc()
            return {"idea": result.idea or "", "video": result.output or ""}
        except Exception:
            PIPELINE_FAILURE.inc()
            raise

    async def run_multiple_videos(self, count: int) -> List[Dict[str, str]]:
        async def single() -> Dict[str, str]:
            pid = uuid.uuid4().hex
            state = StateManager(f"state_{pid}.json")
            scheduler = PipelineScheduler(self.config.pipeline.video_batch_large)
            saved = await self.state_mgr.load_state(pid)
            result = await scheduler.run_pipeline(
                self.stages, state, ProgressTracker(), saved.context
            )
            await self.state_mgr.save_state(pid, PipelineState("completed", result))
            return {"idea": result.idea or "", "video": result.output or ""}

        return await asyncio.gather(*(single() for _ in range(count)))

    async def run_multiple_videos_distributed(
        self, count: int, workers: int
    ) -> List[Dict[str, str]]:
        """Run videos across multiple workers and aggregate results."""

        async def batch(n: int) -> List[Dict[str, str]]:
            return await self.run_multiple_videos(n)

        parts = [count // workers + (1 if i < count % workers else 0) for i in range(workers)]
        results = await asyncio.gather(*(batch(p) for p in parts if p))
        merged: List[Dict[str, str]] = []
        for chunk in results:
            merged.extend(chunk)
        return merged

    async def run_music_only(self, prompt: str) -> Dict[str, str]:
        stage = MusicGeneration(self.container["music_generator"])
        ctx = PipelineContext(idea=prompt)
        res = await self.scheduler.run_pipeline(
            [stage], self.state, ProgressTracker(), ctx
        )
        await self.state_mgr.save_state(
            self.pipeline_id, PipelineState("music_generation", res)
        )
        return {"music": res.music_path or ""}


async def run_pipeline(config: Config) -> Dict[str, str]:
    from services.factory import create_services
    from utils.logging_config import setup_logging
    from utils.monitoring import start_metrics_server, start_health_server

    setup_logging()
    start_metrics_server(8000)
    await start_health_server(config, 8001)
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
