import asyncio
import hashlib
import json
from pathlib import Path
from typing import Dict

from exceptions import FileOperationError


class IntegrityChecker:
    async def sha256(self, path: Path) -> str:
        try:
            data = await asyncio.to_thread(path.read_bytes)
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc
        return hashlib.sha256(data).hexdigest()

    async def verify(self, path: Path, checksum: str) -> bool:
        return await self.sha256(path) == checksum

    async def update_checksum_file(self, file: Path, name: str, checksum: str) -> None:
        if file.exists():
            try:
                content = await asyncio.to_thread(file.read_text)
                data = json.loads(content)
            except OSError:
                data = {}
        else:
            data = {}
        data[name] = checksum
        try:
            await asyncio.to_thread(file.write_text, json.dumps(data))
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc

    async def load_checksums(self, file: Path) -> Dict[str, str]:
        if not file.exists():
            return {}
        try:
            content = await asyncio.to_thread(file.read_text)
            return json.loads(content)
        except OSError as exc:
            raise FileOperationError(str(exc)) from exc
