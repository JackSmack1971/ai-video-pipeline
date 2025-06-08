from __future__ import annotations

from dataclasses import dataclass

@dataclass
class RetryPolicy:
    max_attempts: int
    max_time: int  # seconds

SERVICE_POLICIES = {
    "openai": RetryPolicy(3, 300),
    "replicate": RetryPolicy(5, 300),
    "sonauto": RetryPolicy(3, 300),
}


def get_policy(service: str) -> RetryPolicy:
    return SERVICE_POLICIES.get(service, RetryPolicy(3, 300))
