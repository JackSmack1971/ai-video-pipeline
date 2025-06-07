import re
from pathlib import Path as _Path
import sys
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from utils.validation import sanitize_prompt, validate_file_path


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text())
def test_sanitize_prompt_valid_chars(text: str) -> None:
    assume(text.strip())
    cleaned = sanitize_prompt(text)
    assert cleaned == "" or re.fullmatch(r"[\w\s.,!?'-]+", cleaned)


def test_sanitize_prompt_invalid() -> None:
    with pytest.raises(ValueError):
        sanitize_prompt("")


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc"], ), min_size=1, max_size=10))
def test_validate_file_path_allowed(tmp_path: Path, name: str) -> None:
    assume("/" not in name and name not in {".", ".."})
    allowed = tmp_path / "allowed"
    allowed.mkdir(exist_ok=True)
    file_path = allowed / name
    file_path.write_text("x")
    result = validate_file_path(file_path, [allowed])
    assert result == file_path.resolve()


def test_validate_file_path_disallowed(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    with pytest.raises(Exception):
        validate_file_path(tmp_path / "other" / "x.txt", [allowed])
