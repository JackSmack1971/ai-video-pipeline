from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError
from .schemas import Config, PipelineConfig, SecurityConfig, ComplianceConfig
from .validator import ConfigError, validate_keys

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs"
_cached: Optional[Config] = None
_mtime: float = 0.0


def _parse_value(val: str) -> Any:
    try:
        return json.loads(val)
    except Exception:
        return val


def _decrypt(val: str) -> str:
    if not val.startswith("ENC:"):
        return val
    key = os.getenv("PIPELINE_SECRET_KEY")
    if not key:
        raise ConfigError("Missing PIPELINE_SECRET_KEY")
    from cryptography.fernet import Fernet, InvalidToken

    try:
        f = Fernet(key.encode())
        return f.decrypt(val[4:].encode()).decode()
    except InvalidToken as exc:
        raise ConfigError("Failed to decrypt config value") from exc


async def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = await asyncio.to_thread(path.read_text)
    return json.loads(data)


async def load_pipeline_config(env: Optional[str] = None) -> PipelineConfig:
    env = env or os.getenv("PIPELINE_ENV", "dev")
    base = await _read_json(_CONFIG_PATH / "base.json")
    override = await _read_json(_CONFIG_PATH / f"{env}.json")
    if "pipeline" in base:
        base = base["pipeline"]
    if "pipeline" in override:
        override = override["pipeline"]
    data = {**base, **override}
    prefix = "PIPELINE_PIPELINE_"
    overrides = {
        k[len(prefix):].lower(): _parse_value(v)
        for k, v in os.environ.items()
        if k.startswith(prefix)
    }
    data.update(overrides)
    try:
        return PipelineConfig(**data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


async def load_config(env: Optional[str] = None) -> Config:
    global _cached, _mtime
    env = env or os.getenv("PIPELINE_ENV", "dev")
    pipeline = await load_pipeline_config(env)
    top = {
        k[len("PIPELINE_"):].lower(): _parse_value(v)
        for k, v in os.environ.items()
        if k.startswith("PIPELINE_") and not k.startswith("PIPELINE_PIPELINE_")
    }
    keys = {
        "openai_api_key": _decrypt(os.getenv("OPENAI_API_KEY", top.get("openai_api_key", ""))),
        "sonauto_api_key": _decrypt(os.getenv("SONAUTO_API_KEY", top.get("sonauto_api_key", ""))),
        "replicate_api_key": _decrypt(os.getenv("REPLICATE_API_KEY", top.get("replicate_api_key", ""))),
    }
    security = SecurityConfig(
        token_expiry=int(os.getenv("SECURITY_TOKEN_EXPIRY", "3600")),
        rate_limit=int(os.getenv("SECURITY_RATE_LIMIT", "60")),
    )
    compliance = ComplianceConfig(
        audit_log=os.getenv("COMPLIANCE_AUDIT_LOG", "logs/audit.log"),
        retention_days=int(os.getenv("COMPLIANCE_RETENTION_DAYS", "30")),
    )
    api_timeout = int(os.getenv("API_TIMEOUT", str(top.get("api_timeout", 60))))
    try:
        cfg = Config(
            **keys,
            api_timeout=api_timeout,
            pipeline=pipeline,
            security=security,
            compliance=compliance,
        )
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
    validate_keys(cfg)
    return cfg


async def get_config() -> Config:
    global _cached, _mtime
    env = os.getenv("PIPELINE_ENV", "dev")
    path = _CONFIG_PATH / f"{env}.json"
    mtime = path.stat().st_mtime if path.exists() else 0.0
    if _cached is None or mtime != _mtime:
        _cached = await load_config(env)
        _mtime = mtime
    return _cached


async def reload_config() -> Config:
    old = _cached
    new = await load_config()
    if old and old != new:
        old_d = old.__dict__
        new_d = new.__dict__
        logging.info(
            "Config updated: %s",
            {
                k: (old_d.get(k), new_d.get(k))
                for k in new_d
                if old_d.get(k) != new_d.get(k)
            },
        )
    globals()["_cached"] = new
    return new


def enable_sighup_reload() -> None:
    loop = asyncio.get_event_loop()

    def handler(_: int, __: Any) -> None:
        loop.create_task(reload_config())

    signal.signal(signal.SIGHUP, handler)
