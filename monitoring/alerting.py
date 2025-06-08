from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .health_checks import ServiceHealthChecker
from .metrics_collector import MetricsCollector
from .performance_tracker import PerformanceTracker


@dataclass
class Alert:
    service: str
    message: str


class AlertManager:
    def __init__(
        self,
        collector: MetricsCollector,
        checker: ServiceHealthChecker,
        tracker: PerformanceTracker,
    ) -> None:
        self.collector = collector
        self.checker = checker
        self.tracker = tracker

    async def evaluate(self) -> List[Alert]:
        alerts: List[Alert] = []
        health = await self.checker.get_overall_health()
        for h in health.services:
            if not h.healthy:
                alerts.append(Alert(h.service, h.details or "unhealthy"))
        for service, errors in self.collector.errors.items():
            calls = self.collector.calls.get(service, 1)
            if errors / calls > 0.05:
                alerts.append(Alert(service, "error rate high"))
        for service, count in self.collector.calls.items():
            if self.tracker.check_deviation(service, self.collector.RESPONSE_TIME.labels(service=service)._sum.get() / count):
                alerts.append(Alert(service, "response time degraded"))
        return alerts
