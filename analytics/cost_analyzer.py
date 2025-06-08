from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .usage_tracker import TimeRange


@dataclass
class CostRecord:
    job_id: str
    service: str
    cost: float
    timestamp: datetime


class CostAnalyzer:
    def __init__(self) -> None:
        self._records: List[CostRecord] = []

    async def record_cost(self, job_id: str, service: str, cost: float) -> None:
        self._records.append(CostRecord(job_id, service, cost, datetime.utcnow()))

    async def get_cost_breakdown(self, job_id: str) -> Dict[str, float]:
        breakdown: Dict[str, float] = {}
        for r in self._records:
            if r.job_id == job_id:
                breakdown[r.service] = breakdown.get(r.service, 0.0) + r.cost
        return breakdown

    async def get_total_cost(self, time_range: TimeRange) -> float:
        return sum(
            r.cost for r in self._records if time_range.start <= r.timestamp <= time_range.end
        )

    async def recommend_optimizations(self) -> List[str]:
        totals: Dict[str, float] = defaultdict(float)
        for r in self._records:
            totals[r.service] += r.cost
        if not totals:
            return []
        expensive = max(totals.items(), key=lambda x: x[1])[0]
        return [f"Consider optimizing usage of {expensive}"]
