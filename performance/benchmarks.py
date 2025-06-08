from __future__ import annotations

import asyncio
import time
from typing import List

from pipeline.parallel_scheduler import ParallelPipelineScheduler
from pipeline.stages import PipelineContext, PipelineStage


class DummyStage(PipelineStage):
    def __init__(self, name: str, delay: float, requires: set[str] | None = None) -> None:
        self.name = name
        self.delay = delay
        self.requires = requires or set()

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        await asyncio.sleep(self.delay)
        ctx.meta[self.name] = True
        return ctx


async def run_benchmark() -> float:
    stages: List[PipelineStage] = [
        DummyStage("a", 0.1),
        DummyStage("b", 0.1, {"a"}),
        DummyStage("c", 0.1, {"a"}),
        DummyStage("d", 0.1, {"b", "c"}),
    ]
    scheduler = ParallelPipelineScheduler()
    start = time.perf_counter()
    await scheduler.execute_pipeline(stages, PipelineContext())
    return time.perf_counter() - start


if __name__ == "__main__":
    result = asyncio.run(run_benchmark())
    print(f"Execution time: {result:.2f}s")
