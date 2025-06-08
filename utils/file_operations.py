import asyncio
from pathlib import Path
from typing import Iterable

from utils.monitoring import FILE_PROCESS_TIME

from .validation import validate_file_path
from exceptions import FileOperationError

BASE_DIR = Path.cwd()


def _resolve(path: str, allowed: Iterable[str]) -> Path:
    return validate_file_path(Path(path), [BASE_DIR / d for d in allowed])


async def read_file(path: str) -> str:
    file_path = _resolve(path, ["prompts", "image", "video", "music", "voice", "."])  # allow reading from these
    loop = asyncio.get_event_loop()
    start = loop.time()
    try:
        return await asyncio.to_thread(file_path.read_text)
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc
    finally:
        FILE_PROCESS_TIME.labels(operation="read_file").observe(loop.time() - start)


async def save_file(path: str, data: bytes) -> None:
    file_path = _resolve(path, ["image", "video", "music", "voice"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    start = loop.time()
    try:
        await asyncio.to_thread(file_path.write_bytes, data)
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc
    finally:
        FILE_PROCESS_TIME.labels(operation="save_file").observe(loop.time() - start)
