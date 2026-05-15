# 提供 QMT Data API 的 ASGI 应用入口。
"""ASGI entrypoint for QMT Data API."""

from qmt_data_api.app import create_app

app = create_app()
