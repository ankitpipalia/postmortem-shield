from __future__ import annotations

import hashlib

from postmortem_shield.providers.base import LLMProvider


class DeterministicMockProvider(LLMProvider):
    """Offline provider to keep demos deterministic and keyless."""

    name = "mock"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        fingerprint = hashlib.sha256(f"{system_prompt}\n{user_prompt}".encode()).hexdigest()[:16]
        return f"mock_completion::{fingerprint}"


def get_provider(name: str) -> LLMProvider:
    if name == "mock":
        return DeterministicMockProvider()
    raise ValueError(f"Unsupported provider '{name}'. Supported providers: mock")
