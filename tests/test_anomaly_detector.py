from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from monitoring.anomaly_detector import AnomalyDetector


def test_anomaly_detection():
    detector = AnomalyDetector(window=5, threshold=2)
    for i in range(5):
        assert not detector.add_point(float(i))
    assert detector.add_point(20.0)

