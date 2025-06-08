import json
import os
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import load_config, reload_config, ConfigError, load_pipeline_config, PipelineConfig


def test_load_config_success(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890')
    cfg = load_config()
    assert cfg.openai_api_key.startswith('sk-')
    assert cfg.api_timeout == 60
    assert cfg.pipeline.max_stored_ideas == 6


def test_load_config_missing(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-test')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_test')
    with pytest.raises(ConfigError):
        load_config()


def test_pipeline_env_override(monkeypatch):
    monkeypatch.setenv('PIPELINE_ENV', 'staging')
    cfg = load_pipeline_config('staging')
    assert cfg.api_timeout == 180


def test_reload_config(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-firstkey1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-firstkey1234567890abcd')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_firstkey1234567890abcd')
    cfg1 = load_config()
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-secondkey1234567890abcd')
    cfg2 = reload_config()
    assert cfg1.openai_api_key != cfg2.openai_api_key


def test_api_timeout_bounds(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890abcd')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890abcd')
    monkeypatch.setenv('API_TIMEOUT', '10')
    with pytest.raises(ConfigError):
        load_config()


def test_pipeline_config_bounds():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PipelineConfig(default_video_duration=0)
    with pytest.raises(ValidationError):
        PipelineConfig(video_batch_large=11)


def test_env_override(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890')
    monkeypatch.setenv('PIPELINE_PIPELINE_MAX_STORED_IDEAS', '9')
    cfg = load_config()
    assert cfg.pipeline.max_stored_ideas == 9


def test_hot_reload(monkeypatch, tmp_path):
    cfg_dir = tmp_path / 'cfg'
    cfg_dir.mkdir()
    (cfg_dir / 'base.json').write_text(json.dumps({'max_stored_ideas': 6}))
    (cfg_dir / 'dev.json').write_text(json.dumps({'max_stored_ideas': 7}))
    monkeypatch.setattr('config.loader._CONFIG_PATH', cfg_dir)
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890')
    monkeypatch.setenv('PIPELINE_ENV', 'dev')
    cfg1 = load_config()
    (cfg_dir / 'dev.json').write_text(json.dumps({'max_stored_ideas': 8}))
    cfg2 = reload_config()
    assert cfg1.pipeline.max_stored_ideas != cfg2.pipeline.max_stored_ideas
