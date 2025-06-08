from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List

from security.vulnerability_scanner import VulnerabilityScanner


async def run_bandit(paths: List[str]) -> int:
    proc = await asyncio.create_subprocess_exec(
        "bandit", "-r", *paths, "-f", "json", "-o", "bandit_report.json"
    )
    await proc.communicate()
    return proc.returncode or 0


async def run_zap(target: str) -> int:
    proc = await asyncio.create_subprocess_exec(
        "zap-cli", "quick-scan", "-r", "-o", "zap_report.html", target
    )
    await proc.communicate()
    return proc.returncode or 0


async def main() -> None:
    scanner = VulnerabilityScanner()
    vulns = await scanner.scan_requirements(Path("requirements.txt"))
    if vulns:
        print("Vulnerabilities found:", ", ".join(vulns))
    await run_bandit(["ai_video_pipeline", "services", "utils", "security"])
    target = os.getenv("ZAP_TARGET")
    if target:
        await run_zap(target)


if __name__ == "__main__":
    asyncio.run(main())
