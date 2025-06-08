from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
import asyncio
import pytest

from scripts import quality_check, security_scan


class DummyBlock:
    def __init__(self, complexity: int) -> None:
        self.complexity = complexity
        self.lineno = 1


@pytest.mark.asyncio
async def test_quality_main(monkeypatch) -> None:
    calls = []

    async def fake_complexity(paths, max_complexity=10):
        calls.append("complexity")

    async def fake_doc(paths):
        calls.append("doc")

    async def fake_cov(threshold=85):
        calls.append("cov")

    monkeypatch.setattr(quality_check, "check_complexity", fake_complexity)
    monkeypatch.setattr(quality_check, "check_docstrings", fake_doc)
    monkeypatch.setattr(quality_check, "check_coverage", fake_cov)
    await quality_check.main()
    assert calls == ["complexity", "doc", "cov"]


@pytest.mark.asyncio
async def test_security_main(monkeypatch) -> None:
    calls = []

    async def fake_sast(paths):
        calls.append("sast")

    async def fake_dep():
        calls.append("dep")

    async def fake_sec(paths):
        calls.append("sec")

    monkeypatch.setattr(security_scan, "scan_sast", fake_sast)
    monkeypatch.setattr(security_scan, "scan_dependencies", fake_dep)
    monkeypatch.setattr(security_scan, "scan_secrets", fake_sec)
    await security_scan.main()
    assert calls == ["sast", "dep", "sec"]


@pytest.mark.asyncio
async def test_quality_helpers(monkeypatch, tmp_path: Path) -> None:
    file = tmp_path / "f.py"
    file.write_text("print('ok')")
    monkeypatch.setattr(quality_check, "cc_visit", lambda code: [DummyBlock(5)])
    await quality_check.check_complexity([str(file)], 10)
    async def fake_run(cmd, timeout=1):
        return 0, ""
    monkeypatch.setattr(quality_check, "_run", fake_run)
    await quality_check.check_docstrings(["."])
    await quality_check.check_coverage(85)


@pytest.mark.asyncio
async def test_security_helpers(monkeypatch) -> None:
    async def fake_run(cmd, timeout=1):
        return 0, ""
    monkeypatch.setattr(security_scan, "_run", fake_run)
    await security_scan.scan_sast(["."])
    await security_scan.scan_dependencies()
    await security_scan.scan_secrets(["."])

@pytest.mark.asyncio
async def test_run_success() -> None:
    code, out = await quality_check._run(["echo", "hi"], timeout=2)
    assert code == 0
    assert "hi" in out


@pytest.mark.asyncio
async def test_run_timeout() -> None:
    with pytest.raises(quality_check.QualityError):
        await quality_check._run(["sleep", "2"], timeout=1)

@pytest.mark.asyncio
async def test_security_run_success() -> None:
    code, out = await security_scan._run(["echo", "ok"], timeout=2)
    assert code == 0
    assert "ok" in out


@pytest.mark.asyncio
async def test_security_run_timeout() -> None:
    with pytest.raises(security_scan.SecurityError):
        await security_scan._run(["sleep", "2"], timeout=1)
