"""Tests for paper-trade ledger."""

from __future__ import annotations

from pathlib import Path

import pytest

from tradingagents_debate.decision import TradeDecision
from tradingagents_debate.ledger import STARTING_CASH, Ledger, load_ledger, save_ledger


def test_starting_cash() -> None:
    ledger = Ledger()
    assert ledger.cash == STARTING_CASH == 2000.0


def test_buy_then_sell_updates_cash_and_shares(tmp_path: Path) -> None:
    ledger = Ledger()
    buy = TradeDecision(action="BUY", size=10, rationale="buy", approved=True)
    rec = ledger.apply(
        ticker="NVDA",
        decision=buy,
        price=100.0,
        seed=1,
        llm_mode="mock",
        as_of="2024-11-15",
    )
    assert rec["action"] == "BUY"
    assert ledger.cash == pytest.approx(1000.0)
    assert ledger.position_shares("NVDA") == 10

    sell = TradeDecision(action="SELL", size=4, rationale="trim", approved=True)
    ledger.apply(
        ticker="NVDA",
        decision=sell,
        price=110.0,
        seed=1,
        llm_mode="mock",
        as_of="2024-11-15",
    )
    assert ledger.position_shares("NVDA") == 6
    assert ledger.cash == pytest.approx(1440.0)

    path = tmp_path / "ledger.json"
    save_ledger(ledger, path)
    loaded = load_ledger(path)
    assert loaded.cash == ledger.cash
    assert loaded.position_shares("NVDA") == 6
    assert len(loaded.trades) == 2


def test_rejected_trade_is_hold(tmp_path: Path) -> None:
    ledger = Ledger()
    decision = TradeDecision(action="HOLD", size=0, rationale="rejected", approved=False)
    rec = ledger.apply(
        ticker="TSM",
        decision=decision,
        price=190.0,
        seed=7,
        llm_mode="mock",
        as_of="2024-11-15",
    )
    assert rec["action"] == "HOLD"
    assert ledger.cash == STARTING_CASH
    path = tmp_path / "l.json"
    save_ledger(ledger, path)
    assert load_ledger(path).trades[0]["approved"] is False


def test_buy_clipped_to_cash() -> None:
    ledger = Ledger(cash=50.0)
    decision = TradeDecision(action="BUY", size=100, rationale="too big", approved=True)
    rec = ledger.apply(
        ticker="QS",
        decision=decision,
        price=10.0,
        seed=0,
        llm_mode="mock",
        as_of="2024-11-15",
    )
    assert rec["size"] == 5.0
    assert ledger.cash == pytest.approx(0.0)
