# Plan: Microsoft Agent Framework demo (Trip Briefing Agent)

Written per `skills/project-planning/SKILL.md`.

## 1. Goal

Show something concrete about [Microsoft Agent Framework](https://github.com/microsoft/agent-framework): an agent that plans and executes a **multi-step tool-calling flow**. A reviewer types a city into a web UI; the agent calls two tools (`get_weather`, `get_local_time`, backed by live Open-Meteo data), the framework executes them and threads results back, and the agent composes a final briefing. The UI renders the entire agent loop — user message, tool calls with arguments, tool results, final answer.

## 2. Constraints

- Microsoft Agent Framework ships Python and .NET SDKs only (the npm name `@microsoft/agent-framework` is a 0.0.1-beta placeholder). This app therefore uses the **Python SDK** (`agent-framework-core` + `agent-framework-openai`) with **uv** for dependency management. Bun remains the monorepo standard for JS/TS apps per `AGENTS.md`.
- No secrets in the repo. `OPENAI_API_KEY` is optional and documented in `.env.example`. Without it, a deterministic `ScriptedPlannerClient` (a real `BaseChatClient` implementation) stands in for the LLM so the full agent loop runs offline.
- Out of scope: streaming responses, multi-agent workflows, chat history/threads, deployment.

## 3. Steps

1. Scaffold `apps/ms-agent-framework/` with uv; add `agent-framework-core`, `agent-framework-openai`, `fastapi`, `uvicorn`, `httpx`, `python-dotenv`.
2. Write two `@tool` functions calling Open-Meteo (geocoding + forecast, no API key).
3. Implement `ScriptedPlannerClient(FunctionInvocationLayer, BaseChatClient)` — first pass returns two `function_call` contents, second pass composes the briefing from `function_result` contents.
4. Build the `Agent` with instructions + tools; select OpenAI client vs scripted client from env.
5. FastAPI server: `POST /api/briefing` runs the agent and returns the step-by-step trace extracted from `response.messages`; static single-page UI renders it.
6. Verify the happy path locally (`uv run main.py`, query a city, confirm live tool results in the trace).
7. Capture validation artifacts: screenshot of the rendered trace + short video of the happy path; attach to the PR.

## 4. Success criteria

- `cd apps/ms-agent-framework && uv run main.py` starts the server on http://localhost:8787 with no `.env` present.
- Entering a city (e.g. "Kyoto") renders four trace sections: the user message, two tool calls with JSON arguments, two tool results containing **live** weather/time data, and a final briefing paragraph.
- `GET /api/health` reports the active model client mode.
- PR includes at least one screenshot and one video of the running app.

## How to validate

Run the app with no `.env`, click the "Kyoto" example chip, and check that the tool results show current data (the `local_time` field should match the present time in Japan). Optionally set `OPENAI_API_KEY` in `.env` and repeat — the trace shape is the same but planning/composition come from the LLM.
