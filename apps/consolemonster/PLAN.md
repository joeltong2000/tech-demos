# PLAN — ConsoleMonster demo

## 1. Goal

Show what [ConsoleMonster](https://consolemonster.dev) (PowerShell Gallery module by Przemysław Kłys, v2.3.0, MIT) does for everyday PowerShell output: one-line tables from ordinary command output, live dashboards updated while a script works, and interactive menus and forms — capped with a themed mock "JD Edwards EnterpriseOne server health" dashboard driven by a local JSON file. The happy path a reviewer runs is `pwsh -File scripts/01-table.ps1` and friends.

## 2. Constraints

- Runtime: PowerShell 7 (`pwsh`) on the CI/VM; the module itself also supports Windows PowerShell 5.1 (PSGallery lists Desktop + Core editions). No Bun needed — the demo is pure PowerShell.
- Dependency: the `ConsoleMonster` module from PowerShell Gallery (`Install-Module ConsoleMonster -Scope CurrentUser`). Free, MIT, no module dependencies, no license key, no account.
- No secrets, no network calls at runtime: the JDE demo reads `data/jde-health.json`; nothing touches a real JDE instance.
- Out of scope: the .NET/C# API, recording/replay cmdlets, Pester integration, and real system integration (services, event logs).

## 3. Steps

1. [x] Research the real API: official site, PowerShell Gallery listing, and the module's own `Get-Help` output after installing v2.3.0.
2. [x] Commit this plan.
3. [x] `scripts/setup.ps1` — one-command module install.
4. [x] `scripts/01-table.ps1` — one-line table from real `Get-Process` output, then a sample dataset with presenters, grouping and totals.
5. [x] `scripts/02-live-dashboard.ps1` — `Invoke-ConsoleDashboard` with progress, sparkline, status strip, live table and log region updated from a worker script.
6. [x] `scripts/03-menu-and-form.ps1` — `Show-ConsoleMenu` shell with a page, an action and a `New-ConsoleForm` form item (`-FormOnly` runs the standalone `Read-ConsoleForm`); recordings drive it with real keystrokes via tmux.
7. [x] `scripts/04-jde-health.ps1` — mock JDE EnterpriseOne health dashboard (enterprise/HTML/AIS server status, job queue counts, UBE runs) replayed from `data/jde-health.json`.
8. [x] Run everything under `pwsh` 7 in a real TTY (tmux); fix issues.
9. [x] Record asciinema casts of each script, convert to GIF/MP4 with agg + ffmpeg, extract PNG screenshots; attach to the PR.
10. [x] README with setup, per-script explanations and the 5.1-vs-7 compatibility note; add the pick to `tracking/seen-bookmarks.json`; open the PR.

## 4. Success criteria

- `pwsh -File scripts/setup.ps1` installs the module from PSGallery.
- `pwsh -File scripts/01-table.ps1` prints bordered, fitted tables from `Get-Process` and the sample dataset — no errors.
- `pwsh -File scripts/02-live-dashboard.ps1` shows a live dashboard that finishes on its own (~20 s) and leaves its final state in the scrollback.
- `pwsh -File scripts/03-menu-and-form.ps1` opens an interactive menu; `-Demo` runs the same menu+form hands-free. 
- `pwsh -File scripts/04-jde-health.ps1` replays the mock JDE health feed and ends with a summary table.
- Artifacts: at least one PNG screenshot and one GIF/MP4 recording of the demos running, attached to the PR.
