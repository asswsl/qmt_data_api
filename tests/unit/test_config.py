# 验证应用配置加载与解析逻辑。
from qmt_data_api.core.config import clear_settings_cache, get_settings


def test_settings_parse_api_keys(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_KEY_ENABLED", "true")
    monkeypatch.setenv("API_KEYS", "alpha,beta")
    monkeypatch.setenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "5")
    monkeypatch.setenv("API_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("API_RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("API_RATE_LIMIT_WINDOW_SECONDS", "30")
    clear_settings_cache()

    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.api_key_enabled is True
    assert settings.api_keys == ("alpha", "beta")
    assert settings.market_snapshot_cache_ttl_seconds == 5
    assert settings.api_rate_limit_enabled is True
    assert settings.api_rate_limit_requests == 2
    assert settings.api_rate_limit_window_seconds == 30

    clear_settings_cache()
