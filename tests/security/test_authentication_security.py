import sys
import time
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.security_test_utils import validate_api_key
from exceptions import ConfigurationError


@pytest.mark.security
class TestAuthenticationSecurity:
    @pytest.mark.asyncio
    async def test_api_key_timing_attacks(self) -> None:
        correct_key = "sk-correct-key-12345"
        attack_keys = [
            "sk-wrong-key-123456",
            "sk-corr",
            "sk-correct-key-12346",
            "",
            "invalid-format",
        ]
        for attack_key in attack_keys:
            start = time.perf_counter()
            with pytest.raises(ConfigurationError):
                validate_api_key(attack_key)
            duration = time.perf_counter() - start
            assert duration <= 0.01
