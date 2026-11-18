"""Orchestrate the full TradingAgents-style debate pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tradingagents_debate.agents import AgentMessage, DebateAgents
from tradingagents_debate.decision import TradeDecision, parse_decision
from tradingagents_debate.ledger import DEFAULT_LEDGER, Ledger, load_ledger, save_ledger
from tradingagents_debate.llm import LLMClient, resolve_llm
from tradingagents_debate.market import MarketSnapshot, get_snapshot
from tradingagents_debate.transcript import print_banner, print_decision, print_message


@dataclass
class DebateResult:
    snapshot: MarketSnapshot
    messages: list[AgentMessage]
    decision: TradeDecision
    ledger_record: dict[str, Any]
    ledger: Ledger
    llm_mode: str
    seed: int


def run_debate(
    ticker: str,
    *,
    seed: int = 42,
    ledger_path: Path | str = DEFAULT_LEDGER,
    market_path: Path | None = None,
    llm: LLMClient | None = None,
    llm_mode: str | None = None,
    print_transcript: bool = True,
    persist: bool = True,
) -> DebateResult:
    if llm is None:
        llm, llm_mode = resolve_llm(seed=seed)
    else:
        llm_mode = llm_mode or type(llm).__name__

    snap = get_snapshot(ticker, path=market_path)
    ledger = load_ledger(ledger_path)
    agents = DebateAgents(llm, seed=seed)

    messages: list[AgentMessage] = []

    # Analyst team (parallel conceptually; sequential for the transcript).
    analysts = [
        agents.fundamentals_analyst(snap),
        agents.sentiment_analyst(snap),
        agents.news_analyst(snap),
        agents.technical_analyst(snap),
    ]
    messages.extend(analysts)

    bull = agents.bull_researcher(snap, analysts)
    bear = agents.bear_researcher(snap, analysts)
    messages.extend([bull, bear])

    cash = ledger.cash
    position = ledger.position_shares(snap.ticker)
    trader_msg = agents.trader(
        snap, analysts, bull, bear, cash=cash, position=position
    )
    messages.append(trader_msg)

    proposed = parse_decision(trader_msg.content, approved=True)
    risk_msg = agents.risk_manager(
        snap,
        trader_msg,
        cash=cash,
        position=position,
        proposed_action=proposed.action,
        proposed_size=proposed.size,
    )
    messages.append(risk_msg)

    decision = parse_decision(risk_msg.content)

    if print_transcript:
        print_banner(snap.ticker, snap.as_of, seed, llm_mode or "mock")
        for msg in messages:
            print_message(msg)

    record = ledger.apply(
        ticker=snap.ticker,
        decision=decision,
        price=snap.last_close,
        seed=seed,
        llm_mode=llm_mode or "mock",
        as_of=snap.as_of,
    )

    if print_transcript:
        print_decision(decision, record)

    if persist:
        save_ledger(ledger, ledger_path)

    return DebateResult(
        snapshot=snap,
        messages=messages,
        decision=decision,
        ledger_record=record,
        ledger=ledger,
        llm_mode=llm_mode or "mock",
        seed=seed,
    )
