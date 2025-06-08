from __future__ import annotations

from typing import AsyncIterator

from exceptions import FileOperationError
from utils import file_operations

from ..media_repository import MediaRepository


class LocalMediaRepository(MediaRepository):
    """Store media files on the local filesystem."""

    async def save_media(self, path: str, data: AsyncIterator[bytes]) -> str:
        async def _writer() -> AsyncIterator[bytes]:
            async for chunk in data:
                yield chunk

        try:
            await file_operations.save_file_stream(path, _writer())
            return path
        except FileOperationError:
            raise
        except Exception as exc:
            raise FileOperationError(str(exc)) from exc

    async def load_media(self, path: str) -> AsyncIterator[bytes]:
        try:
            async for chunk in file_operations.read_file_stream(path):
                yield chunk
        except FileOperationError:
            raise
        except Exception as exc:
            raise FileOperationError(str(exc)) from exc
