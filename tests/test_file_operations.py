import asyncio
from pathlib import Path
import sys
import os
import json
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils import file_operations
from exceptions import FileError


@pytest.mark.asyncio
async def test_read_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(file_operations, "BASE_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    file_path = 'image/test_unit.txt'
    await file_operations.save_file(file_path, b'hello')
    content = await file_operations.read_file(file_path)
    assert content == 'hello'
    checks = json.loads((tmp_path / 'image' / '.checksums.json').read_text())
    assert file_path.split('/')[-1] in checks


@pytest.mark.asyncio
async def test_invalid_path(tmp_path: Path):
    with pytest.raises(FileError):
        await file_operations.read_file('/etc/passwd')


@pytest.mark.asyncio
async def test_path_traversal(tmp_path: Path):
    with pytest.raises(FileError):
        await file_operations.read_file('../secret.txt')


@pytest.mark.asyncio
async def test_checksum_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(file_operations, "BASE_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    path = 'image/bad.txt'
    await file_operations.save_file(path, b'data')
    file = tmp_path / path
    file.write_bytes(b'changed')
    with pytest.raises(FileError):
        await file_operations.read_file(path)
