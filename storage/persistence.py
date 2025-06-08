import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from typing import Any, TYPE_CHECKING
from exceptions import FileOperationError

if TYPE_CHECKING:  # pragma: no cover
    from pipeline.stages import PipelineContext
else:
    PipelineContext = Any


@dataclass
class PipelineState:
    stage: str
    context: PipelineContext


class PipelineStateManager:
    def __init__(self, base_dir: str = "state") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_state(self, pipeline_id: str, state: PipelineState) -> None:
        path = self.base_dir / f"{pipeline_id}.json"
        data = json.dumps({"stage": state.stage, "context": asdict(state.context)})
        try:
            await asyncio.to_thread(path.write_text, data)
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc

    async def load_state(self, pipeline_id: str) -> PipelineState:
        path = self.base_dir / f"{pipeline_id}.json"
        if not path.exists():
            from pipeline.stages import PipelineContext as PC
            return PipelineState("", PC())
        try:
            data = await asyncio.to_thread(path.read_text)
            payload = json.loads(data)
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc
        from pipeline.stages import PipelineContext as PC
        ctx = PC(**payload.get("context", {}))
        return PipelineState(payload.get("stage", ""), ctx)

    async def list_recoverable_pipelines(self) -> List[str]:
        return [p.stem for p in self.base_dir.glob("*.json")]

    async def cleanup_old_states(self, max_age: timedelta) -> None:
        now = datetime.utcnow()
        for p in self.base_dir.glob("*.json"):
            try:
                mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
                if now - mtime > max_age:
                    await asyncio.to_thread(p.unlink)
            except OSError:
                continue
