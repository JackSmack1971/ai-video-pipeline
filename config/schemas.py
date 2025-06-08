from __future__ import annotations

from dataclasses import field
from pydantic.dataclasses import dataclass
from pydantic import Field, model_validator
from .errors import ConfigError

@dataclass
class PipelineConfig:
    max_stored_ideas: int = Field(6, ge=1, le=100)
    default_video_duration: int = Field(10, ge=1, le=60)
    api_timeout: int = Field(300, ge=30, le=600)
    retry_attempts: int = Field(3, ge=1, le=10)
    history_file: str = "last_ideas.json"
    video_batch_small: int = Field(3, ge=1, le=10)
    video_batch_large: int = Field(5, ge=1, le=10)
    music_only_prompt: str = "ambient soundtrack"

    @model_validator(mode="after")
    def check_values(cls, values: "PipelineConfig") -> "PipelineConfig":
        if values.video_batch_large < values.video_batch_small:
            raise ConfigError("video_batch_large must be >= video_batch_small")
        if not 1 <= values.default_video_duration <= 60:
            raise ConfigError("default_video_duration must be between 1 and 60")
        if not 1 <= values.video_batch_small <= 10:
            raise ConfigError("video_batch_small must be between 1 and 10")
        if not 1 <= values.video_batch_large <= 10:
            raise ConfigError("video_batch_large must be between 1 and 10")
        if not 30 <= values.api_timeout <= 600:
            raise ConfigError("api_timeout must be between 30 and 600")
        return values


@dataclass
class SecurityConfig:
    token_expiry: int = Field(3600, ge=60, le=86400)
    rate_limit: int = Field(60, ge=1, le=1000)


@dataclass
class Config:
    openai_api_key: str
    sonauto_api_key: str
    replicate_api_key: str
    api_timeout: int = Field(60, ge=30, le=600)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
