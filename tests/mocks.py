from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from config import Config

@dataclass
class FakeResponse:
    data: bytes
    status: int = 200

    async def read(self) -> bytes:
        return self.data

    async def json(self) -> Dict[str, Any]:
        import json
        return json.loads(self.data.decode())

    async def text(self) -> str:
        return self.data.decode()


async def fake_openai_chat(prompt: str, config: Config, model: str = "gpt-4o") -> Any:
    class Choice:
        def __init__(self, content: str) -> None:
            self.message = type("msg", (), {"content": content})

    class Resp:
        def __init__(self, content: str) -> None:
            self.choices = [Choice(content)]

    return Resp("Idea: Test Idea\nPrompt: test prompt")


async def fake_openai_speech(
    text: str, voice: str, instructions: str, config: Config
) -> Any:
    class Speech:
        def __init__(self, data: bytes) -> None:
            self.data = data

        def stream_to_file(self, filename: str) -> None:
            p = Path(filename); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(self.data)

    return Speech(b"voice")


async def fake_replicate_run(
    model: str, inputs: Dict[str, Any], config: Config
) -> Any:
    if "kling" in model:
        class F:
            def read(self) -> bytes:
                return b"video"

        return F()
    return "http://dummy/image.png"


async def fake_http_get(
    url: str, config: Config, headers: Dict[str, str] | None = None
) -> FakeResponse:
    if "status" in url:
        return FakeResponse(b"\"SUCCESS\"")
    if "generations" in url:
        return FakeResponse(b'{"song_paths": ["http://dummy/song.mp3"]}')
    return FakeResponse(b"data")


async def fake_http_post(
    url: str, payload: Dict[str, Any], headers: Dict[str, str], config: Config
) -> FakeResponse:
    return FakeResponse(b'{"task_id": "123"}')


async def async_merge(*args: Any, **kwargs: Any) -> str:
    return "final_output.mp4"
