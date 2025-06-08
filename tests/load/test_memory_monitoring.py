import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
import asyncio
import pytest

from utils.load_testing.performance_monitor import get_memory_usage


@pytest.mark.resource_monitoring
@pytest.mark.asyncio
async def test_memory_leak_detection():
    start = get_memory_usage()
    baseline = start
    growth = []
    for i in range(100):
        _ = bytearray(1024)
        if i % 10 == 0:
            mem = get_memory_usage()
            growth.append(mem - baseline)
            if len(growth) > 5 and all(a > b for a, b in zip(growth[-5:], growth[-6:-1])):
                pytest.fail("Potential memory leak")
    final = get_memory_usage()
    inc = (final - start) / start * 100 if start else 0
    assert inc < 20
