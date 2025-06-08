from pathlib import Path
import sys
import asyncio
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from observability.health_monitoring import HealthMonitor
from monitoring.health_checks import ServiceHealthChecker, SystemHealthStatus, HealthStatus


class DummyChecker(ServiceHealthChecker):
    async def get_overall_health(self) -> SystemHealthStatus:
        return SystemHealthStatus([HealthStatus("svc", False, "down")])


healed = []

def healer(service: str) -> None:
    healed.append(service)


@pytest.mark.asyncio
async def test_health_monitor():
    monitor = HealthMonitor(DummyChecker(None), healer)
    await monitor.check_and_heal()
    assert "svc" in healed
