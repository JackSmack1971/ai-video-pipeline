from __future__ import annotations

import asyncio

from .schemas import Config, PipelineConfig, SecurityConfig
from .loader import (
    load_config as _load_config,
    reload_config as _reload_config,
    load_pipeline_config as _load_pipeline_config,
    get_config as _get_config,
    enable_sighup_reload,
)
from .validator import ConfigError, validate_keys


async def load_config_async(env: str | None = None) -> Config:
    return await _load_config(env)


def load_config(env: str | None = None) -> Config:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(load_config_async(env))
    raise RuntimeError("Use load_config_async inside async context")


async def reload_config_async() -> Config:
    return await _reload_config()


def reload_config() -> Config:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(reload_config_async())
    raise RuntimeError("Use reload_config_async inside async context")


async def load_pipeline_config_async(env: str | None = None) -> PipelineConfig:
    return await _load_pipeline_config(env)


def load_pipeline_config(env: str | None = None) -> PipelineConfig:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(load_pipeline_config_async(env))
    raise RuntimeError("Use load_pipeline_config_async inside async context")


def get_config() -> Config:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_get_config())
    raise RuntimeError("Use load_config_async or get_pipeline_config inside async context")


def get_pipeline_config() -> PipelineConfig:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(load_pipeline_config_async())
    raise RuntimeError("Use load_pipeline_config_async inside async context")

__all__ = [
    "Config",
    "PipelineConfig",
    "SecurityConfig",
    "load_config",
    "reload_config",
    "load_pipeline_config",
    "get_config",
    "get_pipeline_config",
    "enable_sighup_reload",
    "ConfigError",
    "validate_keys",
]
