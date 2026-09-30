# Rules for agents working in this repo

This is Joe's sticky tech-demos monorepo. Every demo lives here — never create a new repository for a demo.

1. **Only touch `apps/`** for demo code. One app per `apps/<slug>/` directory. Root-level files (`AGENTS.md`, `skills/`, `tracking/`) change only when the task explicitly requires it.
2. **Plan before coding.** Follow `skills/project-planning/SKILL.md` and commit the resulting `PLAN.md` inside the app folder.
3. **Every PR must include validation artifacts**: at least one screenshot AND one short video of the running app, attached to the PR or committed and clearly linked from the PR description.
4. **Bun is the package manager** for JavaScript/TypeScript apps. Do not use npm, yarn, or pnpm. For demos whose subject requires another runtime (e.g. a Python-only SDK), use that runtime's standard tooling and say so in the app README.
5. **Never commit secrets.** API keys are documented via `.env.example` only. Apps should degrade gracefully (or ship an offline mode) when keys are absent.
6. **Track picks.** When building a demo from a bookmark/pick, add an entry to `tracking/seen-bookmarks.json` in the same PR.
7. **Keep scope tight.** One clear happy path a reviewer can run locally with a single documented command.
