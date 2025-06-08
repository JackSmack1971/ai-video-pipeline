from __future__ import annotations

import asyncio


async def run_suite() -> None:
    proc = await asyncio.create_subprocess_exec(
        "pytest", "-m", "load or chaos", "-q"
    )
    await proc.communicate()


if __name__ == "__main__":
    asyncio.run(run_suite())
