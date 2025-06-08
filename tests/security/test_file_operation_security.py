import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.file_operations import read_file, save_file
from exceptions import FileOperationError


@pytest.mark.security
class TestFileOperationSecurity:
    @pytest.mark.asyncio
    async def test_unsafe_read(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr('utils.file_operations.BASE_DIR', tmp_path)
        with pytest.raises(FileOperationError):
            await read_file('/etc/passwd')

    @pytest.mark.asyncio
    async def test_unsafe_write(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr('utils.file_operations.BASE_DIR', tmp_path)
        with pytest.raises(FileOperationError):
            await save_file('../secret.txt', b'x')
