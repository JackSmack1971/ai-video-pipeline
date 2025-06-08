from __future__ import annotations

from typing import Dict


class NotificationChannel:
    def send(self, message: str) -> None:
        print(message)


class NotificationRouter:
    def __init__(self, channels: Dict[str, NotificationChannel]) -> None:
        self.channels = channels

    def notify(self, channel: str, message: str) -> None:
        if channel in self.channels:
            self.channels[channel].send(message)
