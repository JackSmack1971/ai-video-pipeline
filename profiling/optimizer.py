from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .bottleneck_detector import BottleneckDetector, Bottleneck


@dataclass
class OptimizationRecommendation:
    message: str


class Optimizer:
    def __init__(self, detector: BottleneckDetector) -> None:
        self.detector = detector

    async def recommend(self) -> List[OptimizationRecommendation]:
        bottlenecks = await self.detector.detect()
        recs: List[OptimizationRecommendation] = []
        for b in bottlenecks:
            if b.resource == "cpu":
                recs.append(OptimizationRecommendation("use concurrency or vectorization"))
            elif b.resource == "memory":
                recs.append(OptimizationRecommendation("free unused objects and optimize data formats"))
            elif b.resource == "cpu_regression":
                recs.append(OptimizationRecommendation("investigate recent commits for performance issues"))
        return recs
