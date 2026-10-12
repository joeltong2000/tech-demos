# C# Dev Kit 11.0 pre-release demo

A small-but-real multi-project .NET solution (**ParcelTrack**) for exercising the
[C# Dev Kit 11.0 pre-release](https://devblogs.microsoft.com/dotnet/faster-lighter-csharp-dev-kit/)
in VS Code, plus honest on-VM measurements comparing it to the stable release in
[`MEASUREMENTS.md`](./MEASUREMENTS.md).

> This is a .NET demo, so it uses the `dotnet` CLI and .NET SDK instead of Bun
> (per the monorepo rule allowing the subject's native tooling).

## What C# Dev Kit 11.0 changes

C# Dev Kit is Microsoft's VS Code extension for solution-level C# development
(Solution Explorer, test discovery, project system). Version 11.0 (previous version: 3.3)
is a ground-up rearchitecture:

- **One native process instead of six.** The six managed ServiceHub-style processes are
  consolidated into a single `CSDevKit` server compiled with **.NET Native AOT** — no runtime
  load or JIT on the startup path.
- **Project caches.** Each project's build/design-time data is cached on disk on first load;
  later opens are served from the cache. Microsoft measured whole-solution load dropping
  from 50.3 s to 2.3 s on Orleans (155 projects) and 84.1 s to 3.0 s on Aspire (407 projects),
  with the *active file* ready in ~0.5 s.
- **Active-file-first loading.** Language support in the file you're editing arrives before
  the rest of the solution finishes loading.
- **Faster incremental builds** via fast up-to-date checks and Build Acceleration
  (39× faster no-op builds on Aspire in Microsoft's measurements).
- **~80–85% less memory** for the extension's server process(es).
- **New features:** full language support (completions, diagnostics, go-to-definition) in
  `.csproj`/`.props`/`.targets` files, and the **C# Doctor** for diagnosing environment issues.

## Prerequisites

- [.NET SDK](https://dotnet.microsoft.com/download) 10.0+ (`dotnet --version`)
- [VS Code](https://code.visualstudio.com/) (the real one — C# Dev Kit is not on Open VSX,
  so it is not available in code-server/VSCodium)

## Run the happy path

```bash
cd apps/csharp-dev-kit-11/ParcelTrack
dotnet build        # 6 projects build
dotnet test         # 16 tests pass (11 domain unit + 5 API integration)
dotnet run --project src/ParcelTrack.Api   # then: curl localhost:5000/parcels
```

The solution is deliberately multi-project so the extension has real work to do:

```
ParcelTrack.sln
├── src/ParcelTrack.Domain           parcel aggregate + status state machine
├── src/ParcelTrack.Application      ParcelService + repository interface
├── src/ParcelTrack.Infrastructure   in-memory repository + seed data
├── src/ParcelTrack.Api              ASP.NET Core minimal API
├── tests/ParcelTrack.Domain.Tests   xUnit unit tests
└── tests/ParcelTrack.Api.Tests      xUnit + WebApplicationFactory integration tests
```

## Install the 11.0 pre-release in VS Code

1. Install the **C# Dev Kit** extension (`ms-dotnettools.csdevkit`) from the Marketplace.
2. On the extension's page in the Extensions view, click **Switch to Pre-Release Version**.
   You should see version **11.0.x** after reload. (CLI equivalent:
   `code --install-extension ms-dotnettools.csdevkit --pre-release`.)
3. The companion **C#** extension (`ms-dotnettools.csharp`) is installed automatically;
   the 11.x Dev Kit pairs with the pre-release C# extension.

## Open the solution and what to look for

1. `code apps/csharp-dev-kit-11/ParcelTrack` (open the folder containing `ParcelTrack.sln`).
2. Watch the **Solution Explorer** view populate with all 6 projects — with 11.0 this is
   near-instant on second open thanks to the project cache.
3. Open `src/ParcelTrack.Api/Program.cs` and hover/F12 on `ParcelService` — note how quickly
   language support is live in the active file.
4. Check your process list: with 11.0 there is a single native `CSDevKit` process next to
   Roslyn (`Microsoft.CodeAnalysis.LanguageServer`), instead of ~six
   `Microsoft.VisualStudio.Code.ServiceController` / ServiceHub processes with 3.3.
5. The **Testing** view discovers all 16 xUnit tests; run them from the beaker icon.
6. Build twice from the terminal or via **.NET: Build** — the second (no-op) build is much
   faster in 11.0 thanks to fast up-to-date checks.

## What was measured on this VM

See [`MEASUREMENTS.md`](./MEASUREMENTS.md) for the release-vs-pre-release comparison run on
this repo's VM (solution load, process count, memory), including exactly what could and
could not be measured fairly.
