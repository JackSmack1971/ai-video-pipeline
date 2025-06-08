from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from exceptions import PipelineBaseException, ServiceError, SecurityError
from monitoring.structured_logger import get_logger, set_correlation_id


_SANITIZE_RE = re.compile(r"(key|token|secret)=\S+", re.I)
logger = get_logger(__name__)


def sanitize_message(message: str) -> str:
    return _SANITIZE_RE.sub("***", message)


async def error_middleware(request: Request, call_next):
    cid = str(uuid.uuid4())
    set_correlation_id(cid)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response
    except PipelineBaseException as exc:
        logger.error("handled error", extra={"cid": cid, **exc.context})
        msg = sanitize_message(exc.message)
        code = 400 if isinstance(exc, SecurityError) else 502
        return JSONResponse(
            status_code=code,
            content={"detail": msg, "correlation_id": cid},
            headers={"X-Correlation-ID": cid},
        )
    except Exception as exc:
        logger.exception("unhandled error", extra={"cid": cid})
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "correlation_id": cid},
            headers={"X-Correlation-ID": cid},
        )
