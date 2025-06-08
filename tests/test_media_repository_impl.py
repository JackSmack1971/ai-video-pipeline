import asyncio
from typing import AsyncIterator

import pytest

from repositories.implementations.in_memory_media_repository import InMemoryMediaRepository
from repositories.implementations.caching_media_repository import CachingMediaRepository


async def _aiter(data: bytes) -> AsyncIterator[bytes]:
    yield data


@pytest.mark.asyncio
async def test_in_memory_roundtrip() -> None:
    repo = InMemoryMediaRepository()
    await repo.save_media("a.txt", _aiter(b"hi"))
    chunks = [c async for c in repo.load_media("a.txt")]
    assert b"".join(chunks) == b"hi"


@pytest.mark.asyncio
async def test_caching_repository() -> None:
    base = InMemoryMediaRepository()
    repo = CachingMediaRepository(base)
    await repo.save_media("b.txt", _aiter(b"x"))
    # first load goes through base
    data1 = [c async for c in repo.load_media("b.txt")][0]
    assert data1 == b"x"
    base._store["b.txt"] = b"y"
    # second load uses cache
    data2 = [c async for c in repo.load_media("b.txt")][0]
    assert data2 == b"x"
