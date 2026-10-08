# Plan: PSAIOpenAIDecisions ticket-triage demo

## 1. Goal

Demonstrate [PSAIOpenAIDecisions](https://github.com/dfinke/PSAIOpenAIDecisions) (Doug Finke's PowerShell client for the OpenAI Decisions API) by piping a batch of support tickets through all three decision shapes — yes/no (predicate), multiple-choice routing, and ordered scoring — in a single PowerShell pipeline. The happy path runs fully offline against a local Bun mock of `POST /v1/decisions`, so a reviewer needs no OpenAI key.

## 2. Constraints

- **Runtimes:** Bun for the mock Decisions API server and orchestration (monorepo standard); PowerShell 7 (`pwsh`) for the pipeline demo itself, since the subject is a PowerShell module.
- **Module install:** the real `PSAIOpenAIDecisions` module is installed from PowerShell Gallery on first run (no credentials needed). The demo never patches the module; it redirects it to the mock via the module's own `-Endpoint` parameter (applied through `$PSDefaultParameterValues`).
- **Credentials:** none required for the happy path. `.env.example` documents the optional `OPENAI_API_KEY` + real-mode switch; default is mock. In mock mode a placeholder key is set in-process only (the module refuses to run with an empty key).
- **Out of scope:** image inputs, the module's Excel examples, `Find-OpenAIDecision`/tagging commands, any UI beyond the terminal, live-mode testing against the real API.

## 3. Steps

1. [x] Scaffold `apps/psai-openai-decisions/` and commit this plan.
2. [x] Mock server (`mock/server.ts`): Bun HTTP server implementing `POST /v1/decisions` with deterministic keyword-overlap heuristics for predicate / choice / score answers, matching the module's expected wire format.
3. [x] Sample data (`data/tickets.csv`): eight support tickets crafted so mock decisions look sensible.
4. [x] Demo script (`demo/TicketTriage.ps1`): installs/imports the module, then pipes tickets through `Invoke-OpenAIDecision`, `Select-OpenAIDecision` (yes/no), `Get-OpenAIDecisionChoice` (routing), and `Get-OpenAIDecisionScore` (urgency), ending in a triage board table.
5. [x] Orchestrator (`scripts/run-demo.ts`): starts the mock server, health-checks it, runs `pwsh demo/TicketTriage.ps1`, shuts the server down. Wired to `bun run demo`.
6. [x] README + `.env.example` (mock vs real mode).
7. [x] Run end-to-end in mock mode; capture screenshot + short video of the happy path.
8. [x] Add `tracking/seen-bookmarks.json` entry; open PR with artifacts.

## 4. Success criteria

- `cd apps/psai-openai-decisions && bun install && bun run demo` completes with exit code 0 and no credentials set.
- The reviewer sees: the mock server start, one full `Invoke-OpenAIDecision` result (probability + choice + score for a single ticket), tickets filtered by the yes/no gate, each ticket routed to billing/technical/account, and a final triage board sorted by urgency score.
- Artifacts: screenshot of the final triage board and a short video of the run, both linked from the PR.
