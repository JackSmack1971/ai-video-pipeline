from __future__ import annotations

from typing import Any, Callable, Dict


class Container:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._providers: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}

    def register_singleton(self, name: str, provider: Callable[[], Any]) -> None:
        self._providers[name] = provider

    def get(self, name: str, default: Any | None = None) -> Any:
        if name not in self._instances:
            provider = self._providers.get(name)
            if provider is None:
                return default
            self._instances[name] = provider()
        return self._instances[name]

    def __getitem__(self, name: str) -> Any:
        return self.get(name)

    def clear(self) -> None:
        self._providers.clear()
        self._instances.clear()
