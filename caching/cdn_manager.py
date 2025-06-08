from __future__ import annotations

import os
from typing import Optional

import aiohttp


class CDNManager:
    """Upload and invalidate files on a CDN."""

    def __init__(self, config: Optional[object] = None) -> None:
        self.endpoint = os.getenv("CDN_ENDPOINT", "")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def upload_file(self, path: str) -> None:
        if not self.endpoint:
            return
        session = await self._get_session()
        try:
            with open(path, "rb") as f:
                await session.put(f"{self.endpoint}/{os.path.basename(path)}", data=f)
        except Exception:
            pass

    async def invalidate(self, filename: str) -> None:
        if not self.endpoint:
            return
        session = await self._get_session()
        try:
            await session.delete(f"{self.endpoint}/{filename}")
        except Exception:
            pass
