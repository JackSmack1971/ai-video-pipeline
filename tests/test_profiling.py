import asyncio
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest

from profiling.app_profiler import ApplicationProfiler, PerformanceReport
from profiling.resource_tracker import ResourceTracker, ResourceSnapshot
from profiling.bottleneck_detector import BottleneckDetector, Bottleneck
from profiling.optimizer import Optimizer


@pytest.mark.asyncio
async def test_application_profiler_report(monkeypatch):
    tracker = ResourceTracker()

    async def fake_collect() -> ResourceSnapshot:
        return ResourceSnapshot(10, 20, 0, 0, 0, 0, 0)

    async def fake_avg() -> ResourceSnapshot:
        return ResourceSnapshot(10, 20, 0, 0, 0, 0, 0)

    monkeypatch.setattr(tracker, "collect_once", fake_collect)
    monkeypatch.setattr(tracker, "average_usage", fake_avg)

    profiler = ApplicationProfiler(tracker, interval=0.01)
    await profiler.profile_pipeline_execution("p1")
    await asyncio.sleep(0.02)
    report = await profiler.generate_performance_report()
    assert isinstance(report, PerformanceReport)
    assert report.cpu == 10
    assert report.memory == 20


@pytest.mark.asyncio
async def test_resource_tracker_collect(monkeypatch):
    monkeypatch.setattr("psutil.cpu_percent", lambda: 5)

    class Mem:
        percent = 15

    monkeypatch.setattr("psutil.virtual_memory", lambda: Mem)

    class Disk:
        read_bytes = 1
        write_bytes = 2

    monkeypatch.setattr("psutil.disk_io_counters", lambda: Disk)

    class Net:
        bytes_sent = 3
        bytes_recv = 4

    monkeypatch.setattr("psutil.net_io_counters", lambda: Net)

    tracker = ResourceTracker()
    snap = await tracker.collect_once()
    assert snap.cpu == 5
    assert snap.memory == 15


@pytest.mark.asyncio
async def test_bottleneck_detection(monkeypatch):
    tracker = ResourceTracker()

    async def fake_avg() -> ResourceSnapshot:
        return ResourceSnapshot(85, 90, 0, 0, 0, 0, 0)

    monkeypatch.setattr(tracker, "average_usage", fake_avg)

    detector = BottleneckDetector(tracker)
    issues = await detector.detect()
    assert any(b.resource == "cpu" for b in issues)
    assert any(b.resource == "memory" for b in issues)


@pytest.mark.asyncio
async def test_optimizer(monkeypatch):
    detector = BottleneckDetector(ResourceTracker())

    async def fake_detect() -> list[Bottleneck]:
        return [
            Bottleneck("cpu", 90, ""),
            Bottleneck("memory", 95, ""),
        ]

    monkeypatch.setattr(detector, "detect", fake_detect)
    optimizer = Optimizer(detector)
    recs = await optimizer.recommend()
    assert len(recs) == 2
