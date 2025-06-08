import asyncio
from pathlib import Path
import zipfile

from .persistence import PipelineStateManager, PipelineState


class RecoveryManager:
    def __init__(self, backup_dir: str = "backups") -> None:
        self.backup_dir = Path(backup_dir)

    async def restore_backup(self, archive_name: str, target_dir: str) -> None:
        path = self.backup_dir / archive_name
        with zipfile.ZipFile(path, "r") as zf:
            await asyncio.to_thread(zf.extractall, target_dir)

    async def recover_pipeline(self, pipeline_id: str, manager: PipelineStateManager) -> PipelineState:
        return await manager.load_state(pipeline_id)
