# 规范化和校验证券代码。
"""Symbol normalization helpers."""

from __future__ import annotations

import re

_SYMBOL_PATTERN = re.compile(r"^[0-9]{6}\.(SH|SZ|BJ)$")


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def is_valid_symbol(symbol: str) -> bool:
    return bool(_SYMBOL_PATTERN.fullmatch(normalize_symbol(symbol)))


def normalize_symbol_list(symbols: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        item = normalize_symbol(symbol)
        if item and item not in seen:
            normalized.append(item)
            seen.add(item)
    return normalized
