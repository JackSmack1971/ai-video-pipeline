from __future__ import annotations

from typing import Any

from config import Config

from .container import Container
from .factory import create_services

_container: Container | None = None


def init_services(config: Config) -> Container:
    global _container
    _container = create_services(config)
    return _container


def get_service(name: str) -> Any:
    if _container is None:
        raise RuntimeError("Services not initialized")
    return _container[name]


def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Services not initialized")
    return _container


def clear_services() -> None:
    global _container
    if _container is not None:
        _container.clear()
    _container = None
