from __future__ import annotations

import os
from typing import Dict

from prometheus_client import Counter, Gauge, Histogram


class MetricsCollector:
    RESPONSE_TIME = Histogram("service_response_seconds", "Service response time", ["service"])
    ERROR_COUNT = Counter("service_errors_total", "Service error count", ["service", "type"])
    QUEUE_DEPTH = Gauge("queue_depth", "Queue depth", ["queue"])
    RESOURCE_USAGE = Gauge("resource_usage_percent", "Resource utilization", ["resource"])
    API_QUOTA = Gauge("api_quota_usage_percent", "API quota usage", ["service"])

    def __init__(self) -> None:
        self.calls: Dict[str, int] = {}
        self.errors: Dict[str, int] = {}

    def observe_response(self, service: str, duration: float) -> None:
        self.calls[service] = self.calls.get(service, 0) + 1
        self.RESPONSE_TIME.labels(service=service).observe(duration)

    def increment_error(self, service: str, err_type: str) -> None:
        self.errors[service] = self.errors.get(service, 0) + 1
        self.ERROR_COUNT.labels(service=service, type=err_type).inc()

    def set_queue_depth(self, queue: str, depth: int) -> None:
        self.QUEUE_DEPTH.labels(queue=queue).set(depth)

    def update_resource_usage(self) -> None:
        cpu = os.getloadavg()[0] * 100
        self.RESOURCE_USAGE.labels(resource="cpu").set(cpu)

    def set_api_quota(self, service: str, used: float, limit: float) -> None:
        if limit:
            percent = used / limit * 100
            self.API_QUOTA.labels(service=service).set(percent)
