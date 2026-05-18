# 加载应用运行配置。
"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_api_keys(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    app_host: str
    app_port: int
    api_key_enabled: bool
    api_keys: tuple[str, ...]
    log_level: str
    log_dir: str
    data_dir: str
    cache_dir: str
    market_snapshot_max_symbols: int
    market_snapshot_cache_ttl_seconds: int
    qmt_enable_trade_api: bool
    qmt_enable_real_order: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        api_key_enabled=_parse_bool(os.getenv("API_KEY_ENABLED"), True),
        api_keys=_parse_api_keys(os.getenv("API_KEYS")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=os.getenv("LOG_DIR", "logs/app"),
        data_dir=os.getenv("DATA_DIR", "data"),
        cache_dir=os.getenv("CACHE_DIR", "data/cache"),
        market_snapshot_max_symbols=int(os.getenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "200")),
        market_snapshot_cache_ttl_seconds=int(os.getenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "3")),
        qmt_enable_trade_api=_parse_bool(os.getenv("QMT_ENABLE_TRADE_API"), False),
        qmt_enable_real_order=_parse_bool(os.getenv("QMT_ENABLE_REAL_ORDER"), False),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
