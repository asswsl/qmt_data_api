# 提供 QMT Data API 的轻量 Python 客户端。
"""Lightweight Python client for QMT Data API."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class QmtDataClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/health")

    def get_snapshot(
        self,
        symbols: list[str],
        fields: list[str] | None = None,
        source: str = "auto",
    ) -> dict[str, Any]:
        query = {"symbols": ",".join(symbols), "source": source}
        if fields:
            query["fields"] = ",".join(fields)
        return self._request("GET", f"/api/v1/market/snapshot?{urlencode(query)}")

    def get_kline(
        self,
        symbol: str,
        period: str,
        start: str,
        end: str,
        adjust: str = "none",
        source: str = "auto",
        limit: int | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {
            "symbol": symbol,
            "period": period,
            "start": start,
            "end": end,
            "adjust": adjust,
            "source": source,
        }
        if limit is not None:
            query["limit"] = limit
        if fields:
            query["fields"] = ",".join(fields)
        return self._request("GET", f"/api/v1/market/kline?{urlencode(query)}")

    def get_klines(
        self,
        symbols: list[str],
        period: str,
        start: str,
        end: str,
        adjust: str = "none",
        source: str = "auto",
        limit: int | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/market/klines",
            {
                "symbols": symbols,
                "period": period,
                "start": start,
                "end": end,
                "adjust": adjust,
                "source": source,
                "limit": limit,
                "fields": fields,
            },
        )

    def get_latest_kline(
        self,
        symbol: str,
        period: str = "1m",
        count: int = 240,
        adjust: str = "none",
        source: str = "auto",
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {
            "symbol": symbol,
            "period": period,
            "count": count,
            "adjust": adjust,
            "source": source,
        }
        if fields:
            query["fields"] = ",".join(fields)
        return self._request("GET", f"/api/v1/market/kline/latest?{urlencode(query)}")

    def get_instruments(self, symbols: list[str], source: str = "auto") -> dict[str, Any]:
        query = {"symbols": ",".join(symbols), "source": source}
        return self._request("GET", f"/api/v1/instruments?{urlencode(query)}")

    def get_trading_days(
        self,
        market: str,
        start: str,
        end: str,
        source: str = "auto",
    ) -> dict[str, Any]:
        query = {"market": market, "start": start, "end": end, "source": source}
        return self._request("GET", f"/api/v1/calendar/trading-days?{urlencode(query)}")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None
        headers = {"X-API-Key": self.api_key}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))
