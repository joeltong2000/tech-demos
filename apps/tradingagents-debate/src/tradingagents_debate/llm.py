"""LLM backends: deterministic mock (default) and optional OpenAI-compatible."""

from __future__ import annotations

import hashlib
import os
import random
from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, *, role: str = "") -> str:
        raise NotImplementedError


class MockLLM(LLMClient):
    """Scripted responses filled from context; seeded for reproducibility."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def _pick(self, role: str, options: list[str]) -> str:
        digest = hashlib.sha256(f"{self.seed}:{role}:{options[0][:40]}".encode()).hexdigest()
        idx = int(digest[:8], 16) % len(options)
        # Mix in rng so callers can still vary across roles while staying seeded.
        _ = self._rng.random()
        return options[idx]

    def complete(self, system: str, user: str, *, role: str = "") -> str:
        # The mock ignores system/user prose and returns role-keyed scripts.
        # Orchestrator passes structured context via `user` for template fill.
        return f"[mock:{role or 'generic'}] {user.strip()}"


class OpenAICompatLLM(LLMClient):
    """Thin wrapper around an OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "Install optional deps: pip install 'tradingagents-debate[openai]'"
            ) from exc
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self.model = model

    def complete(self, system: str, user: str, *, role: str = "") -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        return (content or "").strip()


def resolve_llm(*, seed: int = 42, force: str | None = None) -> tuple[LLMClient, str]:
    """Pick mock vs OpenAI-compatible client.

    Priority: explicit ``force`` / ``DEMO_LLM`` env, else mock unless
    ``OPENAI_API_KEY`` is set and DEMO_LLM is not ``mock``.
    """
    mode = (force or os.getenv("DEMO_LLM") or "").strip().lower()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if mode == "mock" or (not mode and not api_key):
        return MockLLM(seed=seed), "mock"
    if mode in {"", "openai", "live"} and api_key:
        return (
            OpenAICompatLLM(
                api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            ),
            "openai",
        )
    if mode == "openai" and not api_key:
        raise RuntimeError("DEMO_LLM=openai requires OPENAI_API_KEY")
    return MockLLM(seed=seed), "mock"
