from __future__ import annotations

class PipelineBaseException(Exception):
    """Base exception for all pipeline errors."""

class ConfigurationError(PipelineBaseException):
    pass

class ServiceError(PipelineBaseException):
    pass

class OpenAIError(ServiceError):
    pass

class ReplicateError(ServiceError):
    pass

class SonautoError(ServiceError):
    pass

class MediaProcessingError(PipelineBaseException):
    pass

class FileOperationError(MediaProcessingError):
    pass

class FFmpegError(MediaProcessingError):
    pass

class FormatConversionError(MediaProcessingError):
    pass

class ValidationError(PipelineBaseException):
    pass

class InputValidationError(ValidationError):
    pass

class ConfigValidationError(ValidationError):
    pass
