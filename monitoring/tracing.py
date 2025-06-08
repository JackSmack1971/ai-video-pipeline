from __future__ import annotations

from opentelemetry import trace

_tracer = trace.get_tracer(__name__)

class PipelineTracer:
    def trace_video_generation(self, pipeline_id: str):
        """Create trace for complete video generation pipeline"""
        return _tracer.start_as_current_span(
            "video_generation", attributes={"pipeline_id": pipeline_id}
        )

    def trace_api_call(self, service: str, operation: str):
        """Trace individual API calls with timing and metadata"""
        return _tracer.start_as_current_span(
            "api_call", attributes={"service": service, "operation": operation}
        )
