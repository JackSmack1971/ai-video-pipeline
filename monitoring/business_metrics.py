from __future__ import annotations

from prometheus_client import Gauge, Histogram

class BusinessMetrics:
    COST = Histogram("video_cost_usd", "Cost per video generation")
    USER_SATISFACTION = Gauge("user_satisfaction_score", "User satisfaction rating")
    SUCCESS_RATE = Gauge("generation_success_rate", "Success rate of generation")
    EFFICIENCY = Gauge("cost_per_successful_generation", "Cost per successful generation")
    API_USAGE = Gauge("api_quota_utilization_percent", "API quota utilization")

    def record_cost(self, amount: float) -> None:
        self.COST.observe(amount)

    def set_satisfaction(self, score: float) -> None:
        self.USER_SATISFACTION.set(score)

    def set_success_rate(self, rate: float) -> None:
        self.SUCCESS_RATE.set(rate)

    def set_efficiency(self, value: float) -> None:
        self.EFFICIENCY.set(value)

    def set_api_usage(self, value: float) -> None:
        self.API_USAGE.set(value)
