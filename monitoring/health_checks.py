from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import List

from config import Config
from utils.api_clients import openai_chat, replicate_run, http_get
from utils.media_processing import merge_video_audio
from exceptions import ServiceError


@dataclass
class HealthStatus:
    service: str
    healthy: bool
    details: str = ""


@dataclass
class SystemHealthStatus:
    services: List[HealthStatus] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(s.healthy for s in self.services)


class ServiceHealthChecker:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def check_openai_health(self) -> HealthStatus:
        try:
            await openai_chat("ping", self.config)
            return HealthStatus("openai", True)
        except Exception as exc:
            return HealthStatus("openai", False, str(exc))

    async def check_replicate_health(self) -> HealthStatus:
        try:
            await replicate_run("black-forest-labs/flux-pro", {"prompt": "test"}, self.config)
            return HealthStatus("replicate", True)
        except Exception as exc:
            return HealthStatus("replicate", False, str(exc))

    async def check_sonauto_health(self) -> HealthStatus:
        try:
            await http_get("https://api.sonauto.ai/health", self.config)
            return HealthStatus("sonauto", True)
        except Exception as exc:
            return HealthStatus("sonauto", False, str(exc))

    async def check_ffmpeg_health(self) -> HealthStatus:
        try:
            await merge_video_audio("", "", None, "", 1)
        except ServiceError:
            # merge_video_audio raises error if paths invalid; this means ffmpeg exists
            return HealthStatus("ffmpeg", True)
        except Exception as exc:
            return HealthStatus("ffmpeg", False, str(exc))
        return HealthStatus("ffmpeg", True)

    async def get_overall_health(self) -> SystemHealthStatus:
        results = await asyncio.gather(
            self.check_openai_health(),
            self.check_replicate_health(),
            self.check_sonauto_health(),
            self.check_ffmpeg_health(),
        )
        return SystemHealthStatus(list(results))
