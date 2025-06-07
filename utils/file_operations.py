import asyncio
from pathlib import Path
from typing import Iterable

from .validation import validate_file_path
from exceptions import FileOperationError

BASE_DIR = Path.cwd()


def _resolve(path: str, allowed: Iterable[str]) -> Path:
    return validate_file_path(BASE_DIR / path, [BASE_DIR / d for d in allowed])


async def read_file(path: str) -> str:
    file_path = _resolve(path, ["prompts", "image", "video", "music", "voice", "."])  # allow reading from these
    try:
        return await asyncio.to_thread(file_path.read_text)
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc


async def save_file(path: str, data: bytes) -> None:
    file_path = _resolve(path, ["image", "video", "music", "voice"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        await asyncio.to_thread(file_path.write_bytes, data)
    except OSError as exc:
        raise FileOperationError(str(exc)) from exc
