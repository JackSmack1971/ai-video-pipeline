from pathlib import Path as _Path
import sys

sys.path.append(str(_Path(__file__).resolve().parents[1]))

import main


class DummyPipe:
    def __init__(self, cfg, services):
        self.tmp = _Path(cfg.pipeline.history_file).parent

    async def run_single_video(self):
        p = self.tmp / "single.mp4"
        p.write_bytes(b"v")
        return {"video": str(p)}

    async def run_multiple_videos(self, count):
        paths = []
        for i in range(count):
            p = self.tmp / f"in{i}.mp4"
            p.write_bytes(b"v")
            paths.append({"video": str(p)})
        return paths

    async def run_music_only(self, prompt):
        return {"music": "done"}


def _patch(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-testopenai1234567890abcd')
    monkeypatch.setenv('SONAUTO_API_KEY', 'sa-testsonauto1234567890abcd')
    monkeypatch.setenv('REPLICATE_API_KEY', 'r8_testreplicate1234567890abcd')
    monkeypatch.setattr(main, 'ContentPipeline', lambda cfg, svc: DummyPipe(cfg, svc))
    monkeypatch.setattr(main, 'create_services', lambda cfg: {})
    monkeypatch.setattr(_Path, 'rename', lambda self, dst: _Path(dst).write_bytes(b''))


def test_run_batch_small(monkeypatch, tmp_path):
    _patch(monkeypatch)
    out = tmp_path / 'out'
    main.main(['run', 'batch', '--size', 'small', '--output', str(out)])
    assert (out / 'video_0.mp4').exists()


def test_run_single(monkeypatch, tmp_path):
    _patch(monkeypatch)
    main.main(['run', 'single'])
    main.main(['run', 'music-only', '--prompt', 'hi'])

