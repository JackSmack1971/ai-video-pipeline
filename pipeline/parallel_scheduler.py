from __future__ import annotations

import asyncio
from typing import Iterable, List, Dict, Set

from .stages import PipelineStage, PipelineContext


class StageExecutionError(Exception):
    """Raised when a pipeline stage fails."""


class ParallelPipelineScheduler:
    def __init__(self, concurrency: int = 4) -> None:
        self.sem = asyncio.Semaphore(concurrency)

    def _dependency_graph(
        self, stages: Iterable[PipelineStage]
    ) -> List[List[PipelineStage]]:
        stage_map: Dict[str, PipelineStage] = {s.name: s for s in stages}
        in_deg: Dict[str, int] = {
            s.name: len(getattr(s, "requires", set())) for s in stages
        }
        deps: Dict[str, List[str]] = {s.name: [] for s in stages}
        for s in stages:
            for dep in getattr(s, "requires", set()):
                deps.setdefault(dep, []).append(s.name)
        queue = [n for n, d in in_deg.items() if d == 0]
        groups: List[List[PipelineStage]] = []
        while queue:
            groups.append([stage_map[n] for n in queue])
            next_q: List[str] = []
            for n in queue:
                for child in deps.get(n, []):
                    in_deg[child] -= 1
                    if in_deg[child] == 0:
                        next_q.append(child)
            queue = next_q
        if any(d > 0 for d in in_deg.values()):
            raise ValueError("Cyclic dependencies detected")
        return groups

    async def _run_stage(
        self, stage: PipelineStage, ctx: PipelineContext
    ) -> PipelineContext:
        async with self.sem:
            try:
                copy = PipelineContext(**vars(ctx))
                return await stage.execute(copy)
            except Exception as exc:
                raise StageExecutionError(stage.name) from exc

    @staticmethod
    def _merge(results: Iterable[PipelineContext], ctx: PipelineContext) -> PipelineContext:
        for res in results:
            for key, value in vars(res).items():
                if value is not None:
                    setattr(ctx, key, value)
        return ctx

    async def execute_pipeline(
        self, stages: Iterable[PipelineStage], ctx: PipelineContext | None = None
    ) -> PipelineContext:
        ctx = ctx or PipelineContext()
        groups = self._dependency_graph(list(stages))
        for group in groups:
            tasks = [self._run_stage(s, ctx) for s in group]
            results = await asyncio.gather(*tasks)
            ctx = self._merge(results, ctx)
        return ctx
