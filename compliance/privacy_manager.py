from __future__ import annotations

from typing import Any, Dict


class PrivacyManager:
    def __init__(self, retention_days: int = 30) -> None:
        self._consents: Dict[str, bool] = {}
        self._data: Dict[str, Dict[str, Any]] = {}
        self._retention_days = retention_days

    async def set_consent(self, user_id: str, consent: bool) -> None:
        self._consents[user_id] = consent

    async def get_consent(self, user_id: str) -> bool:
        return self._consents.get(user_id, False)

    async def store_personal_data(self, user_id: str, data: Dict[str, Any]) -> None:
        self._data[user_id] = data

    async def erase_user_data(self, user_id: str) -> None:
        self._consents.pop(user_id, None)
        self._data.pop(user_id, None)

    async def handle_access_request(self, user_id: str) -> Dict[str, Any]:
        return self._data.get(user_id, {}).copy()

    async def validate_transfer(self, destination: str) -> bool:
        allowed = {"eu", "us"}
        return destination.lower() in allowed
