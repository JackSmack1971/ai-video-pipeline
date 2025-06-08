import asyncio
from pathlib import Path as _Path
import sys

sys.path.append(str(_Path(__file__).resolve().parents[1]))

from ai_video_pipeline import cli
from services import container


class DummyPipe:
    def __init__(self, cfg, services):
        self.tmp = _Path(cfg.pipeline.history_file).parent

    async def run_multiple_videos(self, count):
        paths = []
        for i in range(count):
            p = self.tmp / f"in{i}.mp4"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"v")
            paths.append({"video": str(p)})
        return paths


def test_cli_generate(monkeypatch, tmp_path):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890abcd')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890abcd')
    monkeypatch.setattr(cli, 'ContentPipeline', lambda cfg, services: DummyPipe(cfg, services))
    monkeypatch.setattr(cli, 'create_services', lambda cfg: container.Container())
    monkeypatch.setattr(_Path, 'rename', lambda self, dst: _Path(dst).write_bytes(b''))
    out = tmp_path / 'out'
    cli.main(['generate', '--video-count', '2', '--output-dir', str(out)])
    assert (out / 'video_0.mp4').exists()
    assert (out / 'video_1.mp4').exists()
