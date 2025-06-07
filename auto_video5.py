import asyncio
import os
from pathlib import Path

from config import load_config, ConfigError
from pipeline import ContentPipeline
from services.factory import create_services


async def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        raise SystemExit(str(exc))

    for d in ["image", "video", "music", "voice"]:
        Path(d).mkdir(exist_ok=True)

    services = create_services(config)
    pipeline = ContentPipeline(config, services)
    try:
        results = await pipeline.run_multiple_videos(5)
        print(results)
    except Exception as exc:
        print(f"Pipeline failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
