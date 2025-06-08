from __future__ import annotations

import html
import time
from typing import Any, Dict

from exceptions import InputValidationError


class InputValidator:
    MAX_SIZE = 2048
    RATE_LIMIT = 60
    _hits: Dict[str, int] = {}

    @classmethod
    async def sanitize_text(cls, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            raise InputValidationError("Text required")
        return html.escape(text)[: cls.MAX_SIZE]

    @classmethod
    async def validate_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if len(str(data)) > cls.MAX_SIZE:
            raise InputValidationError("Payload too large")
        return data

    @classmethod
    def too_many_requests(cls, ident: str) -> bool:
        window = int(time.time() // 60)
        key = f"{ident}:{window}"
        cls._hits[key] = cls._hits.get(key, 0) + 1
        return cls._hits[key] > cls.RATE_LIMIT
