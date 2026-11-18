"""Tests for decision parsing."""

from __future__ import annotations

import pytest

from tradingagents_debate.decision import format_decision, parse_decision


def test_parse_final_decision_buy_with_size() -> None:
    text = "Weighing both sides.\nFINAL DECISION: BUY size=12"
    d = parse_decision(text)
    assert d.action == "BUY"
    assert d.size == 12
    assert d.approved is True


def test_parse_hold_forces_zero_size() -> None:
    d = parse_decision("FINAL DECISION: HOLD size=5")
    assert d.action == "HOLD"
    assert d.size == 0.0


def test_reject_forces_hold() -> None:
    text = "Risk Manager: REJECT — too large. FINAL DECISION: BUY size=99"
    d = parse_decision(text)
    assert d.approved is False
    assert d.action == "HOLD"
    assert d.size == 0.0


def test_parse_sell_quantity_alias() -> None:
    d = parse_decision("Sell into strength. SELL quantity=3.5")
    assert d.action == "SELL"
    assert d.size == 3.5


def test_empty_raises() -> None:
    with pytest.raises(ValueError, match="Empty"):
        parse_decision("   ")


def test_missing_action_raises() -> None:
    with pytest.raises(ValueError, match="Could not parse"):
        parse_decision("No actionable call here.")


def test_format_decision() -> None:
    d = parse_decision("FINAL DECISION: BUY size=2")
    assert format_decision(d) == "BUY size=2"
