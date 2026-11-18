"""End-to-end determinism for the mock debate path."""

from __future__ import annotations

from pathlib import Path

from tradingagents_debate.debate import run_debate


def test_same_seed_same_decision(tmp_path: Path) -> None:
    a = run_debate(
        "NVDA",
        seed=42,
        ledger_path=tmp_path / "a.json",
        print_transcript=False,
        persist=True,
    )
    b = run_debate(
        "NVDA",
        seed=42,
        ledger_path=tmp_path / "b.json",
        print_transcript=False,
        persist=True,
    )
    assert a.decision.action == b.decision.action
    assert a.decision.size == b.decision.size
    assert [m.content for m in a.messages] == [m.content for m in b.messages]
