import asyncio
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.api import api_call_with_retry
from exceptions import APIError, NetworkError


@pytest.mark.asyncio
async def test_api_call_success():
    async def call():
        return "ok"
    result = await api_call_with_retry("test", call, max_retries=1, timeout=1)
    assert result == "ok"


@pytest.mark.asyncio
async def test_api_call_timeout():
    async def call():
        await asyncio.sleep(2)
    with pytest.raises(NetworkError):
        await api_call_with_retry("timeout", call, max_retries=1, timeout=1)


@pytest.mark.asyncio
async def test_api_call_failure():
    async def call():
        raise ValueError("boom")
    with pytest.raises(APIError):
        await api_call_with_retry("fail", call, max_retries=1, timeout=1)
