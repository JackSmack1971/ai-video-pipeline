from .hierarchy import (
    PipelineBaseException,
    ConfigurationError,
    ServiceError,
    OpenAIError,
    ReplicateError,
    SonautoError,
    MediaProcessingError,
    FileOperationError,
    FFmpegError,
    FormatConversionError,
    ValidationError,
    InputValidationError,
    ConfigValidationError,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .retry_policies import RetryPolicy, get_policy
from .handlers import handle_exception, fallback_response

# Backwards compatibility
APIError = ServiceError
NetworkError = ServiceError
FileError = FileOperationError
FileOperationError = FileOperationError

__all__ = [
    "PipelineBaseException",
    "ConfigurationError",
    "ServiceError",
    "OpenAIError",
    "ReplicateError",
    "SonautoError",
    "MediaProcessingError",
    "FileOperationError",
    "FFmpegError",
    "FormatConversionError",
    "ValidationError",
    "InputValidationError",
    "ConfigValidationError",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "RetryPolicy",
    "get_policy",
    "handle_exception",
    "fallback_response",
    "APIError",
    "NetworkError",
    "FileError",
    "FileOperationError",
]
