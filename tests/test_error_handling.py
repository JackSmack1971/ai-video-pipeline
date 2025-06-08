import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from utils.circuit_breaker import CircuitBreaker
from utils.retry_logic import retry_async
from utils.error_handling import error_middleware, sanitize_message
from exceptions import ServiceError, CircuitBreakerOpenError, SecurityError


@pytest.mark.asyncio
async def test_retry_async_success():
    attempts = 0

    async def task():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("fail")
        return "ok"

    result = await retry_async("op", task, retries=3, timeout=1)
    assert result == "ok" and attempts == 3


@pytest.mark.asyncio
async def test_retry_async_failure():
    async def bad():
        raise ValueError("boom")

    with pytest.raises(ServiceError):
        await retry_async("bad", bad, retries=1, timeout=0.1)


def test_circuit_breaker_open():
    breaker = CircuitBreaker(max_failures=1, reset_timeout=1)

    async def bad():
        raise ValueError()

    with pytest.raises(ValueError):
        asyncio.run(breaker.call(bad))
    with pytest.raises(CircuitBreakerOpenError):
        asyncio.run(breaker.call(lambda: asyncio.sleep(0)))


def test_error_middleware_sanitizes():
    app = FastAPI()
    app.middleware("http")(error_middleware)

    @app.get("/secure")
    async def secure():
        raise SecurityError("token=123")

    client = TestClient(app)
    resp = client.get("/secure")
    assert resp.status_code == 400
    assert "***" in resp.json()["detail"]
    assert "X-Correlation-ID" in resp.headers

