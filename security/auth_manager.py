from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class User:
    id: str
    roles: list[str]


class AuthError(Exception):
    pass


class AuthManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, User] = {}
        self._users = self._load_users()

    def _load_users(self) -> Dict[str, User]:
        data = os.getenv("API_USERS", "{}")
        try:
            info = json.loads(data)
            return {k: User(**v) for k, v in info.items()}
        except Exception as exc:
            raise AuthError("Invalid user config") from exc

    async def authenticate_api_key(self, api_key: str) -> Optional[User]:
        return self._users.get(api_key)

    async def authorize_operation(self, user: User, operation: str) -> bool:
        return "admin" in user.roles or operation in user.roles

    async def generate_secure_token(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = user
        return token

    async def validate_token(self, token: str) -> Optional[User]:
        return self._tokens.get(token)
