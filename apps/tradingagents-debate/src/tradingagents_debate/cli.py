"""CLI entrypoint: ``uv run debate --ticker NVDA --seed 42``."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from tradingagents_debate.debate import run_debate
from tradingagents_debate.market import available_tickers


def build_parser() -> argparse.ArgumentParser:
    tickers = ", ".join(available_tickers())
    parser = argparse.ArgumentParser(
        prog="debate",
        description=(
            "Offline TradingAgents-style multi-agent debate (paper trades only). "
            "Not financial advice."
        ),
    )
    parser.add_argument(
        "--ticker",
        "-t",
        default="NVDA",
        help=f"Ticker to debate (bundled: {tickers})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Determinism seed for the mock LLM / heuristics (default: 42)",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("ledger.json"),
        help="Paper-trade ledger JSON path (default: ./ledger.json)",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Print the debate without writing the ledger",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress transcript; still updates the ledger unless --no-persist",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Optional dotenv load when present (live LLM path).
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_debate(
            args.ticker,
            seed=args.seed,
            ledger_path=args.ledger,
            print_transcript=not args.quiet,
            persist=not args.no_persist,
        )
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        d = result.decision
        print(
            f"{result.snapshot.ticker} {d.action} size={d.size:g} "
            f"approved={d.approved} cash={result.ledger.cash:.2f}"
        )

    # Hint when someone expected live mode but got mock.
    if result.llm_mode == "mock" and os.getenv("OPENAI_API_KEY"):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
