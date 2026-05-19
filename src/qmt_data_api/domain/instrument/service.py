# 预留证券基础信息服务。
"""Instrument domain service."""

from __future__ import annotations

from qmt_data_api.core.config import get_settings
from qmt_data_api.core.errors import QmtError
from qmt_data_api.domain.instrument.schemas import InstrumentInfo, InstrumentResult
from qmt_data_api.domain.market.errors import invalid_symbol_error, too_many_symbols_error, unsupported_source_error
from qmt_data_api.providers.qmt.xtdata_adapter import fetch_xtdata_instruments
from qmt_data_api.utils.symbols import is_valid_symbol, normalize_symbol_list


def get_instruments(symbols: list[str], source: str = "auto") -> InstrumentResult:
    settings = get_settings()
    normalized_symbols = normalize_symbol_list(symbols)
    if not normalized_symbols:
        raise invalid_symbol_error(symbols)
    if len(normalized_symbols) > settings.market_snapshot_max_symbols:
        raise too_many_symbols_error(len(normalized_symbols), settings.market_snapshot_max_symbols)
    invalid_symbols = [symbol for symbol in normalized_symbols if not is_valid_symbol(symbol)]
    if invalid_symbols:
        raise invalid_symbol_error(invalid_symbols)

    normalized_source = source.strip().lower()
    if normalized_source not in {"auto", "qmt", "local"}:
        raise unsupported_source_error(source)
    if normalized_source == "local":
        return InstrumentResult(
            items=[_local_instrument(symbol) for symbol in normalized_symbols],
            missing_symbols=[],
            source="local",
        )

    try:
        items, missing = fetch_xtdata_instruments(normalized_symbols)
    except QmtError:
        if normalized_source == "auto":
            return InstrumentResult(
                items=[_local_instrument(symbol) for symbol in normalized_symbols],
                missing_symbols=[],
                source="local",
            )
        raise
    if not items and normalized_source == "auto":
        return InstrumentResult(
            items=[_local_instrument(symbol) for symbol in normalized_symbols],
            missing_symbols=[],
            source="local",
        )
    return InstrumentResult(items=items, missing_symbols=missing, source="qmt")


def _local_instrument(symbol: str) -> InstrumentInfo:
    return InstrumentInfo(symbol=symbol, market=symbol.split(".")[-1], instrument_type="stock")
