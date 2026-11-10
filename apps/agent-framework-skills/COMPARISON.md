# With-skill vs without-skill comparison

Honest comparison of building the same offline JD Edwards ops-helper agent **before**
reading the official Microsoft Agent Framework builder skills, then **after**.

Skills used (vendored at `vendor/skills/`, pinned commit in `PINNED_COMMIT.txt`):

- `agent-framework-builder-dotnet` (v0.1 metadata)
- `agent-framework-builder-python` (v0.3 metadata)

Install method confirmed from the [Nov 4 2026 blog post](https://devblogs.microsoft.com/agent-framework/give-your-coding-agent-a-head-start-with-microsoft-agent-framework-skills-for-net-and-python/):

```bash
gh skill install microsoft/agent-framework agent-framework-builder-dotnet@main
gh skill install microsoft/agent-framework agent-framework-builder-python@main
# or: npx skills add microsoft/agent-framework --skill agent-framework-builder-dotnet
```

This demo vendors the skill trees from `microsoft/agent-framework` (`skills/…`) so the
comparison is reproducible without depending on a particular coding-agent skill installer.

## Bottom line

**Differences are real but modest for this small plain-agent demo.** Both baselines already
produced a working tool-calling agent once package APIs were inspected. The skills mainly
corrected *package selection*, *preferred construction patterns*, *pattern sizing*
(plain agent vs harness/workflow), and *offline validation guidance* — they did not change
the happy-path runtime transcript in a large way.

## Package names and versions (verified at build time)

| Surface | Baseline guess | Skill / registry correction | Used |
| --- | --- | --- | --- |
| .NET agent package | `Microsoft.Agents.AI` 1.28.0 (correct from NuGet) | Same; add only narrow packages | `Microsoft.Agents.AI` 1.28.0 |
| .NET MEAI | Guessed `Microsoft.Extensions.AI` **9.10.0** | Agents.AI 1.28.0 requires **≥10.11.0** | **10.11.0** (restore failed with NU1605 until bumped) |
| Python package | Meta-package `agent-framework==1.25.0` | Skill Defaults: prefer **narrow** distribution (`agent-framework-core`) | Baseline: meta; with-skill: `agent-framework-core==1.25.0` |

## API / pattern differences

### .NET

| Topic | Without skill (baseline) | With skill |
| --- | --- | --- |
| Agent construction | `new ChatClientAgent(chatClient, instructions, name, description, tools)` | `chatClient.AsAIAgent(...)` — skill's documented stable pattern |
| Tools | Instance methods on `JdeJobStore` via `AIFunctionFactory.Create` | Static methods + `[Description]` matching official `02_add_tools` sample |
| Session | None (stateless single call) | `CreateSessionAsync()` + `RunAsync(prompt, session)` |
| Offline client | Hand-rolled `IChatClient` | Same idea, but justified by skill Validation §3 ("fake IChatClient") and Extensibility |
| Pattern choice | Implicitly "one agent" | Explicitly selected **plain agent** path; rejected harness/workflow as overkill |
| Live provider | Not structured | `AF_CHAT_MODE` switch + skill provider table notes (OpenAI / Foundry) |

### Python

| Topic | Without skill (baseline) | With skill |
| --- | --- | --- |
| First-guess names (pre-fix) | Remembered `ChatAgent` / `@ai_function` (stale) | Skill + samples: `Agent` / `@tool` |
| Package | Installed `agent-framework` meta (pulls many optional integrations) | `agent-framework-core` only |
| Tools | `@tool` on instance methods | Module-level `@tool(approval_mode="never_require")` like `02_add_tools.py` |
| Custom client | `FunctionInvocationLayer, BaseChatClient` (discovered via introspection) | Same layering, but **documented order** from extensibility.md / `custom_chat_client.py` |
| Session | None | `agent.create_session()` passed to `run` |
| `.env` | Not loaded | Skill: call `load_dotenv()` explicitly when live mode is requested |

## Errors hit while building the baseline

1. **NU1605 package downgrade** — adding `Microsoft.Extensions.AI` 9.10.0 against
   `Microsoft.Agents.AI` 1.28.0 (needs ≥10.11.0). Fixed by bumping MEAI.
2. Stale name memory for Python (`ChatAgent`, `@ai_function`) — corrected by inspecting the
   installed `agent_framework` public exports before the baseline could run. The skill's
   agent-builder reference would have steered straight to `Agent` / `@tool`.
3. No functional runtime errors after the above; both languages' function-invocation layers
   executed the scripted tool call deterministically.

## Build / run results

All four variants build and run with **no API keys** (`AF_CHAT_MODE=scripted` default):

```text
dotnet run --project apps/agent-framework-skills/dotnet/baseline
dotnet run --project apps/agent-framework-skills/dotnet/with-skill
cd apps/agent-framework-skills/python && uv run python baseline.py
cd apps/agent-framework-skills/python && uv run python with_skill.py
```

Each prints the same logical transcript:

1. User asks for job `570213`
2. Model (scripted) emits `GetJobStatus` / `get_job_status` tool call
3. Tool returns JSON with status `E` / Error and the mock errorText
4. Final assistant text summarizes R31410 / Work Order Processing failure

## What the skill would have prevented / improved

- Immediate steer to **plain agent** (avoid overbuilding a workflow for two read-only tools).
- Correct MEAI major version expectation via "validate against current APIs".
- Prefer **narrow** Python distribution instead of the heavy meta-package.
- Prefer `AsAIAgent` / official sample tool style and explicit session creation.
- Explicit offline testing guidance (fake `IChatClient` / custom `BaseChatClient`) that matches
  this demo's CI-friendly design.
- Provider tables for switching to OpenAI / Foundry without inventing package names.

## What the skill did *not* change much

- The core tool-calling loop shape (scripted model turn → local tool → final text) is the same.
- Mock JDE data and tool semantics are identical across variants.
- Runtime output for the happy path is effectively the same string.
