import sys
from pathlib import Path as _Path
import asyncio

sys.path.append(str(_Path(__file__).resolve().parents[1]))

import pytest

from security.auth_manager import AuthManager, User
from security.input_validator import InputValidator
from security.crypto_manager import CryptoManager


@pytest.mark.asyncio
async def test_auth_manager_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_USERS', '{"k":{"id":"u","roles":["admin"]}}')
    auth = AuthManager()
    user = await auth.authenticate_api_key('k')
    assert user and user.id == 'u'
    token = await auth.generate_secure_token(user)
    assert await auth.validate_token(token) == user


@pytest.mark.asyncio
async def test_input_validator() -> None:
    text = await InputValidator.sanitize_text('<b>x</b>')
    assert '&lt;b&gt;x' in text
    assert not InputValidator.too_many_requests('tester')


@pytest.mark.asyncio
async def test_crypto_manager_roundtrip() -> None:
    cm = CryptoManager()
    data = b'secret'
    enc = await cm.encrypt(data)
    dec = await cm.decrypt(enc)
    assert dec == data
    assert await cm.hash_bytes(data)
