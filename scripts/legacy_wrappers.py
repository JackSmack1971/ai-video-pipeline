import asyncio
from typing import List

from main import _build_parser


def auto_video(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(["run", "single"] + (argv or []))
    asyncio.run(args.func(args))


def auto_video3(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(["run", "batch", "--size", "small"] + (argv or []))
    asyncio.run(args.func(args))


def auto_video5(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(["run", "batch", "--size", "large"] + (argv or []))
    asyncio.run(args.func(args))


def auto_video4(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(["run", "music-only"] + (argv or []))
    asyncio.run(args.func(args))

