from __future__ import annotations

import time
from prometheus_client import Counter, Gauge, Histogram


class BusinessMetricsCollector:
    """Track business-specific metrics for video generation pipeline."""

    def __init__(self) -> None:
        self.metrics = {
            "videos_generated_total": Counter(
                "videos_generated_total", ["quality", "duration"]
            ),
            "generation_cost_dollars": Histogram(
                "generation_cost_dollars", ["service"]
            ),
            "user_satisfaction_score": Histogram(
                "user_satisfaction_score", buckets=[1, 2, 3, 4, 5]
            ),
            "pipeline_stage_duration": Histogram(
                "pipeline_stage_duration_seconds", ["stage", "status"]
            ),
            "resource_utilization": Gauge(
                "resource_utilization_percent", ["resource_type"]
            ),
            "api_cost_per_request": Histogram(
                "api_cost_per_request_dollars", ["service"]
            ),
            "output_quality_score": Histogram(
                "output_quality_score", ["content_type"]
            ),
            "generation_retry_count": Counter(
                "generation_retry_count", ["service", "reason"]
            ),
            "user_feedback_rating": Counter(
                "user_feedback_rating", ["rating", "content_type"]
            ),
        }

    async def track_video_generation(self, context) -> None:
        start_time = time.time()
        with context.tracer.start_as_current_span("video_generation") as span:
            span.set_attribute("user_id", context.user_id)
            span.set_attribute("video_duration", context.video_duration)
            try:
                result = await context.execute()
                self.metrics["videos_generated_total"].labels(
                    quality=result.quality, duration=context.video_duration
                ).inc()
                total_cost = sum(s.cost for s in result.service_costs)
                self.metrics["generation_cost_dollars"].observe(total_cost)
            except Exception as exc:  # pragma: no cover - example
                span.record_exception(exc)
                self.metrics["generation_retry_count"].labels(
                    service=context.current_service, reason=type(exc).__name__
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                self.metrics["pipeline_stage_duration"].labels(
                    stage="complete_generation",
                    status="success" if context.success else "failure",
                ).observe(duration)
