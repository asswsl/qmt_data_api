# 验证历史 K 线文件缓存的读写与状态统计。
from __future__ import annotations

from qmt_data_api.cache.file_cache import KlineFileCache
from qmt_data_api.core.config import clear_settings_cache


def test_kline_file_cache_tracks_status(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()
    cache = KlineFileCache()
    payload = {
        "symbol": "600519.SH",
        "period": "1d",
        "adjust": "none",
        "source": "qmt",
        "cache": "miss",
        "bars": [{"trade_date": "2024-01-02", "close": 1685.01}],
    }

    cache.set("600519.SH", "1d", "none", "20240101", "20240110", 5, payload)

    assert cache.get("600519.SH", "1d", "none", "20240101", "20240110", 5) == payload
    assert cache.get("600519.SH", "1d", "none", "20240101", "20240110", 10) is None

    status = cache.status()
    assert status.backend == "json_file"
    assert status.enabled is True
    assert status.item_count == 1
    assert status.hit_count == 1
    assert status.miss_count == 1
    assert status.expired_count == 0
    assert status.max_ttl_seconds is None
    assert status.oldest_item_age_seconds is not None
    assert status.newest_item_age_seconds is not None

    clear_settings_cache()
