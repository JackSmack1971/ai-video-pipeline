from __future__ import annotations

import asyncio
from typing import Iterable

from .stages import PipelineStage, PipelineContext
from .state_manager import StateManager
from .progress import ProgressTracker


class PipelineScheduler:
    def __init__(self, concurrency: int = 1) -> None:
        self.sem = asyncio.Semaphore(concurrency)

    async def run_pipeline(
        self,
        stages: Iterable[PipelineStage],
        state: StateManager,
        progress: ProgressTracker,
        ctx: PipelineContext | None = None,
    ) -> PipelineContext:
        async with self.sem:
            last_stage, saved = await state.load()
            ctx = ctx or saved
            resume = bool(last_stage)
            started = False
            for stage in stages:
                if resume and not started:
                    if stage.name == last_stage:
                        started = True
                    continue
                await progress.update(stage.name, 0.0)
                ctx = await stage.execute(ctx)
                await state.save(stage.name, ctx)
                await progress.update(stage.name, 1.0)
            await state.clear()
            return ctx
