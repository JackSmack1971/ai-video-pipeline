from __future__ import annotations

from typing import Callable

from monitoring.health_checks import ServiceHealthChecker


class HealthMonitor:
    """Automated health checking and self-healing."""

    def __init__(self, checker: ServiceHealthChecker, healer: Callable[[str], None]):
        self.checker = checker
        self.healer = healer

    async def check_and_heal(self) -> None:
        status = await self.checker.get_overall_health()
        for svc in status.services:
            if not svc.healthy:
                self.healer(svc.service)
