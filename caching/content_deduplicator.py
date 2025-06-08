from __future__ import annotations

import hashlib
from difflib import SequenceMatcher
from typing import Dict, Iterable, Optional, Tuple, List


class ContentDeduplicator:
    """Detect similar prompts and media content."""

    def __init__(self) -> None:
        self.prompts: Dict[str, str] = {}

    def prompt_hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.lower().encode()).hexdigest()

    def check_prompt(self, prompt: str) -> Tuple[str, Optional[str]]:
        key = self.prompt_hash(prompt)
        for k, stored in self.prompts.items():
            ratio = SequenceMatcher(None, prompt.lower(), stored.lower()).ratio()
            if ratio >= 0.85:
                return k, stored
        self.prompts[key] = prompt
        return key, None

    async def common_prompts(self) -> Iterable[str]:
        return list(self.prompts.values())[:5]
