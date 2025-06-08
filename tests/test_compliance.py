import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
import pytest

from compliance import AuditLogger, PrivacyManager, AccessControl, ComplianceReporter, DataRetentionManager
from analytics.usage_tracker import TimeRange
from security.auth_manager import User


@pytest.mark.asyncio
async def test_audit_logger(tmp_path: Path) -> None:
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    Path('logs').mkdir()
    logger = AuditLogger('logs/audit.log')
    user = User("u1", ["admin"])
    await logger.log_user_action(user, "create", {"obj": "x"})
    rng = TimeRange(datetime.utcnow() - timedelta(seconds=1), datetime.utcnow() + timedelta(seconds=1))
    report = await logger.generate_audit_report(rng)
    assert len(report.entries) == 1
    os.chdir(old_cwd)


@pytest.mark.asyncio
async def test_privacy_manager() -> None:
    pm = PrivacyManager()
    await pm.set_consent("u", True)
    assert await pm.get_consent("u")
    await pm.store_personal_data("u", {"d": 1})
    data = await pm.handle_access_request("u")
    assert data["d"] == 1
    await pm.erase_user_data("u")
    assert not await pm.get_consent("u")


@pytest.mark.asyncio
async def test_access_control() -> None:
    ac = AccessControl()
    user = User("u", [])
    await ac.assign_role("u", "reader")
    assert await ac.check_access(user, "reader")
    await ac.revoke_role("u", "reader")
    assert not await ac.check_access(user, "reader")


@pytest.mark.asyncio
async def test_data_retention(tmp_path: Path) -> None:
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    Path('logs').mkdir()
    logger = AuditLogger('logs/audit.log')
    user = User("u", ["admin"])
    old = datetime.utcnow() - timedelta(days=2)
    await logger.log_system_event("start", {"t": str(old)})
    # rewrite first entry to simulate old timestamp
    p = Path('logs/audit.log')
    line = p.read_text().splitlines()[0]
    obj = json.loads(line)
    obj['t'] = (datetime.utcnow() - timedelta(days=2)).isoformat()
    p.write_text(json.dumps(obj) + '\n')
    await logger.log_user_action(user, "new", {})
    dr = DataRetentionManager('logs/audit.log', 1)
    await dr.enforce_policy()
    rng = TimeRange(datetime.utcnow() - timedelta(days=1), datetime.utcnow() + timedelta(days=1))
    report = await logger.generate_audit_report(rng)
    assert len(report.entries) == 1
    os.chdir(old_cwd)
