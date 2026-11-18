# TradingAgents debate (offline demo)

A small, self-contained **Python** demo of a [TradingAgents](https://github.com/TauricResearch/TradingAgents)-style multi-agent trading debate. Analyst, bull/bear researcher, trader, and risk-manager agents argue over bundled mock market data, print a colored transcript, and append a **paper trade** to a local ledger (starting cash **$2,000**).

Inspiration: [TradingAgents](https://github.com/TauricResearch/TradingAgents) and [this post](https://x.com/gusik4ever/status/2116504471907791240).

> **Not financial advice. Paper trades only.** No real broker, no real money, no live market data in the default path.

## What TradingAgents is

[TradingAgents](https://github.com/TauricResearch/TradingAgents) is a research framework that mirrors a trading desk: specialized LLM agents (fundamentals / sentiment / news / technical analysts, bull & bear researchers, a trader, and risk / portfolio managers) debate before a decision. The upstream project expects live LLM providers and market data APIs.

## What this demo is (real vs mocked)

| Piece | This demo |
| --- | --- |
| Agent roles & debate order | **Real mapping** to TradingAgents (analysts → bull/bear → trader → risk) |
| LLM | **Mock / scripted by default** (deterministic with `--seed`). Optional OpenAI-compatible API via env (off by default) |
| Market data | **Bundled** JSON for `NVDA`, `TSM`, `QS` (synthetic daily bars + headlines) |
| Broker / exchange | **None** — paper ledger only |
| Upstream `tradingagents` package | **Not used** — it needs live providers and is not a clean offline install. This is a faithful minimal reimplementation of the published roles and flow |

## How to run (one command)

Requires **Python 3.11+**. Prefer [uv](https://docs.astral.sh/uv/):

```bash
cd apps/tradingagents-debate
uv sync --extra dev
uv run debate --ticker NVDA --seed 42
```

Plain pip:

```bash
cd apps/tradingagents-debate
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
debate --ticker NVDA --seed 42
```

Other tickers: `TSM`, `QS`. Ledger defaults to `./ledger.json` (gitignored).

```bash
uv run debate --ticker TSM --seed 7 --ledger /tmp/paper.json
uv run pytest
```

### Optional live LLM

Copy `.env.example` → `.env` and set `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL` / `OPENAI_MODEL`). Install extras: `uv sync --extra openai --extra dev`. Set `DEMO_LLM=mock` to force the offline path even when a key is present.

## Sample output

```
========================================================================
TradingAgents-style debate  |  NVDA  |  as_of=2024-11-15  |  seed=42  |  llm=mock
========================================================================

[Fundamentals Analyst] Company fundamentals
  Fundamentals lean constructive: NVIDIA Corporation (NVDA) — Semiconductors. ...

[Sentiment Analyst] Headline / social mood
  Short-term mood looks mixed. Avg headline sentiment +0.17 → mixed. ...

[News Analyst] Macro / event tape
  As of 2024-11-15: key wires — ...

[Technical Analyst] Price / indicators
  Technicals: momentum supportive. Last 150.5, ...

[Bull Researcher] Long thesis
  BULL case for NVDA: ...

[Bear Researcher] Short / caution thesis
  BEAR case for NVDA: ...

[Trader] Trade proposal
  Trader proposal after weighing bull/bear ... FINAL DECISION: BUY size=...

[Risk Manager] Risk / portfolio check
  Risk Manager: APPROVE — within paper-risk limits. FINAL DECISION: BUY size=...

>>> FINAL: BUY size=... (APPROVED)
  cash $...  |  NVDA shares ...  |  fill px 150.5
```

Re-running with the same `--seed` and a fresh ledger yields the same proposal text on the mock path.

## Layout

```
apps/tradingagents-debate/
  data/market.json          # bundled prices + headlines
  src/tradingagents_debate/ # agents, debate, ledger, CLI
  tests/                    # pytest (ledger + decision parsing)
  validation/               # terminal screenshot + short run video
  PLAN.md
  requirements.txt
  .env.example
```

## Validation artifacts

- Screenshot: [`validation/debate_terminal.png`](validation/debate_terminal.png)
- Screen recording: [`validation/debate_run.mp4`](validation/debate_run.mp4)

## Disclaimer

This demo is for **education and engineering illustration only**. It is **not** financial, investment, or trading advice. Outputs are driven by mock data and heuristics (or an optional third-party model you configure yourself). Do not trade real capital based on this tool.
