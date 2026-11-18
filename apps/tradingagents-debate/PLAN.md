# Plan: TradingAgents-style multi-agent debate (offline)

Written per `skills/project-planning/SKILL.md`.

## 1. Goal

Show a self-contained, offline Python demo of a [TradingAgents](https://github.com/TauricResearch/TradingAgents)-style debate: fundamentals / sentiment / news / technical analysts → bull vs bear researchers → trader proposal → risk manager verdict. The happy path is one command that prints a colored transcript and appends a paper trade to a local ledger (starting cash $2,000).

## 2. Constraints

- **Python 3.11+** with **uv** (or plain pip + pinned `requirements.txt`). Not Bun — the subject is a Python multi-agent trading framework.
- **Offline by default**: mock/scripted LLM + bundled JSON market data. No API keys required. Optional `OPENAI_API_KEY` / compatible base URL via `.env.example` only (off by default).
- Real `tradingagents` package is not used: it needs live LLM providers and market APIs and is not a clean offline PyPI install. This demo is a **faithful minimal reimplementation** of the published roles and flow.
- Out of scope: real brokers, live market feeds, LangGraph, backtests, paid services.

## 3. Steps

1. Scaffold `apps/tradingagents-debate/` with `pyproject.toml`, `requirements.txt`, `.env.example`.
2. Bundle mock prices + headlines for NVDA, TSM, QS.
3. Implement agents, debate orchestrator, colored transcript, paper ledger (`--seed` for determinism).
4. Add pytest coverage for ledger updates and decision parsing.
5. Write README (what TradingAgents is, mapping, one-command run, sample output, disclaimer).
6. Run happy path + tests; capture terminal screenshot + short screen recording; attach to PR.
7. Add tracking entry for the inspiration pick.

## 4. Success criteria

- `cd apps/tradingagents-debate && uv run debate --ticker NVDA --seed 42` prints a full colored debate and a final BUY/SELL/HOLD with size, then appends to `ledger.json`.
- Re-running with the same `--seed` yields the same decision text (deterministic mock path).
- `uv run pytest` passes.
- PR includes a PNG screenshot and an MP4/GIF of a full run.

## Status

Built as a faithful minimal reimplementation (upstream TradingAgents needs live LLMs/APIs). Happy path, tests, and `validation/` artifacts included.
