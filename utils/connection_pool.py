from __future__ import annotations

import aiohttp
from typing import Dict, Tuple

_sessions: Dict[Tuple[str, int], aiohttp.ClientSession] = {}


async def get_session(base_url: str, timeout: int = 60) -> aiohttp.ClientSession:
    """Return or create a pooled HTTP session."""
    key = (base_url, timeout)
    session = _sessions.get(key)
    if session is None or session.closed:
        connector = aiohttp.TCPConnector(limit=20, keepalive_timeout=30)
        _sessions[key] = aiohttp.ClientSession(
            base_url=base_url,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=timeout),
        )
        session = _sessions[key]
    return session


async def close_all() -> None:
    for session in list(_sessions.values()):
        if not session.closed:
            await session.close()
    _sessions.clear()
