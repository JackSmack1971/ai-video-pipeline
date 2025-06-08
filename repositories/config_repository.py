from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ConfigRepository(ABC):
    """Abstraction for configuration storage."""

    @abstractmethod
    async def get_config(self, key: str) -> Optional[str]:
        """Retrieve configuration value."""

    @abstractmethod
    async def set_config(self, key: str, value: str) -> None:
        """Persist configuration value."""
