from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class QualityRecord:
    service: str
    success: bool
    resolution: int
    duration: int
    feedback: int | None = None


class QualityMetrics:
    def __init__(self) -> None:
        self._records: List[QualityRecord] = []

    async def record_result(
        self, service: str, success: bool, resolution: int, duration: int, feedback: int | None = None
    ) -> None:
        self._records.append(QualityRecord(service, success, resolution, duration, feedback))

    async def get_success_rate(self, service: str) -> float:
        items = [r for r in self._records if r.service == service]
        if not items:
            return 0.0
        return sum(1 for r in items if r.success) / len(items)

    async def analyze_feedback(self) -> Dict[str, float]:
        scores: Dict[str, List[int]] = defaultdict(list)
        for r in self._records:
            if r.feedback is not None:
                scores[r.service].append(r.feedback)
        return {k: sum(v) / len(v) for k, v in scores.items() if v}
