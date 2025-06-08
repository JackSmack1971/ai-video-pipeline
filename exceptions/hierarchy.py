from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from monitoring.structured_logger import correlation_id


@dataclass
class PipelineBaseException(Exception):
    """Base exception with context and correlation tracking."""

    message: str
    correlation_id: Optional[str] = field(default=None)
    context: Dict[str, Any] = field(default_factory=dict)
    attempt: int = 0
    elapsed: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.correlation_id:
            self.correlation_id = correlation_id.get()
        super().__init__(self.message)


class SecurityError(PipelineBaseException):
    """Security-related errors."""

class ConfigurationError(PipelineBaseException):
    """Configuration and setup errors."""

class ServiceError(PipelineBaseException):
    """External service errors."""

class OpenAIError(ServiceError):
    pass

class ReplicateError(ServiceError):
    pass

class SonautoError(ServiceError):
    pass

class MediaProcessingError(PipelineBaseException):
    """Errors during media processing."""

class FileOperationError(MediaProcessingError):
    """File system operation errors."""

class FFmpegError(MediaProcessingError):
    """FFmpeg execution errors."""

class FormatConversionError(MediaProcessingError):
    """Media format conversion errors."""

class ValidationError(PipelineBaseException):
    pass

class InputValidationError(ValidationError):
    pass

class ConfigValidationError(ValidationError):
    pass
