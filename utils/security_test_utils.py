from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from exceptions import ConfigurationError, FileOperationError, SecurityError
from security.auth_manager import AuthManager
from utils.validation import validate_file_path

_API_KEY_PATTERNS = {
    'openai': r'^sk-[A-Za-z0-9]{20,}$',
    'sonauto': r'^sa-[A-Za-z0-9]{20,}$',
    'replicate': r'^r8_[A-Za-z0-9]{20,}$',
}


def validate_api_key(key: str) -> None:
    """Validate API keys against known patterns."""
    if not isinstance(key, str) or not key:
        raise ConfigurationError("API key missing")
    for pattern in _API_KEY_PATTERNS.values():
        if re.fullmatch(pattern, key):
            return
    raise ConfigurationError("Invalid API key format")


async def authenticate_request(api_key: str) -> None:
    """Authenticate a request using AuthManager."""
    auth = AuthManager()
    user = await auth.authenticate_api_key(api_key)
    if not user:
        raise SecurityError("Unauthorized")


def process_memory_usage() -> float:
    """Return current process memory usage as percentage of total."""
    try:
        rss = 0
        with open('/proc/self/status') as fh:
            for line in fh:
                if line.startswith('VmRSS:'):
                    rss = int(line.split()[1])
                    break
        with open('/proc/meminfo') as fh:
            meminfo = {line.split(':')[0]: int(line.split()[1]) for line in fh}
        total = meminfo.get('MemTotal', 1)
        return rss / total * 100
    except Exception:
        return 0.0
