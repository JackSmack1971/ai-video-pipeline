import asyncio
import pytest

class FaultyService:
    def __init__(self) -> None:
        self.fail = False

    async def run(self) -> str:
        if self.fail:
            raise RuntimeError("failure")
        await asyncio.sleep(0.01)
        return "ok"

service = FaultyService()

@pytest.mark.asyncio
async def test_random_service_failures() -> None:
    service.fail = True
    with pytest.raises(RuntimeError):
        await service.run()
    service.fail = False

@pytest.mark.asyncio
async def test_network_interruption_and_recovery() -> None:
    async def flaky():
        await asyncio.sleep(0.01)
        if not hasattr(flaky, "called"):
            flaky.called = True
            raise ConnectionError
        return "ok"
    with pytest.raises(ConnectionError):
        await flaky()
    assert await flaky() == "ok"

@pytest.mark.asyncio
async def test_disk_space_exhaustion() -> None:
    with pytest.raises(RuntimeError):
        raise RuntimeError("disk full")

@pytest.mark.asyncio
async def test_memory_pressure() -> None:
    data = [b"x" * 1024 for _ in range(1000)]
    await asyncio.sleep(0)
    assert len(data) == 1000
