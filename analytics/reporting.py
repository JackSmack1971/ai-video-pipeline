from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from .cost_analyzer import CostAnalyzer
from .usage_tracker import UsageTracker, TimeRange
from .quality_metrics import QualityMetrics


class ReportingService:
    def __init__(self, usage: UsageTracker, costs: CostAnalyzer, quality: QualityMetrics) -> None:
        self.usage = usage
        self.costs = costs
        self.quality = quality

    async def generate_summary(self, time_range: TimeRange) -> str:
        usage = await self.usage.get_usage_patterns(time_range)
        total_cost = await self.costs.get_total_cost(time_range)
        data: Dict[str, Any] = asdict(usage)
        data["total_cost"] = total_cost
        return json.dumps(data)
