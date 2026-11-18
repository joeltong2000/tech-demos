"""Parse and normalize trade decisions from agent text."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

Action = Literal["BUY", "SELL", "HOLD"]

_ACTION_RE = re.compile(
    r"\b(BUY|SELL|HOLD)\b(?:\s+(?:size|shares?|qty|quantity)?\s*[:=]?\s*(\d+(?:\.\d+)?))?",
    re.IGNORECASE,
)
_SIZE_RE = re.compile(
    r"(?:size|shares?|qty|quantity)\s*[:=]?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_FINAL_RE = re.compile(
    r"FINAL\s+DECISION\s*:\s*(BUY|SELL|HOLD)"
    r"(?:\s+(?:size|shares?|qty|quantity)?\s*[:=]?\s*(\d+(?:\.\d+)?))?",
    re.IGNORECASE,
)
_VERDICT_RE = re.compile(r"\b(APPROVE|REJECT(?:ED)?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class TradeDecision:
    action: Action
    size: float
    rationale: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_action(raw: str) -> Action:
    action = raw.strip().upper()
    if action not in {"BUY", "SELL", "HOLD"}:
        raise ValueError(f"Invalid action: {raw!r}")
    return action  # type: ignore[return-value]


def parse_decision(
    text: str,
    *,
    default_size: float = 0.0,
    approved: bool | None = None,
) -> TradeDecision:
    """Extract BUY/SELL/HOLD and optional size from free-form agent text.

    Prefers a ``FINAL DECISION:`` line when present. HOLD always forces size 0.
    If ``approved`` is omitted, a REJECT/APPROVE token in the text is used.
    Rejected proposals become HOLD size=0 with ``approved=False``.
    """
    if not text or not text.strip():
        raise ValueError("Empty decision text")

    if approved is None:
        verdict = _VERDICT_RE.search(text)
        if verdict and verdict.group(1).upper().startswith("REJECT"):
            approved = False
        else:
            approved = True

    match = _FINAL_RE.search(text) or _ACTION_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse BUY/SELL/HOLD from: {text!r}")

    action = _normalize_action(match.group(1))
    size_raw = match.group(2)
    if size_raw is None:
        size_match = _SIZE_RE.search(text)
        size_raw = size_match.group(1) if size_match else None

    size = float(size_raw) if size_raw is not None else float(default_size)
    if action == "HOLD":
        size = 0.0
    if size < 0:
        raise ValueError("Size must be non-negative")

    if not approved:
        return TradeDecision(
            action="HOLD",
            size=0.0,
            rationale=text.strip(),
            approved=False,
        )

    return TradeDecision(
        action=action,
        size=size,
        rationale=text.strip(),
        approved=True,
    )


def format_decision(decision: TradeDecision) -> str:
    if decision.action == "HOLD":
        return "HOLD size=0"
    return f"{decision.action} size={decision.size:g}"
