import sys
import asyncio
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.security_test_utils import authenticate_request


@pytest.mark.load
@pytest.mark.asyncio
async def test_stress_authentication() -> None:
    async def attempt() -> None:
        with pytest.raises(Exception):
            await authenticate_request("bad-key")
    tasks = [attempt() for _ in range(200)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert len(results) == 200
    assert all(r is None for r in results)
