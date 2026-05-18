# 定义统一错误码和应用异常。
"""Application error codes and exceptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any


class ErrorCode:
    OK = "OK"
    AUTH_MISSING_API_KEY = "AUTH_MISSING_API_KEY"
    AUTH_INVALID_API_KEY = "AUTH_INVALID_API_KEY"
    REQ_INVALID_PARAMS = "REQ_INVALID_PARAMS"
    QMT_XTDATA_IMPORT_FAILED = "QMT_XTDATA_IMPORT_FAILED"
    QMT_XTDATA_UNAVAILABLE = "QMT_XTDATA_UNAVAILABLE"
    QMT_STATUS_PROBE_FAILED = "QMT_STATUS_PROBE_FAILED"
    SYS_INTERNAL_ERROR = "SYS_INTERNAL_ERROR"


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = HTTPStatus.BAD_REQUEST
    detail: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


class AuthError(AppError):
    pass


class QmtError(AppError):
    pass
