"""Load bundled mock market data and compute simple technicals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "market.json"


@dataclass(frozen=True)
class TechnicalSnapshot:
    last_close: float
    sma_5: float
    sma_20: float
    rsi_14: float
    momentum_5d_pct: float
    avg_volume_5: float
    trend: str


@dataclass(frozen=True)
class MarketSnapshot:
    ticker: str
    name: str
    sector: str
    as_of: str
    fundamentals: dict[str, Any]
    headlines: list[dict[str, Any]]
    prices: list[dict[str, Any]]
    technicals: TechnicalSnapshot

    @property
    def last_close(self) -> float:
        return self.technicals.last_close


def load_market(path: Path | None = None) -> dict[str, Any]:
    data_path = path or DATA_PATH
    with data_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def available_tickers(path: Path | None = None) -> list[str]:
    payload = load_market(path)
    return sorted(payload["tickers"].keys())


def _sma(closes: list[float], window: int) -> float:
    slice_ = closes[-window:]
    return sum(slice_) / len(slice_)


def _rsi(closes: list[float], window: int = 14) -> float:
    if len(closes) < window + 1:
        window = max(1, len(closes) - 1)
    gains: list[float] = []
    losses: list[float] = []
    for prev, cur in zip(closes[-(window + 1) : -1], closes[-window:]):
        delta = cur - prev
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-delta)
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_technicals(prices: list[dict[str, Any]]) -> TechnicalSnapshot:
    closes = [float(row["close"]) for row in prices]
    volumes = [float(row["volume"]) for row in prices]
    last = closes[-1]
    sma_5 = _sma(closes, min(5, len(closes)))
    sma_20 = _sma(closes, min(20, len(closes)))
    rsi = _rsi(closes, min(14, max(1, len(closes) - 1)))
    lookback = min(5, len(closes) - 1)
    momentum = ((last / closes[-(lookback + 1)]) - 1.0) * 100.0 if lookback else 0.0
    avg_vol = sum(volumes[-5:]) / min(5, len(volumes))
    if last > sma_20 * 1.01 and rsi < 70:
        trend = "uptrend"
    elif last < sma_20 * 0.99 or rsi > 70:
        trend = "overextended_or_soft"
    else:
        trend = "rangebound"
    return TechnicalSnapshot(
        last_close=round(last, 4),
        sma_5=round(sma_5, 4),
        sma_20=round(sma_20, 4),
        rsi_14=round(rsi, 2),
        momentum_5d_pct=round(momentum, 2),
        avg_volume_5=round(avg_vol, 0),
        trend=trend,
    )


def get_snapshot(ticker: str, path: Path | None = None) -> MarketSnapshot:
    payload = load_market(path)
    key = ticker.upper()
    if key not in payload["tickers"]:
        known = ", ".join(sorted(payload["tickers"]))
        raise KeyError(f"Unknown ticker {ticker!r}. Available: {known}")
    row = payload["tickers"][key]
    prices = list(row["prices"])
    return MarketSnapshot(
        ticker=key,
        name=row["name"],
        sector=row["sector"],
        as_of=payload["as_of"],
        fundamentals=dict(row["fundamentals"]),
        headlines=list(row["headlines"]),
        prices=prices,
        technicals=compute_technicals(prices),
    )
