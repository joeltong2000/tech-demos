# ConsoleMonster demo

[ConsoleMonster](https://consolemonster.dev) is an MIT-licensed console rendering engine for PowerShell and .NET by Przemysław Kłys (Evotec). One module ([`ConsoleMonster` on PowerShell Gallery](https://www.powershellgallery.com/packages/ConsoleMonster), v2.3.0, no dependencies) gives you:

- **Everyday output** — `Enable-ConsoleFormatting` restyles the output of the commands you already run at the prompt.
- **One-line tables** — `Show-ConsoleTable` turns any pipeline into a fitted, bordered table with presenters (status marks, units, warn thresholds), grouping and totals.
- **Live dashboards** — `New-ConsoleDashboard` + `Invoke-ConsoleDashboard` redraw panels, charts, live tables and a log region ~15×/second while your script works; `Update-Console` is the whole update API.
- **Menus and forms** — `Show-ConsoleMenu` runs a small console app (sidebar, pages, forms, command palette); `Read-ConsoleForm` asks a validated form and returns the answers.

Everything degrades by capability tier: 24-bit → 256 → 16 colours → `NO_COLOR` ASCII, and in redirected/CI output dashboards become append-only lines and menus print once — so the same scripts work in a pipeline.

## Setup

```powershell
pwsh -File scripts/setup.ps1     # or just: Install-Module ConsoleMonster -Scope CurrentUser
```

Free and open: MIT licence, no license key, no account, no telemetry prompts. Nothing in this demo needs credentials or a network connection after the module is installed.

## The scripts

Run each from this folder with `pwsh -File <script>`:

| Script | What it shows |
| --- | --- |
| `scripts/01-table.ps1` | One-line tables from ordinary command output: real `Get-Process` piped straight into `Show-ConsoleTable`, then a sample service inventory with the `Status` presenter, `-GroupBy`, `-ShowTotals` and a `WarnAbove` threshold. |
| `scripts/02-live-dashboard.ps1` | A live dashboard for a simulated nightly file import: phase strip, progress bar, rows-per-second sparkline, a live table keyed by file, and a log region fed by `Write-ConsoleLogEntry`. Finishes on its own (~15 s; `-StepSeconds 0.1` to speed it up) and leaves its final state in the scrollback. |
| `scripts/03-menu-and-form.ps1` | An interactive menu app (`Show-ConsoleMenu -Layout Shell`): a read-only page, an action with a toast, and a form (`New-ConsoleForm`/`New-ConsoleField`) with selects, a toggle, validation and a review page that shows the equivalent command before submit. `-FormOnly` runs the standalone `Read-ConsoleForm` variant. Nothing really restarts. |
| `scripts/04-jde-health.ps1` | The themed example for a JD Edwards EnterpriseOne admin: a mock **JDE server health** dashboard — enterprise/HTML/AIS/database server status, `QBATCH`/`QPRINT` job queue active/waiting counts, and UBE runs (`R09801`, `R31410`, `R3483`…) moving through waiting → processing → done, like Work with Submitted Jobs. Every number is replayed from `data/jde-health.json`; **no real JDE connection or credentials are used or needed**. Ends with a scrollback summary table (~14 s; `-TickSeconds 0.2` to speed it up). |

And for the everyday mode, start an interactive session and type:

```powershell
Import-Module ConsoleMonster
Enable-ConsoleFormatting
Get-Process | Select-Object -First 5   # same commands, nicer output
[version] '2.3.0'                      # record view instead of a bare line
```

## PowerShell 5.1 vs 7

- The module ships both `Desktop` and `Core` editions (minimum PowerShell 5.1, `net472` + `net8.0` assemblies), so the same scripts run on **Windows PowerShell 5.1** and **PowerShell 7** on Windows. The site renders its examples on both and compares every cell.
- This demo was built and verified on **PowerShell 7.5 on Linux** (what the CI/VM runs); `pwsh -File scripts/…` is the supported entry point here.
- 5.1 caveats: it's Windows-only, and on classic `conhost` the console font decides which glyph tier you get (ConsoleMonster falls back from Full → Basic → ASCII automatically). The scripts avoid 7-only language features so they should run on 5.1 unchanged, but 5.1 was not exercised in this environment (no Windows available).

## Notes and limitations found while building

- `Enable-ConsoleFormatting` restyles output at an **interactive prompt**; inside a `pwsh -File` script run it does not take over the script's own output. That matches the library's guidance: in scripts use the explicit `Show-Console*` commands (which is what these demos do).
- Sparkline charts (`New-ConsoleChart -Type Sparkline`) don't accept `-Warning`/`-Critical` thresholds (bar/histogram options) — the error message helpfully lists what each widget supports.
- Live `New-ConsoleKeyValue` widgets update per key (`Update-Console facts -Key … -Value …`), not by replacing content.
- Interactive menus/forms need a real TTY; in redirected/CI output they print once and exit, by design. The recordings here were made in a 110×32 terminal via asciinema.
- No feature required a paid service or key; nothing was skipped for licensing reasons.
