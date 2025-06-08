import asyncio
from pathlib import Path
import sys
import os
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils import file_operations
from exceptions import FileError


@pytest.mark.asyncio
async def test_read_write(tmp_path: Path):
    file_path = 'image/test_unit.txt'
    await file_operations.save_file(file_path, b'hello')
    content = await file_operations.read_file(file_path)
    assert content == 'hello'


@pytest.mark.asyncio
async def test_invalid_path(tmp_path: Path):
    with pytest.raises(FileError):
        await file_operations.read_file('/etc/passwd')


@pytest.mark.asyncio
async def test_path_traversal(tmp_path: Path):
    with pytest.raises(FileError):
        await file_operations.read_file('../secret.txt')
