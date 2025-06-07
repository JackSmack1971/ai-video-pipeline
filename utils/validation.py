import re
from pathlib import Path
from typing import Iterable

from exceptions import FileError


def sanitize_prompt(prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string")
    clean = re.sub(r"[^\w\s.,!?'-]", "", prompt)
    return clean.strip()


def validate_file_path(path: Path, allowed_dirs: Iterable[Path]) -> Path:
    resolved = path.resolve()
    for allowed in allowed_dirs:
        allowed = allowed.resolve()
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue
    raise FileError(f"Access to '{path}' is not allowed")
