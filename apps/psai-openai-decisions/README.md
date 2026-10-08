# PSAIOpenAIDecisions: ticket triage in a PowerShell pipeline

Demo of [PSAIOpenAIDecisions](https://github.com/dfinke/PSAIOpenAIDecisions), Doug Finke's PowerShell client for the [OpenAI Decisions API](https://developers.openai.com/api/docs/guides/decisions). Eight support tickets are piped through all three decision shapes the API offers:

1. **Yes/no (predicate)** — `Select-OpenAIDecision` keeps only tickets where the customer is truly blocked (probability ≥ 0.7).
2. **Multiple choice** — `Get-OpenAIDecisionChoice` routes every ticket to `general` / `billing` / `technical` / `account`.
3. **Scoring** — `Get-OpenAIDecisionScore` rates urgency on an ordered `Low → Critical` scale.

The run ends with a triage board sorted by urgency. The real, unmodified module from PowerShell Gallery is used; only the endpoint is redirected.

**HOW-TO video:** [`docs/tutorial.mp4`](docs/tutorial.mp4) — a ~2.5 minute captioned walkthrough covering prerequisites, running the demo, the three pipeline commands in the script, a custom one-liner against the mock, and how to switch to real mode.

## Run it (mock mode, no credentials)

Prerequisites: [Bun](https://bun.sh) and [PowerShell 7+](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) (`pwsh`).

```sh
cd apps/psai-openai-decisions
bun install
bun run demo
```

`bun run demo` starts a local mock of `POST /v1/decisions` (`mock/server.ts`), installs the `PSAIOpenAIDecisions` module from PowerShell Gallery on first run, executes `demo/TicketTriage.ps1` against the mock, and shuts everything down. No OpenAI key is needed: the demo sets a placeholder key in-process (the module requires a non-empty `OPENAI_API_KEY`) and the mock accepts any bearer token.

## Mock vs real mode

| | Mock (default) | Real |
|---|---|---|
| Endpoint | `http://127.0.0.1:4100/v1/decisions` | `https://api.openai.com/v1/decisions` |
| Credentials | none | `OPENAI_API_KEY` |
| Answers | deterministic keyword/concept heuristics | `gpt-6-luna` |

The mock speaks the module's exact wire format and derives every answer from one signal: how many input tokens match the question directly or through a shared concept group (see `mock/lexicon.ts`). Same input, same answer, every run.

To go live, set both variables from `.env.example` (`OPENAI_API_KEY` and `PSAI_MODE=real`) in your shell and run `bun run demo` again — the mock is skipped and the module calls OpenAI for real. Live calls cost money; nothing in this demo requires them.

## How the redirect works

`Invoke-OpenAIDecision` exposes an `-Endpoint` parameter, but the pipeline commands (`Select-OpenAIDecision`, `Get-OpenAIDecisionChoice`, `Get-OpenAIDecisionScore`) call it internally without surfacing that parameter, and a `$PSDefaultParameterValues` entry in the caller's scope is invisible to calls made inside a module. The demo bridges this by setting the default parameter value in the module's own session state — no module patching:

```powershell
& (Get-Module PSAIOpenAIDecisions) {
    param($Endpoint)
    $script:PSDefaultParameterValues = @{ 'Invoke-OpenAIDecision:Endpoint' = $Endpoint }
} $endpoint
```

## Layout

- `demo/TicketTriage.ps1` — the PowerShell pipeline demo.
- `mock/server.ts`, `mock/lexicon.ts` — Bun mock of the Decisions API.
- `data/tickets.csv` — sample tickets.
- `scripts/run-demo.ts` — orchestrator behind `bun run demo`.
