import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import zipfile

from .integrity_checker import IntegrityChecker


class BackupManager:
    def __init__(self, data_dirs: List[str], backup_dir: str = "backups", retention_days: int = 30) -> None:
        self.data_dirs = [Path(d) for d in data_dirs]
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention = timedelta(days=retention_days)
        self.integrity = IntegrityChecker()

    async def _archive(self, name: str) -> Path:
        path = self.backup_dir / f"{name}.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for d in self.data_dirs:
                for file in d.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(d.parent))
        checksum = await self.integrity.sha256(path)
        await self.integrity.update_checksum_file(self.backup_dir / "checksums.json", path.name, checksum)
        return path

    async def incremental_backup(self) -> Path:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M")
        return await self._archive(f"inc_{ts}")

    async def full_backup(self) -> Path:
        ts = datetime.utcnow().strftime("%Y%m%d")
        return await self._archive(f"full_{ts}")

    async def cleanup_backups(self) -> None:
        now = datetime.utcnow()
        for p in self.backup_dir.glob("*.zip"):
            mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
            if now - mtime > self.retention:
                await asyncio.to_thread(p.unlink)
                checks = await self.integrity.load_checksums(self.backup_dir / "checksums.json")
                if p.name in checks:
                    del checks[p.name]
                    await self.integrity.update_checksum_file(self.backup_dir / "checksums.json", p.name, checks.get(p.name, ""))
