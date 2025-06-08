# AI Video Pipeline - Development Guide

## Project Overview
AI-powered video generation pipeline using OpenAI, Replicate, and Sonauto APIs. 
**Current Status**: 4/10 health score, High technical debt requiring immediate attention.

## Critical Issues to Address
- **Security**: Hardcoded API keys (lines 10-12 in all auto_video*.py files), no input validation, unsafe file operations
- **Code Duplication**: 70%+ duplicate code across auto_video.py, auto_video3.py, auto_video4.py, auto_video5.py
- **No Error Handling**: API failures crash the application, no timeouts or retries
- **Zero Tests**: No test coverage, no mocking of external services

## Security Requirements (MANDATORY)
- NEVER hardcode API keys - always use environment variables with validation
- ALWAYS validate and sanitize user inputs before processing
- ALWAYS add timeout (30-120s) and retry logic for API calls
- ALWAYS use secure file operations with path validation

## Code Standards
- Maximum 30 lines per function
- Use async/await for all I/O operations (API calls, file operations)
- Add type hints and comprehensive error handling
- Write tests for all new code (80% coverage minimum)
- Use dependency injection, no hardcoded dependencies

## File Structure to Consolidate
```
Current duplicated functions across files:
- read_file() / save_file() → utils/file_operations.py
- generate_image() → services/image_generator.py  
- generate_video() → services/video_generator.py
- generate_music() → services/music_generator.py
- generate_voice_dialog() → services/voice_generator.py
```

## Required Error Handling Pattern
```python
async def api_call_with_retry(operation_name: str, api_call, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with timeout(self.config.api_timeout):
                return await api_call()
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise NetworkError(f"{operation_name} failed after {max_retries} attempts")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## API Integration Notes
- **OpenAI**: Idea generation (gpt-4o), TTS (gpt-4o-mini-tts) 
- **Replicate**: Image (flux-pro), Video (kling-v1.6-standard)
- **Sonauto**: Music generation with tags and prompt_strength
- **FFMPEG**: Video composition and merging

## Testing Requirements
- Use pytest with async support and comprehensive mocking
- Mock all external API calls, never make real requests in tests
- Test both success and error scenarios
- Create custom exception classes: APIError, NetworkError, FileOperationError

## Migration Strategy
1. Extract shared utilities and create service classes
2. Add security and error handling to one file at a time
3. Maintain backward compatibility during refactoring
4. Add tests as you refactor each component

**Priority**: Security and reliability over new features. Every change must improve the current 4/10 health score.

## Updated Development Practices
- Follow the workflow in `docs/contributing/development_workflow.md` for setup and code reviews.
- Refer to `docs/api/openapi.yaml` for API documentation. Keep this spec in sync with the codebase.
- Deployment instructions are available in `docs/deployment/production.md` and `docs/deployment/development.md`.
- Troubleshooting guides in `docs/troubleshooting/` should be consulted before opening support tickets.
