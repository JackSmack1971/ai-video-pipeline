from __future__ import annotations

from typing import Any, Callable, Dict


class DIContainer:
    """Lightweight dependency injection container."""

    def __init__(self) -> None:
        self._singletons: Dict[Any, Callable[[], Any]] = {}
        self._instances: Dict[Any, Any] = {}
        self._factories: Dict[Any, Callable[[], Any]] = {}

    def register_singleton(self, key: Any, provider: Callable[[], Any]) -> None:
        self._singletons[key] = provider

    def register_factory(self, key: Any, factory: Callable[[], Any]) -> None:
        self._factories[key] = factory

    def resolve(self, key: Any) -> Any:
        if key in self._instances:
            return self._instances[key]
        if key in self._singletons:
            self._instances[key] = self._singletons[key]()
            return self._instances[key]
        if key in self._factories:
            return self._factories[key]()
        raise KeyError(f"Service {key} not registered")

    def __getitem__(self, key: Any) -> Any:
        return self.resolve(key)

    def get(self, key: Any, default: Any | None = None) -> Any:
        """Dictionary-like access with default fallback."""
        try:
            return self.resolve(key)
        except KeyError:
            return default
