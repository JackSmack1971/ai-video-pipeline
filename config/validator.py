import re
from .schemas import Config
from .errors import ConfigError

_PATTERNS = {
    "openai_api_key": r"^sk-[A-Za-z0-9]{20,}$",
    "sonauto_api_key": r"^sa-[A-Za-z0-9]{20,}$",
    "replicate_api_key": r"^r8_[A-Za-z0-9]{20,}$",
}


def validate_keys(cfg: Config) -> None:
    for name, pattern in _PATTERNS.items():
        value = getattr(cfg, name)
        if not value or not re.match(pattern, value):
            raise ConfigError(f"Invalid format for {name.upper()}")
