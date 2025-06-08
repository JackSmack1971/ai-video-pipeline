import asyncio
from datetime import timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from storage.persistence import PipelineStateManager, PipelineState
from storage.integrity_checker import IntegrityChecker
from storage.backup_manager import BackupManager
from storage.recovery_manager import RecoveryManager
from pipeline.stages import PipelineContext


@pytest.mark.asyncio
async def test_pipeline_state_manager(tmp_path: Path) -> None:
    mgr = PipelineStateManager(base_dir=tmp_path)
    state = PipelineState("stage", PipelineContext(idea="x"))
    await mgr.save_state("p1", state)
    loaded = await mgr.load_state("p1")
    assert loaded.stage == "stage"
    assert loaded.context.idea == "x"
    lst = await mgr.list_recoverable_pipelines()
    assert "p1" in lst
    await mgr.cleanup_old_states(timedelta(seconds=0))
    assert not (tmp_path / "p1.json").exists()


@pytest.mark.asyncio
async def test_integrity_checker(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("data")
    checker = IntegrityChecker()
    cs = await checker.sha256(f)
    assert await checker.verify(f, cs)
    f.write_text("bad")
    assert not await checker.verify(f, cs)


@pytest.mark.asyncio
async def test_backup_and_recovery(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "f.txt").write_text("x")
    bm = BackupManager([data], backup_dir=tmp_path / "bkp", retention_days=0)
    arc = await bm.incremental_backup()
    (data / "f.txt").unlink()
    rm = RecoveryManager(backup_dir=tmp_path / "bkp")
    await rm.restore_backup(arc.name, tmp_path / "out")
    restored = (tmp_path / "out" / "data" / "f.txt").read_text()
    assert restored == "x"
    await bm.cleanup_backups()
    assert not any((tmp_path / "bkp").glob("*.zip"))
