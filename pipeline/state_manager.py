from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Tuple

from .stages import PipelineContext


class StateManager:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    async def load(self) -> Tuple[str, PipelineContext]:
        if not self.path.exists():
            return "", PipelineContext()
        data = await asyncio.to_thread(self.path.read_text)
        payload = json.loads(data)
        ctx = PipelineContext(**payload.get("context", {}))
        return payload.get("stage", ""), ctx

    async def save(self, stage: str, ctx: PipelineContext) -> None:
        data = json.dumps({"stage": stage, "context": asdict(ctx)})
        await asyncio.to_thread(self.path.write_text, data)

    async def clear(self) -> None:
        if self.path.exists():
            await asyncio.to_thread(self.path.unlink)
