# Microsoft Agent Framework builder skills — with vs. without

Demo of the official **coding-agent builder skills** for Microsoft Agent Framework
(`.NET` + `Python`), announced in the
[Nov 4 2026 Agent Framework blog post](https://devblogs.microsoft.com/agent-framework/give-your-coding-agent-a-head-start-with-microsoft-agent-framework-skills-for-net-and-python/).

These are **development-time** skills for your coding assistant (Agent Skills format),
not runtime skills loaded by the shipped app.

## What this shows

The same small offline **JD Edwards ops helper** agent — two function tools over a local
JSON mock of WSJ ("Work with Submitted Jobs") — built four ways:

| Variant | Path |
| --- | --- |
| .NET without skill | `dotnet/baseline` |
| .NET with skill | `dotnet/with-skill` |
| Python without skill | `python/baseline.py` |
| Python with skill | `python/with_skill.py` |

Read [`COMPARISON.md`](./COMPARISON.md) for the concrete differences (packages, APIs,
errors, honesty about how small some of them are).

## Official skills (vendored here)

Installed from `microsoft/agent-framework` into `vendor/skills/` at the commit in
`vendor/skills/PINNED_COMMIT.txt`. Equivalent to the post's install commands:

```bash
gh skill install microsoft/agent-framework agent-framework-builder-dotnet@main
gh skill install microsoft/agent-framework agent-framework-builder-python@main
```

### What each skill teaches (summary)

Both skills are entry points: inspect the project → pick the **smallest** matching pattern →
read only that reference → validate against **current** APIs (not remembered preview syntax).

| Skill | Teaches |
| --- | --- |
| `agent-framework-builder-dotnet` | Core abstractions (`IChatClient`, `AIAgent` / `ChatClientAgent`, harness, workflows); when to use plain agent vs harness vs workflow; NuGet package narrowing (`Microsoft.Agents.AI.*`); DI/hosting; fake `IChatClient` for tests; provider tables (`AsAIAgent`); tools via `AIFunctionFactory` + approvals; sessions/history/context providers |
| `agent-framework-builder-python` | Core abstractions (`SupportsChatGetResponse`, `Agent`, harness via `create_harness_agent`, workflows); narrow distributions (`agent-framework-core` / provider packages, not the meta-package by default); `@tool` + approval modes; custom `BaseChatClient` layer order; explicit `load_dotenv()`; sessions/history/`ContextProvider` |

Companion mentioned in the post: Microsoft Learn MCP at `https://learn.microsoft.com/api/mcp`.

## Prerequisites

- **.NET SDK 9+** (packages also multi-target; this demo uses `net9.0`)
- **Python 3.11+** with [uv](https://github.com/astral-sh/uv)
- No API keys for the default path

Bun is not used: both SDKs are .NET / Python.

## Setup

```bash
# .NET
cd apps/agent-framework-skills/dotnet
dotnet restore

# Python (narrow core package)
cd apps/agent-framework-skills/python
uv sync
```

Optional live providers: copy `.env.example` → `.env` and set values. The apps stay on
`AF_CHAT_MODE=scripted` unless you extend the client factory for a real provider.

## Run (happy path — no keys)

From the repo root (or the language folder):

```bash
# .NET
dotnet run --project apps/agent-framework-skills/dotnet/baseline
dotnet run --project apps/agent-framework-skills/dotnet/with-skill

# Python
cd apps/agent-framework-skills/python
uv run python baseline.py
uv run python with_skill.py
```

Expected: each prints a user prompt for job `570213`, a `GetJobStatus` / `get_job_status`
tool call, a JSON tool result with status `E` (Error) for R31410, and a short final answer.

## Mock data

`data/jde-jobs.json` — fake JDE batch jobs. Tools:

- `GetJobStatus` / `get_job_status(job_number)`
- `ListActiveJobs` / `list_active_jobs()`

## What the comparison shows

See [`COMPARISON.md`](./COMPARISON.md). Short version: the skills mainly fixed MEAI major
version selection, steered Python to `agent-framework-core`, preferred `AsAIAgent` /
official tool styles, and formalized offline fake-client testing. The runtime transcript
for this tiny agent is nearly identical with or without the skill.

## Layout

```text
apps/agent-framework-skills/
  PLAN.md
  README.md
  COMPARISON.md
  .env.example
  data/jde-jobs.json
  vendor/skills/          # official builder skills (pinned)
  dotnet/{baseline,with-skill}/
  python/{baseline.py,with_skill.py,pyproject.toml}
  artifacts/              # screenshot + recording for the PR
```

## Validation artifacts

- Screenshot: [`artifacts/screenshot-run.png`](./artifacts/screenshot-run.png)
- Recording: [`artifacts/demo-run.mp4`](./artifacts/demo-run.mp4) (all four variants)
- Raw log: [`artifacts/run-output.txt`](./artifacts/run-output.txt)

Or regenerate locally:

```bash
./apps/agent-framework-skills/run-all.sh
```
