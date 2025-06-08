from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from monitoring.business_metrics import BusinessMetrics


def test_business_metrics():
    metrics = BusinessMetrics()
    metrics.record_cost(1.0)
    metrics.set_satisfaction(0.5)
    metrics.set_success_rate(0.9)
    metrics.set_efficiency(0.1)
    metrics.set_api_usage(70.0)
    assert metrics.COST._sum.get() >= 1.0
    assert metrics.USER_SATISFACTION._value.get() == 0.5

