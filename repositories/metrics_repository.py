from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class MetricsRepository(ABC):
    """Abstraction for metrics collection."""

    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        """Store a metric value with tags."""
