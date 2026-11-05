# JDE Orchestrator: fire-and-forget calls with `JDE__ASYNCH`

A small runnable demo of JD Edwards EnterpriseOne Orchestrator's **per-call job
queue override**. It calls the *same* orchestration twice against an AIS server:

1. **Synchronously** (no override): the call blocks until the orchestration
   finishes and returns **HTTP 200** with the full output (~4 s here).
2. **Fire and forget**: the body includes `"jde__jobQueue": "JDE__ASYNCH"`, so
   the AIS server answers **HTTP 202 Accepted immediately** (milliseconds) and
   keeps running the job server-side.

It then prints the timings side by side and shows the async run progressing
`Queued → Running → Successful` in a mock Orchestrator Monitor.

## What `JDE__ASYNCH` is

An orchestration's job queue and scope are normally fixed at design time in
Orchestrator Studio. Per Oracle's
[Overriding the AIS Job Queue and Scope for Individual Orchestrator Calls](https://docs.oracle.com/en/applications/jd-edwards/cross-product/9.2/eotos/overriding-the-ais-job-queue-and-scope-for-individual-orchestrator-calls.html),
an **individual call** can override them by passing the reserved `jde__jobQueue`
parameter in the JSON body. The five valid values (note the **double underscore**
after `JDE`):

| Override value | Behavior |
| --- | --- |
| `JDE__DEFAULT` | Default queue; synchronous, caller waits for the response |
| `JDE__SINGLE` | Single-threaded FIFO system queue; synchronous |
| `JDE__USER_SINGLE` | Single-threaded FIFO queue per user; synchronous |
| `JDE__ASYNCH` | **Fire and forget** (system scope): immediate 202-Accepted, job continues on the server |
| `JDE__USER_ASYNCH` | Fire and forget, per-user queue |

**Use it when** the caller doesn't need the orchestration's output and shouldn't
wait for it — e.g. kicking off long-running integrations, batch-style updates,
or webhook handlers that must respond fast.

**Don't use it when** you need the result: with a 202 **you lose the response
body entirely** (no outputs, and no inline error — a failing orchestration still
got its 202). You also lose ordering guarantees versus the `*_SINGLE` queues,
and async jobs still count against the AIS server's `MaxConcurrentJobs` limit.

## Run it

```bash
cd apps/jde-orchestrator-async
bun install && bun run demo
```

No configuration needed: by default the demo starts a **local mock AIS server**
in-process (slow 4 s orchestration, honors the `jde__jobQueue` override) and
runs both calls against it.

### Mock vs real mode

Copy `.env.example` to `.env` to change settings. Set `MOCK=false` plus
`AIS_BASE_URL`, `AIS_USERNAME`, `AIS_PASSWORD`, `ORCHESTRATION_NAME`, and
`ORCHESTRATION_INPUT_JSON` to point the same demo at a real AIS server using
basic auth (`POST {AIS_BASE_URL}/jderest/v3/orchestrator/{name}`). No secrets
are committed; the mock accepts any non-empty basic-auth credentials.

### Checking on the async job afterwards

The docs do **not** define a REST endpoint for polling an async orchestration's
result. What they do describe:

- The **Orchestrator Monitor** application (P980060X) shows run details (status
  Queued/Running/Successful/Failed, duration, input/output) when monitoring is
  enabled — at design time or per call via the `jde-AIS-MonitorRequest` header
  (this demo sends `monitorRequestIO`).
- If the orchestration launches a **UBE report**, you can poll
  `POST /jderest/v2/report/status` with the job number.

Since the real Monitor is a web UI, the mock exposes a stand-in endpoint,
`GET /mock/monitor/runs` (clearly labeled mock-only), which the demo polls to
show the async run completing.

### Optional PowerShell client

With the mock running in one terminal (`bun run mock`), the same two calls in
PowerShell:

```powershell
pwsh scripts/demo.ps1                      # mock on localhost:9208
pwsh scripts/demo.ps1 -BaseUrl https://real-ais:7078 -Username JDE -Password ...
```

Tested with PowerShell 7.4.6 on Linux (installed from the free tarball). If you
don't have pwsh, the Bun demo covers everything; the script is a bonus.

## Sample output

```text
=== JDE Orchestrator: synchronous vs fire-and-forget (JDE__ASYNCH) ===

  [mock-ais] mock AIS server listening on http://localhost:42615
  Mode:           mock (local simulated AIS server)
  Orchestration:  ORCH_DemoSlowLookup

[1/2] Synchronous call — no override; waits for the result
      -> HTTP 200 after 4.00 s
      output: {"ServiceRequest1":{"orderNumber":"12345","orderStatus":"540 - Shipped",...}}

[2/2] Fire-and-forget call — "jde__jobQueue": "JDE__ASYNCH"
      -> HTTP 202 after 0.4 ms  (job keeps running on the AIS server)
      output: null <- no response body: you traded it for the instant 202

Timings, same orchestration:
  call                                     status   latency   response body
  synchronous (default queue)              200       4.00 s   full orchestration output
  async ("jde__jobQueue": "JDE__ASYNCH")   202       0.4 ms   empty — fire and forget

Checking on the fire-and-forget run:
  t+   4 ms  run 9d9f13e4  status: Running
  t+ 4.02 s  run 9d9f13e4  status: Successful
  recorded output: {"ServiceRequest1":{...},"jde__status":"SUCCESS",...}
```

## Assumptions and deviations from the docs

- The task brief said `jdejobQueue` / `JDEASYNCH`; the Oracle doc actually
  spells them `jde__jobQueue` and `JDE__ASYNCH` (double underscores), and the
  doc explicitly calls out the double underscore. This demo follows the doc.
- The docs specify the 202-Accepted status for fire-and-forget calls but not a
  202 response body, so the mock returns an **empty body**.
- The mock's orchestration output shape (`ServiceRequest1` + `jde__*` fields)
  is a plausible v3-style response, invented for the demo; real output depends
  on the orchestration's design.
- `GET /mock/monitor/runs` is **not** a real AIS endpoint — it's a mock-only
  stand-in for the Orchestrator Monitor UI, as explained above.
- The mock accepts any basic-auth credentials and doesn't implement tokens,
  environments, or the full error model.

## Files

| Path | Purpose |
| --- | --- |
| `src/demo.ts` | The demo: both calls, timing table, async status check |
| `src/mock-ais.ts` | Mock AIS server (`bun run mock` to run standalone) |
| `src/client.ts` | Minimal orchestrator REST client (basic auth) |
| `src/types.ts` | The five documented queue overrides + monitor types |
| `scripts/demo.ps1` | Optional PowerShell client (same two calls) |
