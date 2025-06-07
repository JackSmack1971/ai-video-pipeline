from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import web
from prometheus_client import Counter, Histogram, start_http_server

API_RESPONSE_TIME = Histogram(
    "api_response_time_seconds", "API response times", ["operation"]
)
FILE_PROCESS_TIME = Histogram(
    "file_processing_seconds", "File processing durations", ["operation"]
)
PIPELINE_SUCCESS = Counter("pipeline_success_total", "Successful pipeline runs")
PIPELINE_FAILURE = Counter("pipeline_failure_total", "Failed pipeline runs")


async def start_health_server(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/health", lambda request: web.json_response({"status": "ok"}))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner


def start_metrics_server(port: int) -> None:
    start_http_server(port)

