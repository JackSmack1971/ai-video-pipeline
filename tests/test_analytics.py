import asyncio
from datetime import datetime, timedelta

import pytest

from analytics.usage_tracker import UsageTracker, GenerationRequest, GenerationResult, TimeRange
from analytics.cost_analyzer import CostAnalyzer
from analytics.quality_metrics import QualityMetrics
from analytics.prediction_models import LinearPredictor


@pytest.mark.asyncio
async def test_usage_tracker_patterns():
    tracker = UsageTracker()
    now = datetime.utcnow()
    req = GenerationRequest("1", {"user_id": "a"}, now)
    await tracker.track_generation_request(req)
    await tracker.track_generation_completion(GenerationResult("1", True, now))
    rng = TimeRange(now - timedelta(seconds=1), now + timedelta(seconds=1))
    rep = await tracker.get_usage_patterns(rng)
    assert rep.total == 1 and rep.completed == 1


@pytest.mark.asyncio
async def test_cost_analyzer_breakdown():
    analyzer = CostAnalyzer()
    await analyzer.record_cost("1", "openai", 0.5)
    await analyzer.record_cost("1", "replicate", 1.0)
    result = await analyzer.get_cost_breakdown("1")
    assert result["openai"] == 0.5 and result["replicate"] == 1.0


@pytest.mark.asyncio
async def test_quality_metrics_success_rate():
    metrics = QualityMetrics()
    await metrics.record_result("svc", True, 720, 10, feedback=4)
    await metrics.record_result("svc", False, 720, 10)
    rate = await metrics.get_success_rate("svc")
    assert 0 < rate < 1


@pytest.mark.asyncio
async def test_linear_predictor():
    predictor = LinearPredictor()
    await predictor.train([1, 2, 3], [2, 4, 6])
    preds = await predictor.predict([4])
    assert preds[0] == pytest.approx(8.0)
