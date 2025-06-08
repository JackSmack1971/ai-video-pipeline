import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
import random; random.seed(0)
import asyncio
import pytest

from utils.load_testing.chaos_simulator import simulated_service_failures


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_api_service_failures():
    cfg = {"service": "dummy", "failure_rate": 0.5}
    success = 0
    for _ in range(10):
        try:
            async with simulated_service_failures(cfg):
                await asyncio.sleep(0)
                success += 1
        except RuntimeError:
            pass
    assert success >= 5
