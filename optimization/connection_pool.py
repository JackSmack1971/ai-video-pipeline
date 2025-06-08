from __future__ import annotations

import aiohttp
from typing import Dict

_sessions: Dict[str, aiohttp.ClientSession] = {}


async def get_session(timeout: int) -> aiohttp.ClientSession:
    key = str(timeout)
    session = _sessions.get(key)
    if session is None or session.closed:
        _sessions[key] = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
        session = _sessions[key]
    return session


async def close_all() -> None:
    for session in list(_sessions.values()):
        if not session.closed:
            await session.close()
