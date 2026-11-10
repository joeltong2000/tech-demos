# Plan: Microsoft Agent Framework builder skills — with vs. without

## 1. Goal

Show what difference the official Microsoft Agent Framework **builder skills** for coding agents
(`agent-framework-builder-dotnet`, `agent-framework-builder-python`, announced Nov 4 2026 on the
Agent Framework blog) make when a coding agent builds a small tool-calling agent. The happy path:
run the same offline "JDE ops helper" agent in four variants — .NET baseline, .NET skill-guided,
Python baseline, Python skill-guided — and read `COMPARISON.md` for the concrete differences.

## 2. Constraints

- Runtimes: .NET 9 SDK (C#) and Python 3.12 via **uv** (the Python Agent Framework SDK requires
  ≥3.11, so Bun does not apply; no JS tooling is needed).
- Packages come only from official sources verified at build time: NuGet `Microsoft.Agents.AI`
  1.28.0 and PyPI `agent-framework` 1.25.0.
- **No API keys, no paid services.** Both agents run against a scripted mock chat client
  (deterministic function-call → final-answer sequence). `.env.example` documents how a real
  provider (OpenAI / Azure OpenAI) would be wired instead. No secrets in the repo.
- Honesty rule for the comparison: the *baseline* variants are written from the coding agent's
  generic pre-trained knowledge **before** reading any skill content; the *with-skill* variants are
  written after reading the vendored skills. Differences, however small, are recorded truthfully.
- Out of scope: workflows/multi-agent orchestration, hosting, real JD Edwards connectivity,
  real model calls in CI.

## 3. Steps

1. [x] Create `apps/agent-framework-skills/` and this plan.
2. [x] Verify real package names/versions on NuGet and PyPI; confirm skill names and location in
   `microsoft/agent-framework` (`skills/agent-framework-builder-{dotnet,python}`).
3. [x] Write baseline agents (.NET + Python) from generic knowledge only; record every error hit.
4. [x] Vendor the two official skills at a pinned commit into `vendor/skills/` (the repo-level
   equivalent of `gh skill install microsoft/agent-framework agent-framework-builder-dotnet@main`).
5. [x] Read the skills; write the skill-guided agents following their guidance.
6. [x] Shared mock data: `data/jde-jobs.json` with fake JD Edwards batch-job records; tools
   `get_job_status` + `list_active_jobs` in both languages.
7. [x] Verify all four variants build and run deterministically offline.
8. [x] Write `README.md`, `COMPARISON.md`, `.env.example`; add tracking entry.
9. [x] Capture validation artifacts: screenshot + terminal recording (mp4) of both agents running.
10. [x] Open PR with artifacts linked (https://github.com/joeltong2000/tech-demos/pull/7).

## 4. Success criteria

- `cd apps/agent-framework-skills/dotnet && dotnet run --project with-skill` prints a deterministic
  agent transcript: user question → `get_job_status` tool call with arguments → tool result →
  final answer naming job `570212/WEDI0012` status, with **no keys set**.
- `cd apps/agent-framework-skills/python && uv run with_skill.py` does the same for Python.
- `baseline` variants run the same scenario (modulo the differences documented in COMPARISON.md).
- `COMPARISON.md` lists concrete with-vs-without differences: package names, APIs, patterns,
  errors hit, build/run results — and says plainly if they are small.
- Artifacts: at least one screenshot and one short recording of both agents running, linked
  from the PR body.
