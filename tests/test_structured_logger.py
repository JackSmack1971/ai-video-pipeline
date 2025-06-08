from pathlib import Path
import logging
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from monitoring.structured_logger import set_correlation_id, get_logger
from utils.logging_config import setup_logging


def test_structured_logging(caplog):
    setup_logging(logging.INFO)
    set_correlation_id("abc123")
    logger = get_logger("test")
    from utils.logging_config import JsonFormatter
    record = logger.logger.makeRecord(
        "test", logging.INFO, __file__, 0, "hello", None, None, None, {"key": "secret"}
    )
    formatted = JsonFormatter().format(record)
    assert '"correlation_id": "abc123"' in formatted
    assert '"key": "***"' in formatted
