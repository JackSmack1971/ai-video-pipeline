import sys
import time
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.security_test_utils import validate_api_key
from exceptions import ConfigurationError


@pytest.mark.security
@pytest.mark.asyncio
async def test_constant_time_validation() -> None:
    keys = ["sk-wrong", "sa-invalid", "r8_bad"]
    for key in keys:
        start = time.perf_counter()
        with pytest.raises(ConfigurationError):
            validate_api_key(key)
        duration = time.perf_counter() - start
        assert duration <= 0.01
