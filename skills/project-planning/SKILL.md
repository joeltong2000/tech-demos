---
name: project-planning
description: Plan a demo app before writing any code. Use at the start of every new apps/<slug>/ demo.
---

# Project planning

Before writing code for a new demo, produce a short plan and commit it as `PLAN.md` in the app folder. The plan must contain these four sections:

## 1. Goal

One or two sentences: what the demo shows and why it is interesting. Name the specific technology being demonstrated and the single happy path a reviewer will run.

## 2. Constraints

- Runtime and package manager (Bun for JS/TS; otherwise justify).
- External services and credentials needed — keys go in `.env.example`, never in the repo.
- What is explicitly out of scope.

## 3. Steps

An ordered, checkable list from empty folder to running app. Each step should be small enough to verify independently. Include the step where validation artifacts (screenshot + video) are captured.

## 4. Success criteria

Concrete checks a reviewer can perform:

- The exact command(s) that start the app.
- What the reviewer should see when the happy path works.
- Which artifacts prove it (screenshot, video).

Keep the whole plan under a page. If the plan changes during implementation, update `PLAN.md` in the same PR — it documents what was actually built.
