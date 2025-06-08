from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .resource_tracker import ResourceTracker, ResourceSnapshot


@dataclass
class Bottleneck:
    resource: str
    value: float
    suggestion: str


class BottleneckDetector:
    def __init__(self, tracker: ResourceTracker) -> None:
        self.tracker = tracker
        self.baseline: ResourceSnapshot | None = None

    async def detect(self) -> List[Bottleneck]:
        avg = await self.tracker.average_usage()
        issues: List[Bottleneck] = []
        if avg.cpu > 80:
            issues.append(Bottleneck("cpu", avg.cpu, "optimize CPU intensive code"))
        if avg.memory > 80:
            issues.append(Bottleneck("memory", avg.memory, "reduce memory usage"))
        if self.baseline and avg.cpu > self.baseline.cpu * 1.5:
            issues.append(Bottleneck("cpu_regression", avg.cpu, "check recent changes"))
        self.baseline = avg
        return issues
