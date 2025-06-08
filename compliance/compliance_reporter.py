from __future__ import annotations

from typing import Any, Dict

from analytics.usage_tracker import TimeRange

from .audit_logger import AuditLogger


class ComplianceReporter:
    def __init__(self, logger: AuditLogger) -> None:
        self._logger = logger

    async def generate_gdpr_report(self, time_range: TimeRange) -> Dict[str, Any]:
        report = await self._logger.generate_audit_report(time_range)
        return {"entries": len(report.entries)}

    async def security_dashboard(self) -> Dict[str, Any]:
        return {"status": "ok"}
