"""FastAPI application factory."""

from fastapi import FastAPI

from qmt_data_api.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="QMT Data API", version="0.1.0")
    app.include_router(api_router)
    return app
