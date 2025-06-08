import asyncio
import os
from pathlib import Path

from config import load_config_async, ConfigError
from pipeline import ContentPipeline
from services.factory import create_services


async def main() -> None:
    try:
        config = await load_config_async()
    except ConfigError as exc:
        raise SystemExit(str(exc))

    os.environ["REPLICATE_API_TOKEN"] = config.replicate_api_key
    for d in ["image", "video", "music", "voice"]:
        Path(d).mkdir(exist_ok=True)

    services = create_services(config)
    pipeline = ContentPipeline(config, services)
    try:
        result = await pipeline.run_single_video()
        print(result)
    except Exception as exc:
        print(f"Pipeline failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
