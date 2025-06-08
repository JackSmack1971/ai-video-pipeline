from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class SecuritySettings:
    token_expiry: int = 3600
    rate_limit: int = 60


def load_security_config() -> SecuritySettings:
    return SecuritySettings(
        token_expiry=int(os.getenv("SECURITY_TOKEN_EXPIRY", "3600")),
        rate_limit=int(os.getenv("SECURITY_RATE_LIMIT", "60")),
    )
