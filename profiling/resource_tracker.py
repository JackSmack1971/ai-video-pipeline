from __future__ import annotations

from dataclasses import dataclass
from typing import List

import psutil

from exceptions import ServiceError


@dataclass
class ResourceSnapshot:
    cpu: float
    memory: float
    disk_read: float
    disk_write: float
    net_sent: float
    net_recv: float
    gpu: float


class ResourceTracker:
    def __init__(self) -> None:
        self.snapshots: List[ResourceSnapshot] = []

    async def collect_once(self) -> ResourceSnapshot:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()
            snap = ResourceSnapshot(
                cpu,
                mem,
                disk.read_bytes,
                disk.write_bytes,
                net.bytes_sent,
                net.bytes_recv,
                0.0,
            )
            self.snapshots.append(snap)
            return snap
        except Exception as exc:
            raise ServiceError(f"resource tracking failed: {exc}") from exc

    async def average_usage(self) -> ResourceSnapshot:
        if not self.snapshots:
            return ResourceSnapshot(0, 0, 0, 0, 0, 0, 0)
        total = ResourceSnapshot(0, 0, 0, 0, 0, 0, 0)
        for s in self.snapshots:
            total.cpu += s.cpu
            total.memory += s.memory
            total.disk_read += s.disk_read
            total.disk_write += s.disk_write
            total.net_sent += s.net_sent
            total.net_recv += s.net_recv
            total.gpu += s.gpu
        n = len(self.snapshots)
        return ResourceSnapshot(
            total.cpu / n,
            total.memory / n,
            total.disk_read / n,
            total.disk_write / n,
            total.net_sent / n,
            total.net_recv / n,
            total.gpu / n,
        )
