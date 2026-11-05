/**
 * Mock JD Edwards AIS / Orchestrator server.
 *
 * Implements just enough of the AIS REST surface for this demo:
 *
 *   POST /jderest/v3/orchestrator/{orchestration}
 *     - Requires a Basic Authorization header (any non-empty credentials pass;
 *       a real AIS server would validate them against EnterpriseOne).
 *     - Simulates a slow orchestration (MOCK_ORCH_DURATION_MS, default 4000 ms).
 *     - Honors the documented "jde__jobQueue" body parameter: JDE__ASYNCH and
 *       JDE__USER_ASYNCH return 202 Accepted immediately while the job keeps
 *       running; the other values (and no override) block and return 200 with
 *       the orchestration output.
 *
 *   GET /mock/monitor/runs
 *     - MOCK-ONLY convenience. The real product surfaces run status in the
 *       Orchestrator Monitor application (P980060X), a web UI, not a public
 *       REST endpoint. This endpoint mimics the Run Details data so the demo
 *       can show the async job progressing Queued -> Running -> Successful.
 */
import { randomUUID } from "node:crypto";

import {
  isFireAndForget,
  isJobQueueOverride,
  JOB_QUEUE_OVERRIDES,
  JOB_QUEUE_PARAM,
  type JobQueueOverride,
  type MonitorRun,
} from "./types.ts";

const ORCH_PATH_PREFIX = "/jderest/v3/orchestrator/";

export interface MockAisOptions {
  port: number;
  orchestrationDurationMs: number;
  quiet?: boolean;
}

export interface MockAisServer {
  url: string;
  stop: () => void;
}

export function startMockAis(options: MockAisOptions): MockAisServer {
  const { port, orchestrationDurationMs, quiet = false } = options;
  const runs: MonitorRun[] = [];
  const log = (message: string) => {
    if (!quiet) console.log(`  [mock-ais] ${message}`);
  };

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  /** The pretend orchestration: a slow lookup that echoes its input. */
  async function runOrchestration(
    name: string,
    input: Record<string, unknown>,
    run: MonitorRun,
  ): Promise<Record<string, unknown>> {
    run.status = "Running";
    const started = Date.now();
    await sleep(orchestrationDurationMs);
    const output = {
      ServiceRequest1: {
        orderNumber: input["orderNumber"] ?? "unknown",
        orderStatus: "540 - Shipped",
        shipTo: "Capital Distributors",
        extendedPrice: 1234.56,
      },
      jde__status: "SUCCESS",
      jde__startTimestamp: new Date(started).toISOString(),
      jde__endTimestamp: new Date().toISOString(),
      jde__serverExecutionSeconds: (Date.now() - started) / 1000,
    };
    run.status = "Successful";
    run.durationMs = Date.now() - started;
    run.output = output;
    log(`orchestration '${name}' finished after ${run.durationMs} ms (queue ${run.queue})`);
    return output;
  }

  const server = Bun.serve({
    port,
    idleTimeout: 60,
    async fetch(request) {
      const url = new URL(request.url);

      if (request.method === "GET" && url.pathname === "/mock/monitor/runs") {
        return Response.json({ mockOnly: true, runs });
      }

      if (request.method === "POST" && url.pathname.startsWith(ORCH_PATH_PREFIX)) {
        const auth = request.headers.get("authorization") ?? "";
        if (!auth.startsWith("Basic ") || auth.length <= "Basic ".length) {
          return Response.json(
            { message: "Authorization Failure", status: "ERROR" },
            { status: 403 },
          );
        }
        if (!(request.headers.get("content-type") ?? "").includes("application/json")) {
          return Response.json(
            { message: "Invalid Content-Type Header - Must use application/json", status: "ERROR" },
            { status: 415 },
          );
        }

        const orchestrationName = decodeURIComponent(
          url.pathname.slice(ORCH_PATH_PREFIX.length),
        );
        let body: Record<string, unknown>;
        try {
          body = (await request.json()) as Record<string, unknown>;
        } catch {
          return Response.json(
            { message: "Bad Request - Invalid JSON Input", status: "ERROR" },
            { status: 400 },
          );
        }

        let queue: JobQueueOverride = "JDE__DEFAULT";
        if (JOB_QUEUE_PARAM in body) {
          const requested = body[JOB_QUEUE_PARAM];
          if (!isJobQueueOverride(requested)) {
            return Response.json(
              {
                message: `Invalid ${JOB_QUEUE_PARAM} value. Valid overrides: ${JOB_QUEUE_OVERRIDES.join(", ")}`,
                status: "ERROR",
              },
              { status: 400 },
            );
          }
          queue = requested;
        }

        const { [JOB_QUEUE_PARAM]: _queueParam, ...input } = body;
        const run: MonitorRun = {
          runId: randomUUID(),
          name: orchestrationName,
          status: "Queued",
          queue,
          requestReceived: new Date().toISOString(),
          durationMs: null,
          input,
          output: null,
        };
        runs.push(run);
        log(`received '${orchestrationName}' on queue ${queue}`);

        if (isFireAndForget(queue)) {
          // Fire and forget: respond 202 now, keep processing in the background.
          void runOrchestration(orchestrationName, input, run).catch(() => {
            run.status = "Failed";
          });
          // The Oracle docs specify the 202-Accepted status but not a response
          // body for fire-and-forget calls, so the mock returns an empty body.
          return new Response(null, { status: 202 });
        }

        const output = await runOrchestration(orchestrationName, input, run);
        return Response.json(output, { status: 200 });
      }

      return Response.json({ message: "Not Found", status: "ERROR" }, { status: 404 });
    },
  });

  const serverUrl = `http://localhost:${server.port}`;
  log(`mock AIS server listening on ${serverUrl}`);
  return { url: serverUrl, stop: () => server.stop(true) };
}

if (import.meta.main) {
  startMockAis({
    port: Number(process.env.MOCK_PORT ?? 9208),
    orchestrationDurationMs: Number(process.env.MOCK_ORCH_DURATION_MS ?? 4000),
  });
  console.log("  [mock-ais] standalone mode; press Ctrl+C to stop.");
}
