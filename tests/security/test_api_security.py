import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from ai_video_pipeline import api_app


@pytest.mark.security
class TestAPISecurity:
    def test_security_headers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_authenticate_api_key(api_key: str):
            from security.auth_manager import User
            return User(id="u", roles=["admin"])

        monkeypatch.setattr(api_app.auth, "authenticate_api_key", fake_authenticate_api_key)
        client = TestClient(api_app.app)
        resp = client.get("/status/none", headers={"X-API-KEY": "k"})
        assert resp.status_code in {200, 404}
        assert "X-Frame-Options" in resp.headers
