from __future__ import annotations

from fastapi import Request

from src.services.port_manager import PortManager
from src.state.store import InMemoryPortStore


def get_port_manager(request: Request) -> PortManager:
    store = request.app.state.port_store
    if not isinstance(store, InMemoryPortStore):  # pragma: no cover
        raise TypeError("app.state.port_store must be an InMemoryPortStore")
    return PortManager(store=store)

