# Security Guidelines

This project enforces strict input validation and secure defaults.

## Input Validation
- All API requests are validated using Pydantic models.
- Prompts are sanitized with Unicode normalization and a strict whitelist.
- File paths are validated against allowed directories and symlinks are rejected.

## Middleware
- CORS, HTTPS redirects and trusted hosts are configured by default.
- Additional security headers are added to each response to mitigate common attacks.

## Development Tips
- Never hardcode API keys. Use environment variables.
- Wrap all external API calls with retry and timeout logic.
- Validate and sanitize user input before any processing.

