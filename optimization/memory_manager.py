from __future__ import annotations

import asyncio
import gc
import mmap
from collections import deque
from pathlib import Path
from typing import AsyncGenerator


class MemoryManager:
    """Manage temporary buffers and stream large files."""

    _pool: deque[bytearray] = deque()

    @classmethod
    async def get_buffer(cls, size: int) -> bytearray:
        for _ in range(len(cls._pool)):
            buf = cls._pool.pop()
            if len(buf) >= size:
                return buf
            cls._pool.appendleft(buf)
        return bytearray(size)

    @classmethod
    def release_buffer(cls, buf: bytearray) -> None:
        cls._pool.append(buf)
        gc.collect()

    @staticmethod
    async def stream_file(path: Path, chunk_size: int = 65536) -> AsyncGenerator[bytes, None]:
        loop = asyncio.get_event_loop()
        with open(path, "rb") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                while True:
                    chunk = await loop.run_in_executor(None, mm.read, chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                mm.close()
