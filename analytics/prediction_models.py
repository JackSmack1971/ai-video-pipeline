from __future__ import annotations

from typing import List


class LinearPredictor:
    def __init__(self) -> None:
        self._coef = 0.0
        self._intercept = 0.0

    async def train(self, x: List[float], y: List[float]) -> None:
        if len(x) != len(y) or not x:
            return
        n = float(len(x))
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den = sum((xi - mean_x) ** 2 for xi in x) or 1.0
        self._coef = num / den
        self._intercept = mean_y - self._coef * mean_x

    async def predict(self, x: List[float]) -> List[float]:
        return [self._coef * xi + self._intercept for xi in x]
