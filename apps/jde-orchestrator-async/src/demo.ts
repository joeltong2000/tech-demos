/**
 * Demo: call the SAME orchestration twice against an AIS server —
 *   1. synchronously (default queue): blocks until done, HTTP 200 + output
 *   2. fire-and-forget ("jde__jobQueue": "JDE__ASYNCH"): HTTP 202 immediately
 * — then show the timings side by side and check on the async run afterwards.
 *
 * Default is mock mode (local mock AIS server, no config needed).
 * Set MOCK=false plus AIS_* env vars (see .env.example) for a real AIS server.
 */
import { invokeOrchestration, type OrchestratorCallResult } from "./client.ts";
import { startMockAis } from "./mock-ais.ts";
import { JOB_QUEUE_PARAM, type MonitorRun } from "./types.ts";

const bold = (s: string) => `\x1b[1m${s}\x1b[0m`;
const green = (s: string) => `\x1b[32m${s}\x1b[0m`;
const cyan = (s: string) => `\x1b[36m${s}\x1b[0m`;
const yellow = (s: string) => `\x1b[33m${s}\x1b[0m`;
const dim = (s: string) => `\x1b[2m${s}\x1b[0m`;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const fmtMs = (ms: number) => {
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)} s`;
  return ms < 10 ? `${ms.toFixed(1)} ms` : `${ms.toFixed(0)} ms`;
};

const mockMode = (process.env.MOCK ?? "true").toLowerCase() !== "false";
const orchestrationName = process.env.ORCHESTRATION_NAME ?? "ORCH_DemoSlowLookup";
const orchestrationInput = JSON.parse(
  process.env.ORCHESTRATION_INPUT_JSON ?? '{"orderNumber":"12345"}',
) as Record<string, unknown>;
const mockDurationMs = Number(process.env.MOCK_ORCH_DURATION_MS ?? 4000);

console.log(bold("\n=== JDE Orchestrator: synchronous vs fire-and-forget (JDE__ASYNCH) ===\n"));

const mock = mockMode
  ? startMockAis({ port: 0, orchestrationDurationMs: mockDurationMs })
  : null;

const client = mock
  ? { baseUrl: mock.url, username: "DEMO", password: "demo-only" }
  : {
      baseUrl: process.env.AIS_BASE_URL ?? "",
      username: process.env.AIS_USERNAME ?? "",
      password: process.env.AIS_PASSWORD ?? "",
    };

if (!client.baseUrl) {
  console.error("MOCK=false but AIS_BASE_URL is not set. See .env.example.");
  process.exit(1);
}

console.log(`  Mode:           ${mockMode ? "mock (local simulated AIS server)" : "real AIS server"}`);
console.log(`  AIS server:     ${client.baseUrl}`);
console.log(`  Orchestration:  ${orchestrationName}`);
console.log(`  Input:          ${JSON.stringify(orchestrationInput)}\n`);

// ---- Call 1: synchronous (no queue override -> design-time default) --------
console.log(bold("[1/2] Synchronous call") + dim(" — no override; waits for the result"));
console.log(dim(`      POST /jderest/v3/orchestrator/${orchestrationName}`));
console.log(dim(`      body: ${JSON.stringify(orchestrationInput)}`));
const syncResult = await invokeOrchestration(client, orchestrationName, orchestrationInput);
console.log(
  `      -> HTTP ${green(String(syncResult.httpStatus))} after ${yellow(fmtMs(syncResult.elapsedMs))}`,
);
console.log(`      output: ${JSON.stringify(syncResult.body)}\n`);

// ---- Call 2: fire and forget via the documented jde__jobQueue override -----
const asyncBody = { ...orchestrationInput, [JOB_QUEUE_PARAM]: "JDE__ASYNCH" };
console.log(bold("[2/2] Fire-and-forget call") + dim(' — "jde__jobQueue": "JDE__ASYNCH"'));
console.log(dim(`      POST /jderest/v3/orchestrator/${orchestrationName}`));
console.log(dim(`      body: ${JSON.stringify(asyncBody)}`));
const asyncStarted = Date.now();
const asyncResult = await invokeOrchestration(client, orchestrationName, asyncBody);
console.log(
  `      -> HTTP ${green(String(asyncResult.httpStatus))} after ${yellow(fmtMs(asyncResult.elapsedMs))}` +
    dim("  (job keeps running on the AIS server)"),
);
console.log(`      output: ${JSON.stringify(asyncResult.body)} ${dim("<- no response body: you traded it for the instant 202")}\n`);

// ---- Side-by-side timings ---------------------------------------------------
const row = (label: string, r: OrchestratorCallResult, note: string) =>
  `  ${label.padEnd(39)}  ${String(r.httpStatus).padEnd(6)} ${fmtMs(r.elapsedMs).padStart(9)}   ${note}`;
console.log(bold("Timings, same orchestration:"));
console.log(dim(`  ${"call".padEnd(39)}  status   latency   response body`));
console.log(row("synchronous (default queue)", syncResult, "full orchestration output"));
console.log(row('async ("jde__jobQueue": "JDE__ASYNCH")', asyncResult, "empty — fire and forget"));
console.log(
  `\n  ${cyan(`The async caller was unblocked after ${fmtMs(asyncResult.elapsedMs)}; the same work took ${fmtMs(syncResult.elapsedMs)} synchronously.`)}\n`,
);

// ---- Checking on the async job afterwards ----------------------------------
console.log(bold("Checking on the fire-and-forget run:"));
if (mock) {
  console.log(
    dim(
      "  (Oracle docs expose run status via the Orchestrator Monitor UI, P980060X, when\n" +
        "  monitoring is enabled — e.g. via the jde-AIS-MonitorRequest header this demo sends.\n" +
        "  There is no documented REST endpoint to poll an async orchestration's result, so\n" +
        "  this mock mimics the Monitor's Run Details via GET /mock/monitor/runs.)",
    ),
  );
  let lastStatus = "";
  for (;;) {
    const response = await fetch(`${mock.url}/mock/monitor/runs`);
    const { runs } = (await response.json()) as { runs: MonitorRun[] };
    const run = runs.find((r) => r.queue === "JDE__ASYNCH");
    if (!run) break;
    if (run.status !== lastStatus) {
      lastStatus = run.status;
      const elapsed = fmtMs(Date.now() - asyncStarted);
      console.log(`  t+${elapsed.padStart(7)}  run ${run.runId.slice(0, 8)}  status: ${bold(run.status)}`);
    }
    if (run.status === "Successful" || run.status === "Failed") {
      console.log(`  recorded output: ${JSON.stringify(run.output)}`);
      break;
    }
    await sleep(250);
  }
} else {
  console.log(
    "  Against a real AIS server, open Orchestrator Monitor (P980060X) to see the run's\n" +
      "  status and recorded input/output (monitoring was requested via the\n" +
      "  jde-AIS-MonitorRequest header). If the orchestration launches a UBE report,\n" +
      "  poll POST /jderest/v2/report/status with the job number instead.",
  );
}

console.log(green(bold("\nDone.")));
mock?.stop();
