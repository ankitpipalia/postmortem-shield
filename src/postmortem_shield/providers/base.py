from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a completion string from prompts."""
