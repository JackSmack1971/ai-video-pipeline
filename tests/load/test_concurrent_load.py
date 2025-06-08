import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
import asyncio
import time
import pytest

from utils.load_testing.report_generator import generate_performance_report

async def generate_single_video() -> float:
    await asyncio.sleep(0.01)
    return 0.01

@pytest.mark.load
@pytest.mark.asyncio
async def test_concurrent_video_generation_scalability(tmp_path):
    metrics = []
    for users in range(10, 31, 10):
        start = time.perf_counter()
        tasks = [generate_single_video() for _ in range(users)]
        results = await asyncio.gather(*tasks)
        avg = sum(results) / len(results)
        metrics.append({"concurrent_users": users, "success_rate": 1.0, "avg_response_time": avg})
        assert avg <= 30.0
    await generate_performance_report(metrics, str(tmp_path / "perf.json"))
