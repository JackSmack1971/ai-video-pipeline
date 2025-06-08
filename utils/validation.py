import re
from pathlib import Path
from typing import Iterable

MAX_PROMPT_LENGTH = 2000
_SAFE_PROMPT_RE = re.compile(r"[A-Za-z0-9\s.,!?'-]+")

from exceptions import FileError


def sanitize_prompt(prompt: str) -> str:
    """Remove unsafe characters and enforce length and whitelist."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValueError("Prompt exceeds maximum length")
    clean = re.sub(r"[^A-Za-z0-9\s.,!?'-]", "", prompt)
    if not _SAFE_PROMPT_RE.fullmatch(clean):
        clean = "".join(ch for ch in clean if _SAFE_PROMPT_RE.fullmatch(ch))
    return clean.strip()


def validate_file_path(path: Path, allowed_dirs: Iterable[Path]) -> Path:
    """Ensure the path stays within allowed directories."""
    if path.is_absolute():
        raise FileError("Absolute paths are not allowed")
    if any(part == ".." for part in path.parts):
        raise FileError("Path traversal detected")
    base = Path.cwd()
    resolved = (base / path).resolve()
    for allowed in allowed_dirs:
        allowed = allowed.resolve()
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue
    raise FileError(f"Access to '{path}' is not allowed")
