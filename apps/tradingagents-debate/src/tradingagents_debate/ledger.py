"""Paper-trade ledger (JSON) with $2,000 starting cash."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tradingagents_debate.decision import TradeDecision

STARTING_CASH = 2000.0
DEFAULT_LEDGER = Path("ledger.json")


@dataclass
class Position:
    shares: float = 0.0
    avg_cost: float = 0.0


@dataclass
class Ledger:
    cash: float = STARTING_CASH
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)

    def position_shares(self, ticker: str) -> float:
        pos = self.positions.get(ticker.upper())
        return pos.shares if pos else 0.0

    def equity(self, marks: dict[str, float] | None = None) -> float:
        total = self.cash
        marks = marks or {}
        for ticker, pos in self.positions.items():
            px = marks.get(ticker, pos.avg_cost)
            total += pos.shares * px
        return round(total, 2)

    def apply(
        self,
        *,
        ticker: str,
        decision: TradeDecision,
        price: float,
        seed: int,
        llm_mode: str,
        as_of: str,
    ) -> dict[str, Any]:
        ticker = ticker.upper()
        pos = self.positions.get(ticker) or Position()
        action = decision.action
        size = float(decision.size)
        cash_before = self.cash
        shares_before = pos.shares

        if not decision.approved or action == "HOLD" or size == 0:
            action = "HOLD"
            size = 0.0
        elif action == "BUY":
            cost = size * price
            if cost > self.cash + 1e-9:
                # Clip to affordable size.
                size = max(0.0, self.cash / price)
                cost = size * price
            if size <= 0:
                action = "HOLD"
                size = 0.0
            else:
                new_shares = pos.shares + size
                pos.avg_cost = (
                    ((pos.shares * pos.avg_cost) + cost) / new_shares if new_shares else 0.0
                )
                pos.shares = new_shares
                self.cash -= cost
        elif action == "SELL":
            size = min(size, pos.shares)
            if size <= 0:
                action = "HOLD"
                size = 0.0
            else:
                self.cash += size * price
                pos.shares -= size
                if pos.shares <= 1e-12:
                    pos.shares = 0.0
                    pos.avg_cost = 0.0

        self.positions[ticker] = pos
        if pos.shares == 0 and ticker in self.positions:
            # keep zero position for audit clarity
            pass

        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "as_of": as_of,
            "ticker": ticker,
            "action": action,
            "size": round(size, 6),
            "price": price,
            "approved": decision.approved,
            "cash_before": round(cash_before, 2),
            "cash_after": round(self.cash, 2),
            "shares_before": round(shares_before, 6),
            "shares_after": round(pos.shares, 6),
            "seed": seed,
            "llm_mode": llm_mode,
            "rationale": decision.rationale,
        }
        self.trades.append(record)
        return record

    def to_dict(self) -> dict[str, Any]:
        return {
            "starting_cash": STARTING_CASH,
            "cash": round(self.cash, 2),
            "positions": {
                t: {"shares": round(p.shares, 6), "avg_cost": round(p.avg_cost, 4)}
                for t, p in self.positions.items()
            },
            "trades": self.trades,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Ledger:
        positions = {
            t: Position(shares=float(p.get("shares", 0)), avg_cost=float(p.get("avg_cost", 0)))
            for t, p in (data.get("positions") or {}).items()
        }
        return cls(
            cash=float(data.get("cash", STARTING_CASH)),
            positions=positions,
            trades=list(data.get("trades") or []),
        )


def load_ledger(path: Path | str = DEFAULT_LEDGER) -> Ledger:
    path = Path(path)
    if not path.exists():
        return Ledger()
    with path.open(encoding="utf-8") as fh:
        return Ledger.from_dict(json.load(fh))


def save_ledger(ledger: Ledger, path: Path | str = DEFAULT_LEDGER) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(ledger.to_dict(), fh, indent=2)
        fh.write("\n")
