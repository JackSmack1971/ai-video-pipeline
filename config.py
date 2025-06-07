import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic import ValidationError

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

@pydantic_dataclass
class PipelineConfig:
    max_stored_ideas: int = 6
    default_video_duration: int = 10
    api_timeout: int = 300
    retry_attempts: int = 3
    history_file: str = "last_ideas.json"
    video_batch_small: int = 3
    video_batch_large: int = 5
    music_only_prompt: str = "ambient soundtrack"

@pydantic_dataclass
class Config:
    openai_api_key: str
    sonauto_api_key: str
    replicate_api_key: str
    api_timeout: int = 60
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)


def _validate_key(name: str, value: str) -> str:
    if not value:
        raise ConfigError(f"Missing environment variable: {name}")
    if not re.match(r"^[A-Za-z0-9-_.]{20,}$", value):
        raise ConfigError(f"Invalid format for {name}")
    return value


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}") from exc


def load_pipeline_config(env: Optional[str] = None) -> PipelineConfig:
    base_dir = Path(__file__).resolve().parent / "configs"
    env = env or os.getenv("PIPELINE_ENV", "dev")
    base = _load_json(base_dir / "base.json")
    override = _load_json(base_dir / f"{env}.json")
    data = {**base, **override}
    try:
        return PipelineConfig(**data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


_cached_pipeline: Optional[PipelineConfig] = None
_cached_mtime: float = 0.0


def get_pipeline_config() -> PipelineConfig:
    global _cached_pipeline, _cached_mtime
    path = Path(__file__).resolve().parent / "configs" / f"{os.getenv('PIPELINE_ENV', 'dev')}.json"
    mtime = path.stat().st_mtime if path.exists() else 0.0
    if _cached_pipeline is None or mtime != _cached_mtime:
        _cached_pipeline = load_pipeline_config()
        _cached_mtime = mtime
    return _cached_pipeline

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
    pipeline_cfg = get_pipeline_config()
    return Config(openai_key, sonauto_key, replicate_key, timeout, pipeline_cfg)
