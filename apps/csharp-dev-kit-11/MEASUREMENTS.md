# C# Dev Kit: stable 3.40 vs pre-release 11.x, measured on this VM

Honest comparison of the two Marketplace channels of C# Dev Kit opening this repo's
6-project `ParcelTrack` solution. Everything below was actually measured; the last section
lists what was **not** measured and why.

## Setup

- VM: Linux x64, 4 vCPU, 15 GB RAM, X display at 1920×1200 (no GPU).
- VS Code 1.141.0 (real Microsoft build — required, since C# Dev Kit is not on Open VSX).
- .NET SDK 10.0.401.
- Two fully isolated VS Code profiles (separate `--user-data-dir` + `--extensions-dir`,
  identical `settings.json`), one per channel:
  - **Stable**: `ms-dotnettools.csdevkit` **3.40.210** + `ms-dotnettools.csharp` 2.160.4
  - **Pre-release**: `ms-dotnettools.csdevkit` **11.3.30** + `ms-dotnettools.csharp` 11.2.14
- Each profile opened the `ParcelTrack` folder twice, sequentially (never both at once):
  run 1 = first-ever open (cold), run 2 = reopen (warm). Timings come from the extension's
  own "C# Dev Kit" output log timestamps; memory/process data from `ps -eo pid,rss,args`
  after letting the window settle ≥20 s.
- No sign-in, no license purchase, no paid anything was required for either channel.

## Results

### Solution load time (from log marker "Starting: Opening a solution" to all 6 projects ready)

| Run | Stable 3.40 | Pre-release 11.x |
| --- | --- | --- |
| Spawn .NET server | 1,331 / 1,403 ms (cold/warm) | 142 / 102 ms |
| "Completed: Opening a solution" | 1,579 / 1,922 ms | 160 / 242 ms |
| All 6 projects ready — cold | **5.7 s** | **2.5 s** (0 caches found; design-time build 1.9 s) |
| All 6 projects ready — warm | **6.9 s** | **0.52 s** (all 6 served from cache in 257 ms) |

Warm open is ~**13× faster** — and visibly so: stable rebuilds its project model every open
(its warm run was no faster than cold), while 11.x logs
`Load 6 project caches (257ms) - 6 loaded, 0 skipped by marker, 0 missing cache`.
The caches live in `obj/.csdevkit/` and per-project `obj/**/*.lscache*` files.

"All projects ready" markers are the closest equivalents each version logs:
`Project system initialization finished. 6 project(s) are loaded` (3.40) vs
`[WorkspaceLoader] Completed: Load N project caches` / design-time build completion (11.x).

### Extension server processes and memory (settled, Roslyn excluded as in Microsoft's methodology)

| | Stable 3.40 | Pre-release 11.x |
| --- | --- | --- |
| Dev Kit server processes | **5** | **1** (native `CSDevKit`, no `dotnet` host) |
| Combined RSS | **841–943 MB** | **172–188 MB** |
| Reduction | — | **~78–82%** |

Stable's five processes: `Microsoft.VisualStudio.Code.ServiceHost` ×2 (411 + 137 MB),
`Code.Server` (172 MB), `Code.ServiceController` (122 MB), and a `dotnet`-hosted
`ProjectSystem.Server.BuildHost` (102 MB). Pre-release runs a single Native AOT `CSDevKit`
executable. The Roslyn language server (`Microsoft.CodeAnalysis.LanguageServer`) is separate
and nearly identical in both: 305 MB vs 311 MB.

## What could NOT be measured (and why)

- **Blog-scale load times.** Microsoft's headline numbers (50–84 s → 2–3 s) come from
  155–407-project solutions. `ParcelTrack` has 6 projects, so absolute times here are small;
  the relative gap (13× warm) is the meaningful signal.
- **Time to first IntelliSense / semantic tokens in the active file.** Both channels use a
  near-identical Roslyn server, and I had no keystroke-level instrumentation that would
  separate it fairly from editor noise on a software-rendered VM. Not measured.
- **Faster incremental builds (fast up-to-date checks / Build Acceleration).** These apply
  to the extension's build path, not `dotnet build` in a terminal. The Dev Kit log does not
  emit comparable per-build timing markers in 3.40, so no fair number is reported.
- **Statistical rigor.** One cold + one warm run per channel on a shared 4-vCPU VM.
  Treat the numbers as indicative, not a benchmark suite.

No licensing, sign-in, or marketplace blockers were hit: both channels installed via
`code --install-extension` and activated without accounts, so a genuine side-by-side was
possible. Raw `ps` snapshots and log excerpts were captured during the run; the key log
lines are reproduced above verbatim.
