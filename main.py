import argparse
import asyncio
from pathlib import Path
from typing import Any

from config import load_config_async
from pipeline import ContentPipeline
from services.factory import create_services
from utils.validation import sanitize_prompt, validate_file_path


async def _prepare(config_env: str | None) -> tuple[Any, ContentPipeline]:
    cfg = await load_config_async(config_env)
    for d in ["image", "video", "music", "voice"]:
        Path(d).mkdir(exist_ok=True)
    container = create_services(cfg)
    pipe = ContentPipeline(cfg, container)
    return cfg, pipe


async def _run_single(args: argparse.Namespace) -> None:
    _, pipe = await _prepare(args.config)
    try:
        result = await pipe.run_single_video()
        print(result)
    except Exception as exc:
        print(f"Pipeline failed: {exc}")


async def _run_batch(args: argparse.Namespace) -> None:
    cfg, pipe = await _prepare(args.config)
    if args.duration:
        if not 1 <= args.duration <= 60:
            raise ValueError("duration must be between 1 and 60")
        cfg.pipeline.default_video_duration = args.duration
    batch = cfg.pipeline.video_batch_small if args.size == "small" else cfg.pipeline.video_batch_large
    result = await pipe.run_multiple_videos(batch)
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = validate_file_path(out_path, [Path.cwd()])
    out_dir = out_path.resolve()
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for idx, item in enumerate(result):
        Path(item["video"]).rename(Path(out_dir) / f"video_{idx}.mp4")
    print({"videos": [str(Path(out_dir) / f"video_{i}.mp4") for i in range(len(result))]})


async def _run_music_only(args: argparse.Namespace) -> None:
    _, pipe = await _prepare(args.config)
    prompt = sanitize_prompt(args.prompt)
    result = await pipe.run_music_only(prompt)
    print(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="main.py")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run_sub = run.add_subparsers(dest="mode", required=True)

    single = run_sub.add_parser("single")
    single.add_argument("--config")
    single.set_defaults(func=_run_single)

    batch = run_sub.add_parser("batch")
    batch.add_argument("--size", choices=["small", "large"], default="small")
    batch.add_argument("--duration", type=int)
    batch.add_argument("--output", default="outputs")
    batch.add_argument("--config")
    batch.set_defaults(func=_run_batch)

    music = run_sub.add_parser("music-only")
    music.add_argument("--prompt", required=True)
    music.add_argument("--config")
    music.set_defaults(func=_run_music_only)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
