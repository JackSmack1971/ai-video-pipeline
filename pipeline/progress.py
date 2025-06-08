from __future__ import annotations

import asyncio
from typing import Callable, Dict, List, Any


class ProgressTracker:
    def __init__(self) -> None:
        self.callbacks: List[Callable[[str, float], Any]] = []
        self._progress: Dict[str, float] = {}

    def register(self, callback: Callable[[str, float], Any]) -> None:
        self.callbacks.append(callback)

    async def update(self, stage: str, value: float) -> None:
        self._progress[stage] = value
        for cb in self.callbacks:
            await asyncio.to_thread(cb, stage, value)

    @property
    def progress(self) -> Dict[str, float]:
        return self._progress.copy()
