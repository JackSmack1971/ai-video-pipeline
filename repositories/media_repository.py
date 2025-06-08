from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class MediaRepository(ABC):
    """Abstract storage for media files."""

    @abstractmethod
    async def save_media(self, path: str, data: AsyncIterator[bytes]) -> str:
        """Persist media data and return the storage path."""

    @abstractmethod
    async def load_media(self, path: str) -> AsyncIterator[bytes]:
        """Stream media data from storage."""
