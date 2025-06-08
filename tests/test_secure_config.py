import sys
from pathlib import Path as _Path

sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest

from utils import secure_config


@pytest.fixture(autouse=True)
def _tmp_key(monkeypatch, tmp_path):
    key_file = tmp_path / "key.enc"
    monkeypatch.setattr(secure_config, "_KEY_PATH", key_file)
    yield


def test_encrypt_decrypt() -> None:
    text = "secret"
    token = secure_config.encrypt_value(text)
    assert token.startswith("g") or token.startswith("ENC")
    decoded = secure_config.decrypt_value(f"ENC:{token}" if not token.startswith("ENC") else token)
    assert decoded == text


def test_rotate_keys() -> None:
    original = secure_config.encrypt_value("val")
    rotated = secure_config.rotate_keys({"k": original})
    assert "k" in rotated
    assert rotated["k"].startswith("ENC:")
    assert secure_config.decrypt_value(rotated["k"]) == "val"
