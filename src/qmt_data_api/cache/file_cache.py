# 提供历史 K 线 JSON 文件缓存。
"""JSON file cache for historical kline data."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
import time
from typing import Any

from qmt_data_api.cache.base import CacheStatus
from qmt_data_api.core.config import get_settings


class KlineFileCache:
    def __init__(self, *, backend: str = "json_file") -> None:
        self._backend = backend
        self._lock = RLock()
        self._hit_count = 0
        self._miss_count = 0
        self._evicted_count = 0

    def get(
        self,
        symbol: str,
        period: str,
        adjust: str,
        start: str,
        end: str,
        limit: int | None,
    ) -> dict[str, Any] | None:
        path = self._path(symbol, period, adjust, start, end, limit)
        with self._lock:
            if not path.exists():
                self._miss_count += 1
                return None
            try:
                with path.open("r", encoding="utf-8") as file:
                    payload = json.load(file)
            except (OSError, json.JSONDecodeError):
                self._miss_count += 1
                return None
            self._hit_count += 1
            return payload

    def set(
        self,
        symbol: str,
        period: str,
        adjust: str,
        start: str,
        end: str,
        limit: int | None,
        payload: dict[str, Any],
    ) -> None:
        path = self._path(symbol, period, adjust, start, end, limit)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with self._lock:
            with tmp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
            tmp_path.replace(path)

    def status(self) -> CacheStatus:
        root = self._root()
        files = list(root.rglob("*.json")) if root.exists() else []
        now = time.time()
        ages = [now - file.stat().st_mtime for file in files if file.exists()]
        return CacheStatus(
            backend=self._backend,
            enabled=True,
            item_count=len(files),
            hit_count=self._hit_count,
            miss_count=self._miss_count,
            evicted_count=self._evicted_count,
            expired_count=0,
            max_ttl_seconds=None,
            oldest_item_age_seconds=round(max(ages), 3) if ages else None,
            newest_item_age_seconds=round(min(ages), 3) if ages else None,
        )

    def _root(self) -> Path:
        return Path(get_settings().cache_dir) / "klines"

    def _path(
        self,
        symbol: str,
        period: str,
        adjust: str,
        start: str,
        end: str,
        limit: int | None,
    ) -> Path:
        limit_part = "all" if limit is None else str(limit)
        filename = f"{start}_{end}_limit-{limit_part}.json"
        return self._root() / symbol / period / adjust / filename


kline_file_cache = KlineFileCache()


def get_kline_file_cache() -> KlineFileCache:
    return kline_file_cache
