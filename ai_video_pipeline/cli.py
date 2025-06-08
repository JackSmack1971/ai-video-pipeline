import argparse
import asyncio
from pathlib import Path
from typing import List

from config import (
    load_config_async,
    get_pipeline_config,
    PipelineConfig,
)
from pipeline import ContentPipeline
from services.factory import create_services
from utils.logging_config import setup_logging


def _load_custom_config(path: str) -> PipelineConfig:
    text = Path(path).read_text()
    import json
    data = json.loads(text)
    base = get_pipeline_config()
    for k, v in data.items():
        setattr(base, k, v)
    return base


async def _run_generate(args: argparse.Namespace) -> None:
    setup_logging()
    cfg = await load_config_async()
    if args.config_file:
        cfg.pipeline = _load_custom_config(args.config_file)
    cfg.pipeline.default_video_duration = args.duration
    container = create_services(cfg)
    pipe = ContentPipeline(cfg, container)
    result = await pipe.run_multiple_videos(args.video_count)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, item in enumerate(result):
        dest = out_dir / f"video_{idx}.mp4"
        Path(item["video"]).rename(dest)
    print({"videos": [str((out_dir / f"video_{i}.mp4")) for i in range(len(result))]})


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ai_video_pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--idea-type", default="general")
    gen.add_argument("--video-count", type=int, default=get_pipeline_config().video_batch_small)
    gen.add_argument("--duration", type=int, default=get_pipeline_config().default_video_duration)
    gen.add_argument("--output-dir", default="outputs")
    gen.add_argument("--config-file")
    args = parser.parse_args(argv)
    if args.cmd == "generate":
        asyncio.run(_run_generate(args))


if __name__ == "__main__":
    main()
