from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterable

from optimization.memory_manager import MemoryManager


async def stream_write(dest: Path, data: AsyncIterable[bytes], chunk_size: int = 65536) -> None:
    """Write data to file asynchronously using buffered chunks."""
    loop = asyncio.get_event_loop()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as w:
        async for chunk in data:
            await loop.run_in_executor(None, w.write, chunk)


async def stream_copy(src: Path, dest: Path, chunk_size: int = 65536) -> None:
    """Copy file contents asynchronously."""
    async def _reader() -> AsyncIterable[bytes]:
        async for c in MemoryManager.stream_file(src, chunk_size):
            yield c
    await stream_write(dest, _reader(), chunk_size)
