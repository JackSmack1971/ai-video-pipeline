from __future__ import annotations

import os
from hashlib import sha256
from typing import Optional
from cryptography.fernet import Fernet


class CryptoManager:
    def __init__(self, key: Optional[str] = None) -> None:
        self._key = key or os.getenv("PIPELINE_SECRET_KEY") or Fernet.generate_key().decode()
        self._fernet = Fernet(self._key.encode())

    async def encrypt(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    async def decrypt(self, token: bytes) -> bytes:
        return self._fernet.decrypt(token)

    async def hash_bytes(self, data: bytes) -> str:
        return sha256(data).hexdigest()

    @property
    def key(self) -> str:
        return self._key
