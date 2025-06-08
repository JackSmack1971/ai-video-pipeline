from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable


class SecurityError(Exception):
    """Raised when a security scan fails."""


async def _run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise SecurityError("Command timeout") from exc
    return proc.returncode, out.decode()


async def scan_sast(paths: Iterable[str]) -> None:
    code, out = await _run(["bandit", "-r", *paths])
    if code != 0:
        raise SecurityError(out)


async def scan_dependencies() -> None:
    code, out = await _run(["safety", "check", "--full-report"])
    if code != 0:
        raise SecurityError(out)


async def scan_secrets(paths: Iterable[str]) -> None:
    code, out = await _run(["detect-secrets", "scan", *paths])
    if code != 0:
        raise SecurityError(out)


async def main() -> None:
    files = [str(p) for p in Path(".").rglob("*.py") if "venv" not in p.parts]
    await scan_sast(files)
    await scan_dependencies()
    await scan_secrets(files)


if __name__ == "__main__":
    asyncio.run(main())
