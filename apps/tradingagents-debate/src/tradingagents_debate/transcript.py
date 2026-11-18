"""Colored terminal transcript rendering."""

from __future__ import annotations

import sys

from colorama import Fore, Style, init

from tradingagents_debate.agents import AgentMessage
from tradingagents_debate.decision import TradeDecision, format_decision

init(autoreset=True)

ROLE_COLORS = {
    "Fundamentals Analyst": Fore.CYAN,
    "Sentiment Analyst": Fore.MAGENTA,
    "News Analyst": Fore.BLUE,
    "Technical Analyst": Fore.YELLOW,
    "Bull Researcher": Fore.GREEN,
    "Bear Researcher": Fore.RED,
    "Trader": Fore.LIGHTWHITE_EX,
    "Risk Manager": Fore.LIGHTCYAN_EX,
}


def _stream() -> bool:
    return sys.stdout.isatty()


def print_banner(ticker: str, as_of: str, seed: int, llm_mode: str) -> None:
    line = (
        f"TradingAgents-style debate  |  {ticker}  |  as_of={as_of}  "
        f"|  seed={seed}  |  llm={llm_mode}"
    )
    color = Fore.WHITE + Style.BRIGHT if _stream() else ""
    print(f"{color}{'=' * len(line)}")
    print(f"{color}{line}")
    print(f"{color}{'=' * len(line)}{Style.RESET_ALL}")
    print()


def print_message(msg: AgentMessage) -> None:
    color = ROLE_COLORS.get(msg.role, Fore.WHITE) if _stream() else ""
    reset = Style.RESET_ALL if _stream() else ""
    bright = Style.BRIGHT if _stream() else ""
    print(f"{color}{bright}[{msg.role}]{reset} {color}{msg.title}{reset}")
    for line in msg.content.splitlines() or [msg.content]:
        print(f"  {color}{line}{reset}")
    print()


def print_decision(decision: TradeDecision, ledger_record: dict) -> None:
    color = Fore.GREEN if decision.approved and decision.action == "BUY" else (
        Fore.RED if decision.action == "SELL" else Fore.YELLOW
    )
    if not _stream():
        color = ""
    reset = Style.RESET_ALL if _stream() else ""
    bright = Style.BRIGHT if _stream() else ""
    status = "APPROVED" if decision.approved else "REJECTED→HOLD"
    print(f"{color}{bright}>>> FINAL: {format_decision(decision)} ({status}){reset}")
    print(
        f"  cash ${ledger_record['cash_after']:.2f}  |  "
        f"{ledger_record['ticker']} shares {ledger_record['shares_after']:g}  |  "
        f"fill px {ledger_record['price']}"
    )
    print()
