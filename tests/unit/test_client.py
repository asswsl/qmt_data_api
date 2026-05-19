# 验证轻量 Python 客户端的请求封装。
from __future__ import annotations

import json

from qmt_data_api.client import QmtDataClient


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"success": True, "data": {"ok": True}}).encode("utf-8")


def test_client_builds_authorized_kline_request(monkeypatch) -> None:
    captured = {}

    def _fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["api_key"] = request.headers["X-api-key"]
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("qmt_data_api.client.urlopen", _fake_urlopen)

    client = QmtDataClient("http://127.0.0.1:8000", "secret-key", timeout=3)
    payload = client.get_kline("600519.SH", "1d", "20240101", "20240110", fields=["close"])

    assert payload["success"] is True
    assert captured["api_key"] == "secret-key"
    assert captured["timeout"] == 3
    assert captured["url"].startswith("http://127.0.0.1:8000/api/v1/market/kline?")
    assert "symbol=600519.SH" in captured["url"]
    assert "fields=close" in captured["url"]
