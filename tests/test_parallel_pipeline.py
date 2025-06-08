import asyncio
from pathlib import Path as _Path
import importlib.util
import types
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set

BASE = _Path(__file__).resolve().parents[1]

# Stub pipeline.stages to satisfy imports
stages_stub = types.ModuleType("pipeline.stages")

@dataclass
class PipelineContext:
    idea: Optional[str] = None
    prompt: Optional[str] = None
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    music_path: Optional[str] = None
    voice: Optional[Dict[str, str]] = None
    output: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

class PipelineStage:
    name: str
    requires: Set[str] = set()

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        raise NotImplementedError

stages_stub.PipelineContext = PipelineContext
stages_stub.PipelineStage = PipelineStage
sys.modules["pipeline.stages"] = stages_stub

# Create package context
pipeline_pkg = types.ModuleType("pipeline")
pipeline_pkg.__path__ = [str(BASE / "pipeline")]
sys.modules.setdefault("pipeline", pipeline_pkg)

spec = importlib.util.spec_from_file_location(
    "pipeline.parallel_scheduler", BASE / "pipeline" / "parallel_scheduler.py"
)
parallel_mod = importlib.util.module_from_spec(spec)
sys.modules["pipeline.parallel_scheduler"] = parallel_mod
spec.loader.exec_module(parallel_mod)
ParallelPipelineScheduler = parallel_mod.ParallelPipelineScheduler

from utils.streaming_io import stream_copy, stream_write
from utils.connection_pool import get_session, close_all
from utils.caching_layer import ResponseCache


class DummyStage(PipelineStage):
    def __init__(self, name: str, requires=None) -> None:
        self.name = name
        self.requires = requires or set()

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        ctx.meta[self.name] = True
        return ctx


@pytest.mark.asyncio
async def test_dependency_grouping() -> None:
    stages = [
        DummyStage("a"),
        DummyStage("b", {"a"}),
        DummyStage("c", {"a"}),
        DummyStage("d", {"b", "c"}),
    ]
    scheduler = ParallelPipelineScheduler()
    groups = scheduler._dependency_graph(stages)
    assert len(groups) == 3
    assert {s.name for s in groups[0]} == {"a"}
    assert {s.name for s in groups[1]} == {"b", "c"}
    assert {s.name for s in groups[2]} == {"d"}


@pytest.mark.asyncio
async def test_execute_pipeline() -> None:
    stages = [
        DummyStage("a"),
        DummyStage("b", {"a"}),
        DummyStage("c", {"a"}),
    ]
    scheduler = ParallelPipelineScheduler()
    ctx = await scheduler.execute_pipeline(stages, PipelineContext())
    assert ctx.meta == {"a": True, "b": True, "c": True}


@pytest.mark.asyncio
async def test_stream_copy(tmp_path: _Path) -> None:
    src = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    async def gen():
        yield b"x"

    await stream_write(src, gen())
    await stream_copy(src, dest)
    assert dest.read_bytes() == b"x"


@pytest.mark.asyncio
async def test_connection_pool_reuse() -> None:
    s1 = await get_session("https://example.com", 5)
    s2 = await get_session("https://example.com", 5)
    assert s1 is s2
    await close_all()


@pytest.mark.asyncio
async def test_response_cache() -> None:
    cache = ResponseCache(ttl=1)

    async def creator() -> str:
        return "value"

    v1 = await cache.get_or_set("k", creator)
    v2 = await cache.get_or_set("k", creator)
    assert v1 == v2
    assert cache.get("k") == "value"
