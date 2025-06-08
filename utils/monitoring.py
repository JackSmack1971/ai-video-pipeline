from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import web
from prometheus_client import Counter, Histogram, start_http_server

from monitoring.metrics_collector import MetricsCollector
from monitoring.performance_tracker import PerformanceTracker
from monitoring.tracing import PipelineTracer
from monitoring.business_metrics import BusinessMetrics
from monitoring.anomaly_detector import AnomalyDetector
from monitoring.structured_logger import get_logger

API_RESPONSE_TIME = Histogram(
    "api_response_time_seconds", "API response times", ["operation"]
)
FILE_PROCESS_TIME = Histogram(
    "file_processing_seconds", "File processing durations", ["operation"]
)
PIPELINE_SUCCESS = Counter("pipeline_success_total", "Successful pipeline runs")
PIPELINE_FAILURE = Counter("pipeline_failure_total", "Failed pipeline runs")

collector = MetricsCollector()
tracker = PerformanceTracker()
tracer = PipelineTracer()
business_metrics = BusinessMetrics()
detector = AnomalyDetector()
logger = get_logger(__name__)
health_checker: Any | None = None
alert_manager: Any | None = None


async def start_health_server(config: Any, port: int) -> web.AppRunner:
    from monitoring.health_checks import ServiceHealthChecker
    from monitoring.alerting import AlertManager

    global health_checker, alert_manager
    health_checker = ServiceHealthChecker(config)
    alert_manager = AlertManager(collector, health_checker, tracker)

    async def handler(_: web.Request) -> web.Response:
        with tracer.trace_api_call("health", "check"):
            status = await health_checker.get_overall_health()
        return web.json_response({"healthy": status.healthy})

    app = web.Application()
    app.router.add_get("/health", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner


def start_metrics_server(port: int) -> None:
    start_http_server(port)
