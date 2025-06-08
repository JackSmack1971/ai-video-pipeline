from pathlib import Path
import sys
import asyncio
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from observability.predictive_alerting import PredictiveAlerting


class DummyStore:
    async def get_metric_history(self, metric: str, days: int, resolution: str):
        return []


@pytest.mark.asyncio
async def test_predictive_alerting():
    alerting = PredictiveAlerting(DummyStore())
    await alerting.analyze_performance_trends()
