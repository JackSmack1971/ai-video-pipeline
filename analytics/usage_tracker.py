from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class GenerationRequest:
    job_id: str
    params: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GenerationResult:
    job_id: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TimeRange:
    start: datetime
    end: datetime


@dataclass
class UsageReport:
    total: int
    completed: int
    failed: int


@dataclass
class UserProfile:
    user_id: str
    request_count: int


class UsageTracker:
    def __init__(self) -> None:
        self._requests: List[GenerationRequest] = []
        self._results: List[GenerationResult] = []

    async def track_generation_request(self, request: GenerationRequest) -> None:
        self._requests.append(request)

    async def track_generation_completion(self, result: GenerationResult) -> None:
        self._results.append(result)

    async def get_usage_patterns(self, time_range: TimeRange) -> UsageReport:
        reqs = [r for r in self._requests if time_range.start <= r.timestamp <= time_range.end]
        res = [r for r in self._results if time_range.start <= r.timestamp <= time_range.end]
        completed = sum(1 for r in res if r.success)
        failed = sum(1 for r in res if not r.success)
        return UsageReport(total=len(reqs), completed=completed, failed=failed)

    async def identify_power_users(self) -> List[UserProfile]:
        counts: Dict[str, int] = {}
        for r in self._requests:
            uid = r.params.get("user_id", "unknown")
            counts[uid] = counts.get(uid, 0) + 1
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [UserProfile(user_id=u, request_count=c) for u, c in top]
