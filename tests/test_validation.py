import re
import os
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from utils.validation import (
    sanitize_prompt,
    validate_file_path,
    DEFAULT_PROMPT,
    resolve_path,
)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text())
def test_sanitize_prompt_valid_chars(text: str) -> None:
    assume(text.strip())
    cleaned = sanitize_prompt(text)
    assert cleaned == "" or re.fullmatch(r"[\w\s.,!?'-]+", cleaned)


def test_sanitize_prompt_invalid() -> None:
    assert sanitize_prompt("") == DEFAULT_PROMPT


def test_sanitize_prompt_too_long() -> None:
    long_prompt = "a" * 2001
    assert sanitize_prompt(long_prompt) == "a" * 2000


def test_sanitize_prompt_injection() -> None:
    text = "<script>alert('x')</script> SELECT * FROM users;"
    cleaned = sanitize_prompt(text)
    assert "<" not in cleaned and ">" not in cleaned


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc"], ), min_size=1, max_size=10))
def test_validate_file_path_allowed(tmp_path: Path, name: str) -> None:
    assume("/" not in name and name not in {".", ".."})
    allowed = tmp_path / "allowed"
    allowed.mkdir(exist_ok=True)
    file_path = allowed / name
    file_path.write_text("x")
    cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        result = validate_file_path(Path("allowed") / name, [allowed])
        assert result == resolve_path(str(allowed / name))
    finally:
        os.chdir(cwd)


def test_validate_file_path_disallowed(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    with pytest.raises(Exception):
        validate_file_path(tmp_path / "other" / "x.txt", [allowed])


def test_validate_file_path_traversal(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    with pytest.raises(Exception):
        validate_file_path(Path("../etc/passwd"), [allowed])


def test_resolve_path_success(tmp_path: Path) -> None:
    file_path = tmp_path / "x.txt"
    file_path.write_text("x")
    assert resolve_path(str(file_path)) == file_path.resolve()


def test_resolve_path_invalid() -> None:
    with pytest.raises(Exception):
        resolve_path("/non/existent/path.txt")
