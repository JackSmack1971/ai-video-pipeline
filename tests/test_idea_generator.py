import asyncio
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from services import idea_generator
from config import Config


@pytest.mark.asyncio
async def test_generate_idea(monkeypatch, tmp_path: Path):
    cfg = Config("sk", "sa", "rep", 1)

    async def fake_read(path: str) -> str:
        return "[]"

    async def fake_save(path: str, data: bytes) -> None:
        return None

    class FakeResp:
        class Choice:
            message = type("msg", (), {"content": "Idea: Test\nPrompt: do it"})()
        choices = [Choice()]

    async def fake_chat(prompt: str, config: Config):
        return FakeResp()

    monkeypatch.setattr(idea_generator.file_operations, "read_file", fake_read)
    monkeypatch.setattr(idea_generator.file_operations, "save_file", fake_save)
    monkeypatch.setattr(idea_generator, "openai_chat", fake_chat)

    result = await idea_generator.generate_idea(cfg, str(tmp_path / "hist.json"))
    assert result["idea"] == "Test"
    assert result["prompt"] == "do it"
