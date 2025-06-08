# Developer Workflow

This document explains how to contribute effectively to the AI Video Pipeline.

## Setup Automation

Use `make setup` to create a virtual environment and install dependencies. This script validates environment variables and configures pre-commit hooks.

## Code Review Checklist

- [ ] Functions are under 30 lines
- [ ] Async/await used for I/O operations
- [ ] Type hints added to all new code
- [ ] Custom exceptions used for error handling
- [ ] Tests updated with at least 80% coverage

## Testing

Run `pytest` before submitting a pull request. Use mocks for external APIs to ensure tests run offline.

## Release Process

1. Bump version in `pyproject.toml`.
2. Update the changelog.
3. Create a Git tag and push to the repository.

## Security Considerations

Never commit API keys or secrets. Validate all user inputs and use retry logic for external requests.
