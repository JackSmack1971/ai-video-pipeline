import importlib.util
import os
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "secure_config", Path("config/secure_config.py")
)
secure_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(secure_config)
SecureConfig = secure_config.SecureConfig


def test_get_secret_from_docker(tmp_path, monkeypatch):
    secret_name = "sample_secret"
    secrets_dir = Path("/run/secrets")
    secrets_dir.mkdir(parents=True, exist_ok=True)
    secret_file = secrets_dir / secret_name
    secret_file.write_text("value")
    try:
        assert SecureConfig.get_secret(secret_name) == "value"
    finally:
        secret_file.unlink()


def test_get_secret_from_env_file(tmp_path, monkeypatch):
    secret_name = "file_secret"
    secret_file = tmp_path / "s.txt"
    secret_file.write_text("val")
    monkeypatch.setenv(f"{secret_name.upper()}_FILE", str(secret_file))
    assert SecureConfig.get_secret(secret_name) == "val"


def test_get_secret_from_env(monkeypatch):
    secret_name = "env_secret"
    monkeypatch.setenv(secret_name.upper(), "envval")
    assert SecureConfig.get_secret(secret_name) == "envval"


def test_get_required_secret_missing(monkeypatch):
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    with pytest.raises(ValueError):
        SecureConfig.get_required_secret("missing_secret")
