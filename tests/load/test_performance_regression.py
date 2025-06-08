import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from monitoring.performance_tracker import PerformanceTracker


def test_performance_regression_detection():
    tracker = PerformanceTracker()
    assert not tracker.check_deviation("svc", 1.0)
    tracker.baseline["svc"] = 1.0
    assert tracker.check_deviation("svc", 2.0)
