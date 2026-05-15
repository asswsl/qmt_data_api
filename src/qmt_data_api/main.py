"""ASGI entrypoint for QMT Data API."""

from qmt_data_api.app import create_app

app = create_app()
