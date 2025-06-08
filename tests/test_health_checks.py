from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import pytest

from config import Config
from monitoring.health_checks import ServiceHealthChecker, HealthStatus, SystemHealthStatus


class DummyChecker(ServiceHealthChecker):
    async def check_openai_health(self) -> HealthStatus:
        return HealthStatus("openai", True)

    async def check_replicate_health(self) -> HealthStatus:
        return HealthStatus("replicate", True)

    async def check_sonauto_health(self) -> HealthStatus:
        return HealthStatus("sonauto", True)

    async def check_ffmpeg_health(self) -> HealthStatus:
        return HealthStatus("ffmpeg", True)


@pytest.mark.asyncio
async def test_overall_health():
    cfg = Config("k1", "k2", "k3", 60)
    checker = DummyChecker(cfg)
    status = await checker.get_overall_health()
    assert isinstance(status, SystemHealthStatus)
    assert status.healthy
    assert len(status.services) == 4
