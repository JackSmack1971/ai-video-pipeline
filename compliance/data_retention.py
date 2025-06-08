from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from utils.validation import validate_file_path
from exceptions import FileOperationError


class DataRetentionManager:
    def __init__(self, log_file: str, days: int) -> None:
        path = validate_file_path(Path(log_file), [Path('logs')])
        self._path = path
        self._days = days

    async def enforce_policy(self) -> None:
        cutoff = datetime.utcnow() - timedelta(days=self._days)
        try:
            content = await asyncio.to_thread(self._path.read_text)
        except OSError:
            return
        keep: List[str] = []
        for line in content.splitlines():
            data = json.loads(line)
            ts = datetime.fromisoformat(data.get('t'))
            if ts >= cutoff:
                keep.append(line)
        try:
            await asyncio.to_thread(self._path.write_text, '\n'.join(keep))
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc
