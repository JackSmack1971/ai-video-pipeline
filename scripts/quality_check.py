from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

from radon.complexity import cc_visit


class QualityError(Exception):
    """Raised when a quality gate fails."""


async def _run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise QualityError("Command timeout") from exc
    return proc.returncode, out.decode()


async def check_complexity(paths: Iterable[str], max_complexity: int = 10) -> None:
    for file in paths:
        code = await asyncio.to_thread(Path(file).read_text)
        for block in cc_visit(code):
            if block.complexity > max_complexity:
                raise QualityError(
                    f"{file} {block.lineno} complexity {block.complexity} > {max_complexity}"
                )


async def check_docstrings(paths: Iterable[str]) -> None:
    code, out = await _run(["pydocstyle", *paths])
    if code != 0:
        raise QualityError(out)


async def check_coverage(threshold: int = 85) -> None:
    await _run(["coverage", "run", "-m", "pytest"], timeout=300)
    code, out = await _run([
        "coverage",
        "report",
        f"--fail-under={threshold}",
    ])
    if code != 0:
        raise QualityError(out)


async def main() -> None:
    files = [str(p) for p in Path(".").rglob("*.py") if "venv" not in p.parts]
    await check_complexity(files)
    await check_docstrings(files)
    await check_coverage()


if __name__ == "__main__":
    asyncio.run(main())
