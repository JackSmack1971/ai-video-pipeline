from __future__ import annotations

from typing import AsyncIterator, Dict

from ..media_repository import MediaRepository


class InMemoryMediaRepository(MediaRepository):
    """Simple in-memory media storage for testing."""

    def __init__(self) -> None:
        self._store: Dict[str, bytes] = {}

    async def save_media(self, path: str, data: AsyncIterator[bytes]) -> str:
        buf = bytearray()
        async for chunk in data:
            buf.extend(chunk)
        self._store[path] = bytes(buf)
        return path

    async def load_media(self, path: str) -> AsyncIterator[bytes]:
        if path in self._store:
            yield self._store[path]
        else:
            yield b""
