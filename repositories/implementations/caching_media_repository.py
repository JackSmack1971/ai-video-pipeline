from __future__ import annotations

from typing import AsyncIterator, Dict

from ..media_repository import MediaRepository


class CachingMediaRepository(MediaRepository):
    """Cache decorator for another MediaRepository."""

    def __init__(self, repo: MediaRepository) -> None:
        self._repo = repo
        self._cache: Dict[str, bytes] = {}

    async def save_media(self, path: str, data: AsyncIterator[bytes]) -> str:
        buf = bytearray()
        async for chunk in data:
            buf.extend(chunk)
        self._cache[path] = bytes(buf)
        async def _reader() -> AsyncIterator[bytes]:
            yield self._cache[path]
        await self._repo.save_media(path, _reader())
        return path

    async def load_media(self, path: str) -> AsyncIterator[bytes]:
        if path not in self._cache:
            chunks = []
            async for chunk in self._repo.load_media(path):
                chunks.append(chunk)
            self._cache[path] = b"".join(chunks)
        yield self._cache[path]
