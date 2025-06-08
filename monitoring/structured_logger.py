from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Dict

correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

class StructuredLogger(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: Dict[str, Any]):
        extra = self.extra.copy()
        cid = correlation_id.get()
        if cid:
            extra["correlation_id"] = cid
        kwargs.setdefault("extra", extra)
        return msg, kwargs

def set_correlation_id(cid: str) -> None:
    correlation_id.set(cid)

def get_logger(name: str) -> StructuredLogger:
    base = logging.getLogger(name)
    return StructuredLogger(base, {})
