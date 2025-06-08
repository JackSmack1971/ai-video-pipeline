from __future__ import annotations

from collections import deque
from statistics import mean, stdev
from typing import Deque

class AnomalyDetector:
    def __init__(self, window: int = 50, threshold: float = 3.0) -> None:
        self.window = window
        self.threshold = threshold
        self.data: Deque[float] = deque(maxlen=window)

    def add_point(self, value: float) -> bool:
        previous = list(self.data)
        self.data.append(value)
        if len(previous) < self.window:
            return False
        mu = mean(previous)
        sigma = stdev(previous)
        if sigma == 0:
            return False
        return abs(value - mu) > self.threshold * sigma
