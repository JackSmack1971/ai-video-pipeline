from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterable


async def stream_copy(src: Path, dest: Path, chunk_size: int = 65536) -> None:
    loop = asyncio.get_event_loop()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as r, open(dest, "wb") as w:
        while True:
            chunk = await loop.run_in_executor(None, r.read, chunk_size)
            if not chunk:
                break
            await loop.run_in_executor(None, w.write, chunk)


async def stream_write(dest: Path, data: AsyncIterable[bytes], chunk_size: int = 65536) -> None:
    loop = asyncio.get_event_loop()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as w:
        async for chunk in data:
            await loop.run_in_executor(None, w.write, chunk)
