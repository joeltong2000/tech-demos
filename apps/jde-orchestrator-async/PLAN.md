# Plan: JDE Orchestrator fire-and-forget (async) calls

## 1. Goal

Demonstrate JD Edwards EnterpriseOne Orchestrator's per-call job queue override: passing
`"jde__jobQueue": "JDE__ASYNCH"` in the request body makes the AIS server accept the call
immediately with **HTTP 202** (fire and forget) instead of blocking until the orchestration
finishes (HTTP 200 with output). The happy path is one command, `bun run demo`, which calls
the same orchestration twice against a local mock AIS server and prints the timings side by side.

## 2. Constraints

- Runtime: **Bun** (TypeScript), per repo rules. Optional PowerShell client script included
  but pwsh may not run on this VM.
- No live JDE/AIS server is available. Default mode is a **local mock AIS server** that
  simulates a slow orchestration and honors the documented `jde__jobQueue` override values.
- Real mode (pointing at an actual AIS server with basic auth) is configured via env vars
  documented in `.env.example`. No secrets committed.
- Follow the Oracle doc's actual parameter names (`jde__jobQueue`, `JDE__ASYNCH` — double
  underscores). Anything the docs don't specify (e.g. the 202 response body) is an assumption
  called out in the README.
- Out of scope: Orchestrator Studio design, UBE report status polling against a real server,
  token-based auth, any paid tooling.

## 3. Steps

1. [x] Read the Oracle doc; confirm parameter names and the five valid queue override values.
2. [x] Commit this plan.
3. [x] Scaffold Bun app: `package.json`, `tsconfig.json`, `.env.example`.
4. [x] Build `src/mock-ais.ts`: mock `POST /jderest/v3/orchestrator/{name}` that sleeps a few
   seconds for sync calls (200 + output) and returns 202 immediately for `JDE__ASYNCH` /
   `JDE__USER_ASYNCH`, while recording run details in a mock Orchestrator Monitor store
   (`GET /mock/monitor/runs`).
5. [x] Build `src/demo.ts`: call the same orchestration twice (sync, then async override),
   print a side-by-side timing table, then poll the mock monitor until the async run completes.
6. [x] Add optional `scripts/demo.ps1` PowerShell client doing the same two calls.
7. [x] Write README: what JDE__ASYNCH is, trade-offs, how to run, mock vs real mode, sample output.
8. [x] Capture validation artifacts: terminal screenshot + screen recording of `bun run demo`.
9. [x] Add tracking entry to `tracking/seen-bookmarks.json`; open PR with artifacts.

## 4. Success criteria

- `cd apps/jde-orchestrator-async && bun install && bun run demo` works offline with no config.
- Reviewer sees: sync call returns HTTP 200 after ~4 s with the orchestration output; async
  call with `"jde__jobQueue": "JDE__ASYNCH"` returns HTTP 202 in milliseconds with no output;
  a timing table contrasts the two; the mock monitor then shows the async run finishing
  Queued → Running → Successful.
- Artifacts: screenshot of the terminal output and a short screen recording, attached to the PR.
