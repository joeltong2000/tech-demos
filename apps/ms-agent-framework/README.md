# Trip Briefing Agent — Microsoft Agent Framework demo

A small web demo of [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (Python SDK). Type a city; an agent plans two tool calls — `get_weather` and `get_local_time`, backed by live [Open-Meteo](https://open-meteo.com/) data — the framework executes them, and the agent composes a trip briefing. The UI shows every step of the agent loop: user message → tool calls (with arguments) → tool results → final answer.

## Run it

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and network access.

```bash
cd apps/ms-agent-framework
uv run main.py
```

Open http://localhost:8787 and enter a city (or click an example chip).

No API key is needed: without `OPENAI_API_KEY` the demo uses a deterministic
`ScriptedPlannerClient` in place of the LLM. The agent loop, tool schemas, tool
execution, and message threading are all real Microsoft Agent Framework
machinery — only the model's "reasoning" is scripted. The tools fetch live data.

## Optional: real LLM mode

```bash
cp .env.example .env
# set OPENAI_API_KEY (and optionally OPENAI_CHAT_MODEL_ID / OPENAI_BASE_URL)
uv run main.py
```

The header badge shows which model client is active (`offline scripted planner` or `openai:<model>`).

## How it works

- `briefing_agent.py` — two `@tool` functions (Open-Meteo geocoding + forecast); `ScriptedPlannerClient`, a `FunctionInvocationLayer + BaseChatClient` implementation that emits `function_call` contents on the first pass and composes the briefing from `function_result` contents on the second; `build_agent()` wires an `Agent` with instructions and tools, choosing `OpenAIChatClient` or the scripted client from env.
- `main.py` — FastAPI server. `POST /api/briefing` runs the agent and flattens `response.messages` into a JSON step trace; `GET /api/health` reports the active mode; static files serve the UI.
- `static/index.html` — single-page UI rendering the agent trace.

## API

```bash
curl -s -X POST localhost:8787/api/briefing \
  -H 'Content-Type: application/json' -d '{"city":"Kyoto"}'
```

Returns `{"mode": ..., "final": ..., "steps": [...]}` where `steps` is the ordered agent trace.
