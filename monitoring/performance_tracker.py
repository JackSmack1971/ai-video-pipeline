from __future__ import annotations

from typing import Dict


class PerformanceTracker:
    def __init__(self) -> None:
        self.baseline: Dict[str, float] = {}

    def check_deviation(self, service: str, value: float) -> bool:
        base = self.baseline.get(service)
        if base is None:
            self.baseline[service] = value
            return False
        if base == 0:
            return False
        return value > base * 1.5
