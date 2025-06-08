import json
import logging
import os
from typing import Any, Dict

from monitoring.structured_logger import correlation_id, StructuredLogger
from compliance.audit_logger import AuditLogger
from config.schemas import ComplianceConfig


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        cid = getattr(record, "correlation_id", None) or correlation_id.get()
        if cid:
            data["correlation_id"] = cid
        for key, value in record.__dict__.items():
            if key not in vars(logging.LogRecord("", "", 0, 0, "", [], None)):
                data[key] = value
        for k in list(data):
            if "key" in k.lower() or "token" in k.lower():
                data[k] = "***"
        return json.dumps(data)


def get_json_logger(name: str) -> StructuredLogger:
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return StructuredLogger(logger, {})


def setup_logging(
    level: int = logging.INFO,
    compliance: ComplianceConfig | None = None,
) -> AuditLogger | None:
    env = os.getenv("LOG_LEVEL")
    if env:
        level = getattr(logging, env.upper(), level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
    audit_logger: AuditLogger | None = None
    if compliance:
        audit_logger = AuditLogger(compliance.audit_log)
        file_handler = logging.FileHandler(audit_logger.path)
        file_handler.setFormatter(JsonFormatter())
        root.addHandler(file_handler)
    return audit_logger
