from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from services.interfaces import IdeaGeneratorInterface, MediaGeneratorInterface


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


class PipelineStage(ABC):
    name: str

    @abstractmethod
    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        ...

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return True

    async def cleanup(self, ctx: PipelineContext) -> None:  # pragma: no cover
        pass


class IdeaGeneration(PipelineStage):
    name = "idea_generation"

    def __init__(self, service: IdeaGeneratorInterface) -> None:
        self.service = service

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        data = await self.service.generate()
        ctx.idea = data["idea"]
        ctx.prompt = data["prompt"]
        return ctx


class ImageGeneration(PipelineStage):
    name = "image_generation"

    def __init__(self, service: MediaGeneratorInterface) -> None:
        self.service = service

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return bool(ctx.prompt)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not await self.validate_inputs(ctx):
            raise ValueError("prompt required")
        ctx.image_path = await self.service.generate(ctx.prompt)
        return ctx


class VideoGeneration(PipelineStage):
    name = "video_generation"

    def __init__(self, service: MediaGeneratorInterface) -> None:
        self.service = service

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return bool(ctx.prompt and ctx.image_path)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not await self.validate_inputs(ctx):
            raise ValueError("image and prompt required")
        ctx.video_path = await self.service.generate(
            ctx.prompt, image_path=ctx.image_path
        )
        return ctx


class MusicGeneration(PipelineStage):
    name = "music_generation"

    def __init__(self, service: MediaGeneratorInterface) -> None:
        self.service = service

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return bool(ctx.idea)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not await self.validate_inputs(ctx):
            raise ValueError("idea required")
        ctx.music_path = await self.service.generate(ctx.idea)
        return ctx


class VoiceGeneration(PipelineStage):
    name = "voice_generation"

    def __init__(self, service: MediaGeneratorInterface) -> None:
        self.service = service

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return bool(ctx.idea)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not await self.validate_inputs(ctx):
            raise ValueError("idea required")
        ctx.voice = await self.service.generate(ctx.idea)
        return ctx


class Composition(PipelineStage):
    name = "composition"

    def __init__(self, duration: int) -> None:
        self.duration = duration

    async def validate_inputs(self, ctx: PipelineContext) -> bool:
        return bool(ctx.video_path and ctx.music_path)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not await self.validate_inputs(ctx):
            raise ValueError("missing media")
        voice_file = ctx.voice["filename"] if ctx.voice else None
        from . import merge_video_audio

        ctx.output = await merge_video_audio(
            ctx.video_path,
            ctx.music_path,
            voice_file,
            "final_output.mp4",
            self.duration,
        )
        return ctx
