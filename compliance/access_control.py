from __future__ import annotations

from typing import Dict, Set

from security.auth_manager import User


class AccessControl:
    def __init__(self) -> None:
        self._roles: Dict[str, Set[str]] = {}

    async def assign_role(self, user_id: str, role: str) -> None:
        self._roles.setdefault(user_id, set()).add(role)

    async def revoke_role(self, user_id: str, role: str) -> None:
        if user_id in self._roles:
            self._roles[user_id].discard(role)

    async def check_access(self, user: User, role: str) -> bool:
        return role in self._roles.get(user.id, set())

    async def list_roles(self, user_id: str) -> Set[str]:
        return self._roles.get(user_id, set()).copy()
