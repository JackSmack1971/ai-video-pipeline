from pathlib import Path
import sys
import asyncio
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from observability.slo_monitoring import SLOMonitor


@pytest.mark.asyncio
async def test_slo_monitor():
    monitor = SLOMonitor()
    result = await monitor.check_slo_compliance()
    assert "availability" in result
