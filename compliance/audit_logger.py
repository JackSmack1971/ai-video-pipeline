from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from analytics.usage_tracker import TimeRange
from security.auth_manager import User
from utils.validation import validate_file_path
from exceptions import FileOperationError


@dataclass
class AuditEntry:
    timestamp: datetime
    user_id: str
    action: str
    details: Dict[str, Any]


@dataclass
class AuditReport:
    entries: List[AuditEntry]


class AuditLogger:
    def __init__(self, log_file: str) -> None:
        path = validate_file_path(Path(log_file), [Path('logs')])
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._lock = asyncio.Lock()

    @property
    def path(self) -> Path:
        return self._path

    async def _append(self, entry: Dict[str, Any]) -> None:
        try:
            async with self._lock:
                await asyncio.to_thread(
                    self._path.open('a').write,
                    json.dumps(entry) + '\n'
                )
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc

    async def log_user_action(self, user: User, action: str, details: Dict[str, Any]) -> None:
        entry = {
            't': datetime.utcnow().isoformat(),
            'user': user.id,
            'action': action,
            'details': details,
        }
        await self._append(entry)

    async def log_data_access(self, user: User, data_type: str, purpose: str) -> None:
        await self.log_user_action(user, f'access_{data_type}', {'purpose': purpose})

    async def log_system_event(self, event_type: str, details: Dict[str, Any]) -> None:
        entry = {
            't': datetime.utcnow().isoformat(),
            'event': event_type,
            'details': details,
        }
        await self._append(entry)

    async def generate_audit_report(self, time_range: TimeRange) -> AuditReport:
        try:
            content = await asyncio.to_thread(self._path.read_text)
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc
        entries: List[AuditEntry] = []
        for line in content.splitlines():
            data = json.loads(line)
            ts = datetime.fromisoformat(data.get('t'))
            if time_range.start <= ts <= time_range.end:
                entries.append(
                    AuditEntry(
                        timestamp=ts,
                        user_id=data.get('user', ''),
                        action=data.get('action', data.get('event', '')),
                        details=data.get('details', {}),
                    )
                )
        return AuditReport(entries)
