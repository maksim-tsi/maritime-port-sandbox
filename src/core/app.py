from __future__ import annotations

import os

from fastapi import FastAPI

from src.api.admin.simulation import build_router as build_admin_router
from src.api.public.pcs import router as pcs_router
from src.state.store import InMemoryPortStore


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def create_app(
    *,
    expose_admin_docs: bool | None = None,
    port_store: InMemoryPortStore | None = None,
) -> FastAPI:
    expose_admin_docs_resolved = (
        _env_flag("EXPOSE_ADMIN_DOCS", default=False)
        if expose_admin_docs is None
        else expose_admin_docs
    )

    app = FastAPI(title="Maritime Port Sandbox", version="0.1.0")
    app.state.port_store = port_store or InMemoryPortStore()

    app.include_router(pcs_router)
    app.include_router(build_admin_router(expose_in_openapi=expose_admin_docs_resolved))

    return app

