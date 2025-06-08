from __future__ import annotations

import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class Tracing:
    """Configure OpenTelemetry distributed tracing."""

    def __init__(self) -> None:
        self.tracer = self._setup_tracer()

    def _setup_tracer(self) -> trace.Tracer:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "14268")),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        return trace.get_tracer(__name__)
