import asyncio
from pathlib import Path
from typing import AsyncIterable, Iterable, Optional

from utils.monitoring import FILE_PROCESS_TIME

from .validation import validate_file_path
from exceptions import FileOperationError
from storage.integrity_checker import IntegrityChecker
from optimization.streaming_io import stream_write
from optimization.memory_manager import MemoryManager
from caching.cache_manager import CacheManager

integrity = IntegrityChecker()

BASE_DIR = Path.cwd()

_cache_manager: Optional[CacheManager] = None


def set_cache_manager(manager: CacheManager) -> None:
    global _cache_manager
    _cache_manager = manager


def _resolve(path: str, allowed: Iterable[str]) -> Path:
    return validate_file_path(Path(path), [BASE_DIR / d for d in allowed])


async def read_file(path: str) -> str:
    file_path = _resolve(path, ["prompts", "image", "video", "music", "voice", "."])  # allow reading from these
    loop = asyncio.get_event_loop()
    start = loop.time()
    try:
        data = await asyncio.to_thread(file_path.read_text)
        checksum_file = file_path.parent / ".checksums.json"
        checks = await integrity.load_checksums(checksum_file)
        expected = checks.get(file_path.name)
        if expected and not await integrity.verify(file_path, expected):
            raise FileOperationError("Checksum mismatch")
        return data
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc
    finally:
        FILE_PROCESS_TIME.labels(operation="read_file").observe(loop.time() - start)


async def read_cached_file(path: str) -> str:
    if _cache_manager:
        cached = await _cache_manager.get_cached_image(path)
        if cached:
            return await read_file(cached)
    return await read_file(path)


async def save_file(path: str, data: bytes) -> None:
    file_path = _resolve(path, ["image", "video", "music", "voice"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    start = loop.time()
    try:
        await asyncio.to_thread(file_path.write_bytes, data)
        checksum = await integrity.sha256(file_path)
        await integrity.update_checksum_file(
            file_path.parent / ".checksums.json", file_path.name, checksum
        )
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc
    finally:
        FILE_PROCESS_TIME.labels(operation="save_file").observe(loop.time() - start)


async def save_cached_file(path: str, data: bytes) -> None:
    await save_file(path, data)
    if _cache_manager:
        await _cache_manager.cache_generation_result(path, {"file": path})


async def read_file_stream(path: str, chunk_size: int = 65536) -> AsyncIterable[bytes]:
    file_path = _resolve(path, ["prompts", "image", "video", "music", "voice", "."])
    async for chunk in MemoryManager.stream_file(file_path, chunk_size):
        yield chunk


async def save_file_stream(path: str, data: AsyncIterable[bytes]) -> None:
    file_path = _resolve(path, ["image", "video", "music", "voice"])
    await stream_write(file_path, data)
