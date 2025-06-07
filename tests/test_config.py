import os
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import load_config, ConfigError


def test_load_config_success(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-openai1234567890')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-test-sonauto123456')
    monkeypatch.setenv('REPLICATE_API_KEY', 'rep-test-replicate123456')
    cfg = load_config()
    assert cfg.openai_api_key.startswith('sk-')
    assert cfg.api_timeout == 60


def test_load_config_missing(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-test')
    monkeypatch.setenv('REPLICATE_API_KEY', 'rep-test')
    with pytest.raises(ConfigError):
        load_config()
