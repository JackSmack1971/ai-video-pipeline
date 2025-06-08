from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import pytest

from monitoring.metrics_collector import MetricsCollector
from monitoring.performance_tracker import PerformanceTracker
from monitoring.alerting import AlertManager, Alert
from monitoring.health_checks import ServiceHealthChecker, HealthStatus, SystemHealthStatus
from config import Config


class DummyChecker(ServiceHealthChecker):
    async def get_overall_health(self) -> SystemHealthStatus:
        return SystemHealthStatus([HealthStatus("openai", True)])


@pytest.mark.asyncio
async def test_alerting_on_errors():
    collector = MetricsCollector()
    tracker = PerformanceTracker()
    checker = DummyChecker(Config("k1", "k2", "k3", 60))
    manager = AlertManager(collector, checker, tracker)
    collector.observe_response("svc", 1.0)
    collector.increment_error("svc", "fail")
    alerts = await manager.evaluate()
    assert any(a.message == "error rate high" for a in alerts)


def test_performance_tracker():
    tracker = PerformanceTracker()
    assert not tracker.check_deviation("svc", 1.0)
    assert not tracker.check_deviation("svc", 1.2)
    assert tracker.check_deviation("svc", 2.0)
