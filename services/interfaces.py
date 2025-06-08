from __future__ import annotations

from typing import Dict, List, Protocol


class IdeaGeneratorInterface(Protocol):
    async def generate(self) -> Dict[str, str]:
        ...

    async def get_history(self) -> List[str]:
        ...

    async def clear_history(self) -> None:
        ...


class MediaGeneratorInterface(Protocol):
    async def generate(self, prompt: str, **kwargs) -> str:  # pragma: no cover - interface
        ...

    async def get_supported_formats(self) -> List[str]:
        ...

    async def validate_input(self, **kwargs) -> bool:
        ...
