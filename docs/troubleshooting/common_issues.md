# Common Issues and Solutions

This guide lists typical problems encountered when running the AI Video Pipeline.

## API Authentication Errors

Ensure that API keys are provided through environment variables and are not expired. Check `.env` configuration.

## Service Connectivity Problems

- Verify Docker containers are running with `docker ps`.
- Check network rules or firewalls preventing access to external services.
- Use retry logic and adjust timeouts as described in `AGENTS.md`.

## Configuration Mistakes

Invalid or missing configuration values can cause crashes. Validate the `.env` file and ensure all variables are set.

## Log Analysis

Logs are written to the `logs/` directory. Inspect them for stack traces and error messages when troubleshooting issues.
