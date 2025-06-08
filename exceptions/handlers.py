from __future__ import annotations

import logging


def handle_exception(exc: Exception) -> None:
    logging.getLogger("pipeline").exception("Unhandled error: %s", exc)


def fallback_response(service: str) -> str:
    if service == "openai":
        return "Service unavailable"
    return ""
