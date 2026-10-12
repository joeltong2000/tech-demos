# Plan: C# Dev Kit 11.0 pre-release demo

## 1. Goal

Demonstrate the C# Dev Kit **11.0 pre-release** for VS Code — the extension rebuilt as a single
Native AOT `CSDevKit` process with on-disk project caches ([announcement](https://devblogs.microsoft.com/dotnet/faster-lighter-csharp-dev-kit/)) —
by opening a realistic multi-project .NET solution in VS Code and comparing solution load time,
process count, and memory against the current stable release (3.3). The happy path a reviewer runs:
`dotnet build && dotnet test` on the included `ParcelTrack` solution, then open the folder in
VS Code with the pre-release extension and watch the Solution Explorer populate.

## 2. Constraints

- **Runtime/tooling**: .NET 10 SDK (this is a .NET demo, so `dotnet` CLI instead of Bun — allowed
  by AGENTS.md rule 4 for non-JS subjects; noted in README). No JS/TS code in this app.
- **External services**: none. No credentials, no `.env`, everything offline and free.
  VS Code and both C# Dev Kit channels are free to install (Dev Kit's license permits free use
  for individuals/OSS, same terms as Visual Studio Community).
- **Out of scope**: reproducing the blog's 155–407 project benchmarks (too large for a tight
  demo), C# Dev Kit feature tour beyond load/memory (MSBuild editing, C# Doctor get a README
  mention only), any paid tooling.

## 3. Steps

1. [x] Commit this plan.
2. [ ] Install .NET 10 SDK on the VM.
3. [ ] Scaffold the `ParcelTrack` solution: 3 class libraries (`Domain`, `Application`,
   `Infrastructure`), 1 ASP.NET Core minimal web API (`Api`), 2 xUnit test projects
   (`Domain.Tests`, `Api.Tests`) — 6 projects wired with project references.
4. [ ] Verify `dotnet build` succeeds and `dotnet test` is green.
5. [ ] Write `README.md`: what 11.0 changes, how to install the pre-release, how to open the
   solution, what to look for.
6. [ ] Install VS Code on the VM; install C# Dev Kit **release** and **pre-release** into two
   isolated profiles (separate `--user-data-dir`/`--extensions-dir`) for a fair comparison.
7. [ ] Measure on this solution with each profile: time until Solution Explorer/language
   services are ready, extension process count (`ServiceHub`/`Microsoft.VisualStudio.Code.*`
   vs single `CSDevKit`), resident memory of those processes. Record results in
   `MEASUREMENTS.md`. If marketplace/licensing/sign-in blocks a fair side-by-side, document
   exactly what worked and what did not — no fabricated numbers.
8. [ ] Capture validation artifacts: screenshot of the solution open in VS Code with the
   pre-release extension, and a short video of the happy path (build + test + solution load).
9. [ ] Add the bookmark entry to `tracking/seen-bookmarks.json`.
10. [ ] Open one PR into `main` with artifacts linked.

## 4. Success criteria

- `cd apps/csharp-dev-kit-11/ParcelTrack && dotnet build` succeeds; `dotnet test` passes.
- Reviewer opening `ParcelTrack/` in VS Code with C# Dev Kit pre-release sees the Solution
  Explorer list all 6 projects and gets IntelliSense in `Program.cs`.
- PR contains a screenshot and a short video proving the above, plus `MEASUREMENTS.md`
  honestly reporting what was and wasn't measurable on the VM.
