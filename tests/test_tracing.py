import asyncio
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from monitoring.tracing import PipelineTracer


@pytest.mark.asyncio
async def test_tracing_context_manager():
    tracer = PipelineTracer()
    await asyncio.sleep(0)
    # ensure context manager can be used
    with tracer.trace_video_generation("x"):
        with tracer.trace_api_call("svc", "op"):
            assert True

