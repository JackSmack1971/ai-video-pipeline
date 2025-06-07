import asyncio
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils import media_processing


@pytest.mark.asyncio
async def test_merge_video_audio(monkeypatch):
    async def fake_proc(cmd, stdout=None, stderr=None):
        class P:
            returncode = 0
            async def communicate(self):
                return b"", b""
        return P()

    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake_proc)
    out = await media_processing.merge_video_audio("v.mp4", "m.mp3", None, "out.mp4", duration=1)
    assert out == "out.mp4"
