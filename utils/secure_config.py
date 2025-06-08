from __future__ import annotations

from pathlib import Path
from typing import Dict

from cryptography.fernet import Fernet, InvalidToken

class SecureConfigError(Exception):
    """Raised when secure configuration fails."""
    pass

_KEY_PATH = Path.home() / ".pipeline" / "key.enc"


def _ensure_key() -> str:
    """Load or create encryption key stored on disk with 0o600 perms."""
    try:
        if _KEY_PATH.exists():
            return _KEY_PATH.read_text().strip()
        _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key().decode()
        _KEY_PATH.write_text(key)
        _KEY_PATH.chmod(0o600)
        return key
    except OSError as exc:
        raise SecureConfigError("Failed to access encryption key") from exc


def _fernet() -> Fernet:
    return Fernet(_ensure_key().encode())


def encrypt_value(value: str) -> str:
    """Encrypt a configuration value."""
    if not isinstance(value, str):
        raise SecureConfigError("Value must be a string")
    return _fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    """Decrypt an encrypted value if prefixed with ENC:"""
    if not value.startswith("ENC:"):
        return value
    token = value[4:]
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise SecureConfigError("Invalid encrypted value") from exc


def rotate_keys(values: Dict[str, str]) -> Dict[str, str]:
    """Rotate encryption key and re-encrypt provided values."""
    old_key = _fernet()
    new_key = Fernet.generate_key()
    try:
        _KEY_PATH.write_text(new_key.decode())
        _KEY_PATH.chmod(0o600)
    except OSError as exc:
        raise SecureConfigError("Failed to rotate key") from exc
    f_new = Fernet(new_key)
    result: Dict[str, str] = {}
    for k, val in values.items():
        token = val[4:] if val.startswith("ENC:") else val
        try:
            plain = old_key.decrypt(token.encode()).decode()
        except InvalidToken as exc:
            if val.startswith("ENC:"):
                raise SecureConfigError("Invalid encrypted value during rotation") from exc
            plain = val
        result[k] = f"ENC:{f_new.encrypt(plain.encode()).decode()}"
    return result
