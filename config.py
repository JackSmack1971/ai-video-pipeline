import os
import re
from dataclasses import dataclass

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

@dataclass
class Config:
    openai_api_key: str
    sonauto_api_key: str
    replicate_api_key: str
    api_timeout: int = 60


def _validate_key(name: str, value: str) -> str:
    if not value:
        raise ConfigError(f"Missing environment variable: {name}")
    if not re.match(r"^[A-Za-z0-9-_.]{20,}$", value):
        raise ConfigError(f"Invalid format for {name}")
    return value


def load_config() -> Config:
    """Load and validate configuration from environment variables."""
    openai_key = _validate_key("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    sonauto_key = _validate_key("SONAUTO_API_KEY", os.getenv("SONAUTO_API_KEY"))
    replicate_key = _validate_key("REPLICATE_API_KEY", os.getenv("REPLICATE_API_KEY"))
    timeout_str = os.getenv("API_TIMEOUT", "60")
    try:
        timeout = int(timeout_str)
    except ValueError as exc:
        raise ConfigError("API_TIMEOUT must be an integer") from exc
    return Config(openai_key, sonauto_key, replicate_key, timeout)
