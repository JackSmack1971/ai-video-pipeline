class APIError(Exception):
    pass

class NetworkError(Exception):
    pass

class FileError(Exception):
    """Raised when a file operation fails."""
    pass

# Backwards compatibility
FileOperationError = FileError
