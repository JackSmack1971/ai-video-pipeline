import sys
import asyncio
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.security_test_utils import authenticate_request, process_memory_usage


@pytest.mark.load
class TestSecurityUnderLoad:
    @pytest.mark.asyncio
    async def test_concurrent_authentication_attempts(self) -> None:
        async def attempt_auth() -> None:
            with pytest.raises(Exception):
                await authenticate_request("invalid-key")

        initial = process_memory_usage()
        tasks = [attempt_auth() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(r is None for r in results)
        assert process_memory_usage() < initial * 1.2
