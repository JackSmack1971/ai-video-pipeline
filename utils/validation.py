import re
import unicodedata
from functools import wraps
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Type

from pydantic import BaseModel, ValidationError as PydanticError
from monitoring.structured_logger import get_logger

MAX_PROMPT_LENGTH = 2000
DEFAULT_PROMPT = "Default prompt"
_SAFE_PROMPT_RE = re.compile(r"[A-Za-z0-9\s.,!?'-]+")

logger = get_logger(__name__)

from exceptions import FileOperationError
from security.input_validator import InputValidator


def validate_model(model: Type[BaseModel]) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator to validate kwargs using a pydantic model."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                data = model(**kwargs)
            except PydanticError as exc:
                from exceptions import InputValidationError

                raise InputValidationError(str(exc)) from exc
            return await func(*args, **data.dict())

        return wrapper

    return decorator


def sanitize_prompt_param(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Decorator to sanitize the prompt argument for functions and methods."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not args and "prompt" not in kwargs:
            raise ValueError("prompt required")
        if args and not isinstance(args[0], str):
            self = args[0]
            prompt = args[1] if len(args) > 1 else kwargs.get("prompt")
            if prompt is None:
                raise ValueError("prompt required")
            if not str(prompt).strip():
                raise ValueError("prompt required")
            clean = await InputValidator.sanitize_text(sanitize_prompt(prompt))
            new_args = (self, clean, *args[2:])
        else:
            prompt = args[0] if args else kwargs.get("prompt")
            if not str(prompt).strip():
                raise ValueError("prompt required")
            clean = await InputValidator.sanitize_text(sanitize_prompt(str(prompt)))
            new_args = (clean, *args[1:]) if args else ()
        return await func(*new_args, **kwargs)

    return wrapper


def sanitize_prompt(prompt: str) -> str:
    """Sanitize prompts to mitigate injection attacks."""
    if not isinstance(prompt, str) or not prompt.strip():
        logger.warning("Empty or invalid prompt received; using default")
        prompt = DEFAULT_PROMPT
    text = unicodedata.normalize("NFKC", prompt)[:MAX_PROMPT_LENGTH]
    text = re.sub(r"[\r\n\t]", " ", text)
    text = re.sub(r"[^A-Za-z0-9\s.,!?'-]", "", text)
    if not _SAFE_PROMPT_RE.fullmatch(text):
        text = "".join(ch for ch in text if _SAFE_PROMPT_RE.fullmatch(ch))
    return text.strip()


def resolve_path(path: str) -> Path:
    """Resolve a path and ensure it exists."""
    try:
        return Path(path).resolve(strict=True)
    except Exception as exc:
        raise FileOperationError(f"Invalid path: {path}") from exc


def validate_file_path(path: Path, allowed_dirs: Iterable[Path]) -> Path:
    """Validate file paths and block traversal attacks."""
    norm = Path(path)
    if norm.is_absolute() or any(part in {"..", ""} for part in norm.parts):
        raise FileOperationError("Path traversal detected")
    base = Path.cwd()
    resolved = (base / norm).resolve()
    if resolved.is_symlink():
        raise FileOperationError("Symlinks are not allowed")
    for allowed in allowed_dirs:
        try:
            resolved.relative_to((base / allowed).resolve())
            return resolved
        except ValueError:
            continue
    raise FileOperationError(f"Access to '{path}' is not allowed")

